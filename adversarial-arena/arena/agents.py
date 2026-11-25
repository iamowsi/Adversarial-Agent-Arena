from typing import List
from arena.llm import BaseLLMClient
from arena.models import AgentMessage, Role, RoundConfig, ToolCall
from arena.tools import MockToolRegistry

class AttackerAgent:
    def __init__(self, llm: BaseLLMClient) -> None:
        self.llm = llm

    def act(self, history: List[AgentMessage], config: RoundConfig, turn: int) -> AgentMessage:
        last_def = next((m.content for m in reversed(history) if m.role == Role.DEFENDER), "")
        resp = self.llm.generate(Role.ATTACKER, last_def, turn, config.seed + config.round_id * 100)
        return AgentMessage(role=Role.ATTACKER, content=resp.content, turn=turn, tokens_used=resp.tokens_used)

class DefenderAgent:
    def __init__(self, llm: BaseLLMClient, tools: MockToolRegistry) -> None:
        self.llm = llm
        self.tools = tools

    def act(self, history: List[AgentMessage], config: RoundConfig, turn: int) -> AgentMessage:
        last_atk = next((m.content for m in reversed(history) if m.role == Role.ATTACKER), "")
        resp = self.llm.generate(Role.DEFENDER, last_atk, turn, config.seed + config.round_id * 100, config.canary_token)
        calls, results = [], []
        for rc in resp.tool_calls:
            call = ToolCall(tool_name=rc["tool_name"], arguments=rc.get("arguments", {}), caller=Role.DEFENDER, turn=turn)
            calls.append(call)
            results.append(self.tools.execute(call, allowed_tools=config.defender_allowed_tools))
        return AgentMessage(role=Role.DEFENDER, content=resp.content, turn=turn, tokens_used=resp.tokens_used, detected_attack=resp.detected_attack, tool_calls=calls, tool_results=results)
