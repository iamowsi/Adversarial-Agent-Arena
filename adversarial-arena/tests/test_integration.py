from pathlib import Path
from arena.config import ArenaSettings
from arena.llm import MockLLMClient
from arena.orchestrator import ArenaOrchestrator

def test_full_run_and_defense(tmp_path: Path):
    cfg = ArenaSettings(data_dir=tmp_path, rate_limit_delay_sec=0.0)
    report = ArenaOrchestrator(llm=MockLLMClient(defender_vuln_rate=0.0), config=cfg).run_arena("prompt_injection", rounds=5, seed=42)
    assert report.total_rounds == 5
    assert report.attack_success_rate == 0.0
    assert report.detection_rate > 0.0
    assert (tmp_path / "arena.db").exists()
