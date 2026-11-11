import pytest
from .task_model import Task, TaskGraph, TaskState
from .task_router import assign_task


def test_dependencies_control_readiness_and_allow_parallel_tasks():
    graph = TaskGraph()
    graph.add(Task("A", "prepare"))
    graph.add(Task("B", "build", dependencies={"A"}))
    graph.add(Task("C", "docs", dependencies={"A"}))
    graph.add(Task("D", "release", dependencies={"B", "C"}))
    graph.validate()
    assert [t.task_id for t in graph.ready()] == ["A"]
    graph.tasks["A"].state = TaskState.SUCCEEDED
    assert {t.task_id for t in graph.ready()} == {"B", "C"}


def test_missing_dependency_is_rejected():
    graph = TaskGraph()
    graph.add(Task("A", "build", dependencies={"missing"}))
    with pytest.raises(ValueError):
        graph.validate()


def test_cycle_is_rejected():
    graph = TaskGraph()
    graph.add(Task("A", "a", dependencies={"B"}))
    graph.add(Task("B", "b", dependencies={"A"}))
    with pytest.raises(ValueError):
        graph.validate()


def test_router_selects_capable_agent_and_worker():
    task = Task("android", "build apk", required_capabilities={"android", "linux"})
    assignment = assign_task(
        task,
        {"generic": {"linux"}, "android-agent": {"android", "linux"}},
        {"vm-1": {"linux"}, "android-vm": {"android", "linux"}},
    )
    assert assignment.agent == "android-agent"
    assert assignment.worker == "android-vm"
