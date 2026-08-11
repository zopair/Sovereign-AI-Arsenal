from factory.execution.local_worker import LocalWorker
from factory.execution.worker_protocol import JobState


def test_local_worker_emits_execution_evidence():
    evidence = LocalWorker().run_self_check()
    assert evidence.state == JobState.SUCCEEDED
    assert evidence.worker_id == "local-worker"
    assert evidence.has_execution_evidence()
    assert "factory-worker-ok" in evidence.logs[0]
