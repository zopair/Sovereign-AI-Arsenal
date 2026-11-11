from factory.architecture.recovery_policy import (
    FailureClass,
    RecoveryAction,
    RecoveryBudget,
    RecoveryContext,
    classify_failure,
    next_action,
)


def test_runner_failure_routes_to_reschedule():
    failure = classify_failure("runner heartbeat timeout")
    assert failure == FailureClass.WORKER
    assert next_action(failure, RecoveryContext(), RecoveryBudget()) == RecoveryAction.RESCHEDULE


def test_provider_failure_routes_to_provider_switch():
    failure = classify_failure("GitHub Actions provider unavailable")
    assert failure == FailureClass.PROVIDER
    assert next_action(failure, RecoveryContext(), RecoveryBudget()) == RecoveryAction.SWITCH_PROVIDER


def test_recovery_is_bounded():
    failure = FailureClass.CODE
    ctx = RecoveryContext(attempts=5, repair_attempts=3)
    assert next_action(failure, ctx, RecoveryBudget()) == RecoveryAction.ESCALATE
