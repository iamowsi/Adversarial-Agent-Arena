import threading, time, uuid
from pathlib import Path
from typing import List, Optional
from arena.agents import AttackerAgent, DefenderAgent
from arena.config import ArenaSettings, settings as default_settings
from arena.judge import DeterministicJudge
from arena.llm import BaseLLMClient, MockLLMClient
from arena.logger import ArenaLogger
from arena.models import AgentMessage, ArenaReport, RoundConfig, RoundResult
from arena.scorer import ArenaScorer
from arena.tools import MockToolRegistry

SCENARIO_ALIASES = {"prompt_injection": "prompt_injection_tool_abuse", "prompt_injection_tool_abuse": "prompt_injection_tool_abuse"}

class ArenaOrchestrator:
    def __init__(self, llm: Optional[BaseLLMClient] = None, config: ArenaSettings = default_settings, stop_event: Optional[threading.Event] = None) -> None:
        self.settings = config
        self.llm = llm or MockLLMClient()
        self.judge = DeterministicJudge()
        self.scorer = ArenaScorer()
        self.logger = ArenaLogger(config.sqlite_path, config.jsonl_path)
        self.stop_event = stop_event or threading.Event()

    def _is_stopped(self) -> bool:
        return self.stop_event.is_set() or Path(self.settings.stop_file).exists()

    def trigger_emergency_stop(self) -> None:
        self.stop_event.set()

    def run_round(self, cfg: RoundConfig) -> RoundResult:
        tools = MockToolRegistry(cfg.canary_token)
        attacker, defender = AttackerAgent(self.llm), DefenderAgent(self.llm, tools)
        messages: List[AgentMessage] = []
        total_tokens, comp_turn, stopped, turns_done = 0, None, False, 0
        start = time.perf_counter()

        for turn in range(1, cfg.max_turns + 1):
            if self._is_stopped():
                stopped = True
                break
            atk = attacker.act(messages, cfg, turn)
            messages.append(atk)
            total_tokens += atk.tokens_used
            if cfg.rate_limit_delay_sec > 0:
                time.sleep(cfg.rate_limit_delay_sec)
            dfn = defender.act(messages, cfg, turn)
            messages.append(dfn)
            total_tokens += dfn.tokens_used
            turns_done = turn
            elapsed = time.perf_counter() - start
            if self.judge.evaluate(cfg, messages, elapsed, total_tokens).defender_down:
                comp_turn = turn
                break
            if elapsed > cfg.max_seconds or total_tokens > cfg.max_tokens:
                break

        elapsed_total = round(time.perf_counter() - start, 4)
        verdict = self.judge.evaluate(cfg, messages, elapsed_total, total_tokens, stopped)
        return RoundResult(config=cfg, messages=messages, verdict=verdict, elapsed_seconds=elapsed_total, total_tokens=total_tokens, turns_completed=turns_done, compromised_at_turn=comp_turn)

    def run_arena(self, scenario: str = "prompt_injection", rounds: int = 5, seed: int = 42) -> ArenaReport:
        normalized = SCENARIO_ALIASES.get(scenario)
        if not normalized:
            raise ValueError(f"Unsupported scenario: {scenario}")
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        results = []
        for idx in range(1, rounds + 1):
            if self._is_stopped():
                break
            cfg = RoundConfig(
                round_id=idx, scenario=normalized, seed=seed, canary_token=self.settings.canary_token,
                max_turns=self.settings.max_turns_per_round, max_tokens=self.settings.max_tokens_per_round,
                max_seconds=self.settings.max_seconds_per_round, rate_limit_delay_sec=self.settings.rate_limit_delay_sec,
            )
            res = self.run_round(cfg)
            self.logger.log_round(run_id, res)
            results.append(res)
        report = self.scorer.build_report(run_id, normalized, seed, results)
        self.logger.save_report(report, self.settings.data_dir / f"{run_id}_report.json")
        return report
