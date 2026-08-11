"""Deterministic end-to-end gate for the provider-neutral execution path."""
from .local_worker import LocalWorker
from .worker_protocol import ExecutionBroker, JobEvidence, JobState, WorkerRecord


def run_gate() -> dict[str, object]:
    worker = LocalWorker()
    result = worker.run_self_check()
    broker = ExecutionBroker()
    broker.register(WorkerRecord(worker.worker_id, worker.capabilities, heartbeat_at=0))
    selected = broker.select(frozenset({"linux", "python", "ci"}))
    evidence = JobEvidence(
        job_id="production-gate",
        state=JobState.SUCCEEDED if result["ok"] else JobState.FAILED,
        worker_id=selected.worker_id,
        logs=[result["stdout"]],
        started_at=1.0,
        finished_at=2.0,
    )
    return {
        "ok": bool(result["ok"] and evidence.has_execution_evidence()),
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
