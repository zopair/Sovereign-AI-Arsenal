"""Executable tests for the factory recovery contract."""

from factory.recovery import (
    Failure,
    FailureClass,
    RecoveryBudget,
    RecoveryOrchestrator,
    RecoveryStrategy,
    TaskState,
    run_independent_tasks,
)


def test_rotates_after_first_strategy_fails() -> None:
    calls: list[str] = []

    def fail(_: Failure) -> bool:
        calls.append("primary")
        return False

    def succeed(_: Failure) -> bool:
        calls.append("fallback")
        return True

    result = RecoveryOrchestrator(
        [RecoveryStrategy("primary", fail), RecoveryStrategy("fallback", succeed)]
    ).recover(Failure("build", FailureClass.RECOVERABLE, "dependency failure"))

    assert result.state is TaskState.COMPLETED
    assert calls == ["primary", "fallback"]
    assert result.attempts == ["primary", "fallback"]


def test_dangerous_work_requires_approval_but_does_not_global_stop() -> None:
    result = RecoveryOrchestrator([]).recover(
        Failure("production-migration", FailureClass.DANGEROUS, "destructive migration", requires_approval=True)
    )
    assert result.state is TaskState.APPROVAL_REQUIRED


def test_recovery_budget_prevents_infinite_retry() -> None:
    attempts: list[int] = []

    def never(_: Failure) -> bool:
        attempts.append(1)
        return False

    result = RecoveryOrchestrator(
        [RecoveryStrategy("retry", never, estimated_cost=1.0)],
        RecoveryBudget(max_attempts=2, max_cost=2.0),
    ).recover(Failure("test", FailureClass.COMPLEX, "flaky test"))

    assert result.state is TaskState.BLOCKED
    assert len(attempts) == 1
    assert result.attempts == ["retry"]


def test_independent_tasks_continue_after_one_failure() -> None:
    result = run_independent_tasks({
        "ui": lambda: True,
        "api": lambda: (_ for _ in ()).throw(RuntimeError("api down")),
        "docs": lambda: True,
    })
    assert result == {"ui": True, "api": False, "docs": True}
