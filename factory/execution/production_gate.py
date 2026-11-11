"""Deterministic gate for provider-neutral execution."""
from .local_worker import LocalWorker
from .worker_protocol import ExecutionBroker, JobState


def run_gate() -> dict[str, object]:
    worker = LocalWorker()
    broker = ExecutionBroker()
    broker.register(worker.record())
    selected = broker.select(frozenset({"linux", "python", "ci"}))
    evidence = worker.run_self_check()
    return {
        "ok": evidence.state == JobState.SUCCEEDED and evidence.has_execution_evidence(),
        "worker": selected.worker_id,
        "evidence": evidence,
    }


def test_production_gate() -> None:
    result = run_gate()
    assert result["ok"] is True
    assert result["worker"] == "local-worker"


if __name__ == "__main__":
    test_production_gate()
    print("production execution gate: PASS")
