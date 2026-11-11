"""Bounded, capability-aware agent runtime."""
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Tool:
    name: str
    capabilities: frozenset[str]
    invoke: Callable[[dict], dict]


@dataclass
class AgentContext:
    objective: str
    capabilities: frozenset[str]
    budget: int = 10
    state: dict = field(default_factory=dict)


class AgentRuntime:
    def __init__(self, tools: list[Tool] | None = None):
        self.tools = tools or []

    def find_tool(self, capabilities: frozenset[str]) -> Tool:
        for tool in self.tools:
            if capabilities.issubset(tool.capabilities):
                return tool
        raise LookupError(f"no tool satisfies: {', '.join(sorted(capabilities))}")

    def execute(self, context: AgentContext, tool: Tool, payload: dict) -> dict:
        if context.budget <= 0:
            raise RuntimeError("agent execution budget exhausted")
        if not context.capabilities.issubset(tool.capabilities):
            raise PermissionError("tool lacks required agent capabilities")
        context.budget -= 1
        result = tool.invoke(payload)
        context.state["last_tool"] = tool.name
        context.state["last_result"] = result
        return result
