"""Dependency-aware recovery orchestration for the application factory."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable


class FailureClass(str, Enum):
    RECOVERABLE = "recoverable"
    COMPLEX = "complex"
    DANGEROUS = "dangerous"


class TaskState(str, Enum):
    READY = "ready"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True)
class Failure:
    task_id: str
    failure_class: FailureClass
    message: str
    impact: frozenset[str] = frozenset()
    requires_approval: bool = False


@dataclass(frozen=True)
class RecoveryStrategy:
    name: str
    recover: Callable[[Failure], bool]
    estimated_cost: float = 0.0


@dataclass
class RecoveryBudget:
    max_attempts: int = 4
    max_cost: float = 10.0
    attempts: int = 0
    cost: float = 0.0

    def allows(self, strategy: RecoveryStrategy) -> bool:
        return self.attempts < self.max_attempts and self.cost + strategy.estimated_cost <= self.max_cost

    def consume(self, strategy: RecoveryStrategy) -> None:
        self.attempts += 1
        self.cost += strategy.estimated_cost


@dataclass
class RecoveryResult:
    task_id: str
    state: TaskState
    attempts: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    reason: str | None = None


class RecoveryOrchestrator:
    """Try bounded recovery strategies without turning local failures into global stops."""

    def __init__(self, strategies: Iterable[RecoveryStrategy], budget: RecoveryBudget | None = None) -> None:
        self.strategies = list(strategies)
        self.budget = budget or RecoveryBudget()

    def recover(self, failure: Failure) -> RecoveryResult:
        if failure.requires_approval or failure.failure_class is FailureClass.DANGEROUS:
            return RecoveryResult(
                failure.task_id,
                TaskState.APPROVAL_REQUIRED,
                reason="Safety or approval boundary reached; unrelated work may continue.",
            )

        result = RecoveryResult(failure.task_id, TaskState.RECOVERING)
        for strategy in self.strategies:
            if not self.budget.allows(strategy):
                break
            self.budget.consume(strategy)
            result.attempts.append(strategy.name)
            try:
                ok = strategy.recover(failure)
            except Exception as exc:
                result.evidence.append(f"{strategy.name}: exception={type(exc).__name__}: {exc}")
                continue
            if ok:
                result.state = TaskState.COMPLETED
                result.evidence.append(f"{strategy.name}: verified_success")
                return result
            result.evidence.append(f"{strategy.name}: no_recovery")

        result.state = TaskState.BLOCKED
        result.reason = "Recovery budget or available strategies exhausted; scope remains local to the failed task."
        return result


def run_independent_tasks(tasks: dict[str, Callable[[], bool]]) -> dict[str, bool]:
    """Run independent work and isolate failures instead of failing the whole batch."""
    results: dict[str, bool] = {}
    for task_id, task in tasks.items():
        try:
            results[task_id] = bool(task())
        except Exception:
            results[task_id] = False
    return results
