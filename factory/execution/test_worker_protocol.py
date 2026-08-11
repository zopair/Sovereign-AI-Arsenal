from factory.execution.worker_protocol import ExecutionBroker, JobEvidence, JobState, WorkerRecord
import pytest


def test_broker_selects_healthy_capable_worker():
    broker = ExecutionBroker()
    broker.register(WorkerRecord("vm-1", frozenset({"linux", "python"}), heartbeat_at=100))
    assert broker.select(frozenset({"linux"}), now=150).worker_id == "vm-1"


def test_broker_rejects_stale_worker():
    broker = ExecutionBroker(heartbeat_timeout=10)
    broker.register(WorkerRecord("vm-1", frozenset({"linux"}), heartbeat_at=100))
    with pytest.raises(LookupError):
        broker.select(frozenset({"linux"}), now=111)


def test_evidence_distinguishes_pre_execution_failure():
    evidence = JobEvidence("job-1", JobState.FAILED)
    assert evidence.has_execution_evidence() is False
