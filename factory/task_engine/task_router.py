from dataclasses import dataclass
from .task_model import Task


@dataclass(frozen=True)
class TaskAssignment:
    task_id: str
    agent: str
    worker: str


def assign_task(task: Task, available_agents: dict[str, set[str]], available_workers: dict[str, set[str]]) -> TaskAssignment:
    agents = [name for name, capabilities in available_agents.items() if task.required_capabilities.issubset(capabilities)]
    if not agents:
        raise LookupError(f"no agent satisfies capabilities for {task.task_id}")
    workers = [name for name, capabilities in available_workers.items() if task.required_capabilities.issubset(capabilities)]
    if not workers:
        raise LookupError(f"no worker satisfies capabilities for {task.task_id}")
    agent = task.preferred_agent if task.preferred_agent in agents else agents[0]
    worker = task.preferred_worker if task.preferred_worker in workers else workers[0]
    return TaskAssignment(task.task_id, agent, worker)
