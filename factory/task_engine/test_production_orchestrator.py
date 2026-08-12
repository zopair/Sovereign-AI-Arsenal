from factory.execution.worker_protocol import ExecutionBroker, WorkerRecord
from factory.task_engine.production_orchestrator import ProductionOrchestrator
from factory.task_engine.task_model import Task, TaskState
from factory.architecture.recovery_policy import FailureClass, RecoveryAction


def test_orchestrator_routes_ready_task_to_capable_worker():
    broker = ExecutionBroker()
    broker.register(WorkerRecord("vm-python", frozenset({"linux", "python"})))
    orchestrator = ProductionOrchestrator(broker)
    task = Task("build", "build project", required_capabilities={"linux", "python"})
    orchestrator.add_task(task)
    orchestrator.prepare()
    assignment = orchestrator.assign(task, {"builder": {"linux", "python"}})
    assert assignment.worker == "vm-python"


def test_orchestrator_reopens_task_for_worker_recovery():
    broker = ExecutionBroker()
    orchestrator = ProductionOrchestrator(broker)
    task = Task("build", "build project")
    orchestrator.add_task(task)
    result = orchestrator.record_failure("build", "worker heartbeat timeout")
    assert result.failure_class == FailureClass.WORKER
    assert result.recovery_action == RecoveryAction.RESCHEDULE
    assert result.state == TaskState.READY
