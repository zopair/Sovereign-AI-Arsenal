"""Capability-driven execution backend selection for the factory.

The broker intentionally does not depend on the word "runner". It selects an
execution backend from declared capabilities and health evidence, allowing
GitHub-hosted, self-hosted, container, or local execution to be interchangeable.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class BackendState(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass(frozen=True)
class ExecutionBackend:
    name: str
    capabilities: frozenset[str]
    state: BackendState = BackendState.READY
    priority: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionRequest:
    capabilities: frozenset[str]
    exclude: frozenset[str] = frozenset()


class RunnerBroker:
    """Choose the best available backend by capability, not by product name."""

    def __init__(self, backends: Iterable[ExecutionBackend] = ()) -> None:
        self.backends = list(backends)

    def select(self, request: ExecutionRequest) -> ExecutionBackend:
        candidates = [
            b for b in self.backends
            if b.name not in request.exclude
            and b.state != BackendState.OFFLINE
            and request.capabilities.issubset(b.capabilities)
        ]
        if not candidates:
            raise RuntimeError(
                "No execution backend satisfies required capabilities: "
                + ", ".join(sorted(request.capabilities))
            )
        return max(candidates, key=lambda b: (b.state == BackendState.READY, b.priority))

    def failover_order(self, request: ExecutionRequest) -> list[ExecutionBackend]:
        result: list[ExecutionBackend] = []
        excluded = set(request.exclude)
        while True:
            try:
                selected = self.select(ExecutionRequest(request.capabilities, frozenset(excluded)))
            except RuntimeError:
                return result
            result.append(selected)
            excluded.add(selected.name)


DEFAULT_BACKENDS = (
    ExecutionBackend(
        "github-hosted",
        frozenset({"linux", "python", "git", "ci"}),
        priority=20,
    ),
    ExecutionBackend(
        "container",
        frozenset({"linux", "python", "git", "ci", "isolated", "reproducible"}),
        priority=30,
    ),
    ExecutionBackend(
        "self-hosted",
        frozenset({"linux", "python", "git", "ci", "android", "persistent-tooling"}),
        priority=40,
    ),
    ExecutionBackend(
        "local",
        frozenset({"linux", "python", "git", "ci", "offline-preflight"}),
        priority=10,
    ),
)
