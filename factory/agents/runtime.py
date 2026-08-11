"""Minimal provider-neutral execution contract for factory agents."""
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass(frozen=True)
class Tool:
    name: str
    capabilities: frozenset[str]
    handler: Callable[..., Any]


@dataclass
class AgentRuntime:
    agent_id: str
    tools: dict[str, Tool] = field(default_factory=dict)
    budget: int = 100

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def available_tools(self, required: frozenset[str]) -> list[Tool]:
        return [t for t in self.tools.values() if required.issubset(t.capabilities)]

    def call(self, tool_name: str, **kwargs: Any) -> Any:
        if self.budget <= 0:
            raise RuntimeError("agent execution budget exhausted")
        tool = self.tools.get(tool_name)
        if tool is None:
            raise KeyError(f"tool not registered: {tool_name}")
        self.budget -= 1
        return tool.handler(**kwargs)
