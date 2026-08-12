from dataclasses import dataclass

from factory.architecture.recovery_policy import (
    FailureClass,
    RecoveryAction,
    RecoveryBudget,
    RecoveryContext,
    classify_failure,
    next_action,
)
from factory.control.production_state import ProductionState, can_transition
from factory.execution.worker_protocol import ExecutionBroker
from factory.task_engine.task_model import Task, TaskGraph, TaskState
from factory.task_engine.task_router import TaskAssignment, assign_task


@dataclass
class OrchestrationResult:
    task_id: str
    assignment: TaskAssignment | None
    state: TaskState
    failure_class: FailureClass | None = None
    recovery_action: RecoveryAction | None = None


class ProductionOrchestrator:
    """Coordinates planning, routing, execution state and bounded recovery."""

    def __init__(self, broker: ExecutionBroker, budget: RecoveryBudget | None = None):
        self.graph = TaskGraph()
        self.broker = broker
        self.budget = budget or RecoveryBudget()
        self.recovery: dict[str, RecoveryContext] = {}
        self.production_state = ProductionState.PLANNED

    def add_task(self, task: Task) -> None:
        self.graph.add(task)

    def prepare(self) -> None:
        self.graph.validate()
        if can_transition(self.production_state, ProductionState.READY_FOR_EXECUTION):
            self.production_state = ProductionState.READY_FOR_EXECUTION

    def ready_tasks(self) -> list[Task]:
        return self.graph.ready()

    def assign(self, task: Task, agents: dict[str, set[str]]) -> TaskAssignment:
        workers = {
            worker_id: set(worker.capabilities)
            for worker_id, worker in self.broker.workers.items()
            if self.broker.healthy(worker)
        }
        return assign_task(task, agents, workers)

    def record_failure(self, task_id: str, message: str) -> OrchestrationResult:
        task = self.graph.tasks[task_id]
        task.state = TaskState.FAILED
        context = self.recovery.setdefault(task_id, RecoveryContext())
        context.attempts += 1
        failure = classify_failure(message)
        action = next_action(failure, context, self.budget)
        if action != RecoveryAction.ESCALATE:
            task.state = TaskState.READY
        return OrchestrationResult(task_id, None, task.state, failure, action)
