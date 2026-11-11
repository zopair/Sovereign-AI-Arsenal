from factory.execution.runner_broker import (
    BackendState,
    ExecutionBackend,
    ExecutionRequest,
    RunnerBroker,
)


def test_selects_capability_match_over_name():
    broker = RunnerBroker([
        ExecutionBackend("generic", frozenset({"linux", "ci"}), priority=1),
        ExecutionBackend("android-builder", frozenset({"linux", "ci", "android"}), priority=1),
    ])
    selected = broker.select(ExecutionRequest(frozenset({"linux", "ci", "android"})))
    assert selected.name == "android-builder"


def test_skips_offline_backend():
    broker = RunnerBroker([
        ExecutionBackend("broken", frozenset({"linux", "ci"}), BackendState.OFFLINE, 100),
        ExecutionBackend("fallback", frozenset({"linux", "ci"}), BackendState.READY, 1),
    ])
    assert broker.select(ExecutionRequest(frozenset({"linux", "ci"}))).name == "fallback"


def test_failover_produces_multiple_compatible_options():
    broker = RunnerBroker([
        ExecutionBackend("a", frozenset({"linux", "ci"}), priority=3),
        ExecutionBackend("b", frozenset({"linux", "ci"}), priority=2),
        ExecutionBackend("c", frozenset({"linux"}), priority=100),
    ])
    order = broker.failover_order(ExecutionRequest(frozenset({"linux", "ci"})))
    assert [x.name for x in order] == ["a", "b"]


def test_no_capable_backend_is_explicit():
    broker = RunnerBroker([ExecutionBackend("linux-only", frozenset({"linux"}))])
    try:
        broker.select(ExecutionRequest(frozenset({"linux", "gpu"})))
    except RuntimeError as exc:
        assert "gpu" in str(exc)
    else:
        raise AssertionError("expected no-backend failure")
