import pytest

from factory.execution.vm_agent import WorkerState, simulated_worker


def test_simulated_vm_health_and_build():
    worker = simulated_worker()
    assert worker.can_run(frozenset({"linux", "python"}))
    assert worker.execute("health")["ok"] is True
    result = worker.execute("build", {"artifact": "demo.apk"})
    assert result == {"ok": True, "artifact": "demo.apk"}
    assert worker.state == WorkerState.READY


def test_simulated_vm_rejects_unsupported_operation():
    worker = simulated_worker()
    with pytest.raises(LookupError):
        worker.execute("shell")
