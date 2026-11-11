from dataclasses import dataclass, field
from enum import Enum


class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    task_id: str
    objective: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependencies: set[str] = field(default_factory=set)
    required_capabilities: set[str] = field(default_factory=set)
    preferred_agent: str | None = None
    preferred_worker: str | None = None
    acceptance_tests: list[str] = field(default_factory=list)
    retry_limit: int = 3
    state: TaskState = TaskState.PENDING
    evidence: list[dict] = field(default_factory=list)


class TaskGraph:
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        if task.task_id in self.tasks:
            raise ValueError(f"duplicate task id: {task.task_id}")
        self.tasks[task.task_id] = task

    def ready(self) -> list[Task]:
        return [
            task for task in self.tasks.values()
            if task.state == TaskState.PENDING
            and all(self.tasks[d].state == TaskState.SUCCEEDED for d in task.dependencies)
        ]

    def validate(self) -> None:
        for task in self.tasks.values():
            missing = task.dependencies - self.tasks.keys()
            if missing:
                raise ValueError(f"task {task.task_id} has missing dependencies: {sorted(missing)}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError(f"cyclic task dependency: {task_id}")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in self.tasks[task_id].dependencies:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in self.tasks:
            visit(task_id)
