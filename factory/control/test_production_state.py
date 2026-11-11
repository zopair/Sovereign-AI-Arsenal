import pytest
from factory.control.production_state import ProductionState, can_transition


def test_happy_path_transitions():
    path = [
        ProductionState.INTAKE,
        ProductionState.ANALYZING,
        ProductionState.PLANNED,
        ProductionState.READY_FOR_EXECUTION,
        ProductionState.RUNNING,
        ProductionState.TESTING,
        ProductionState.VERIFYING,
        ProductionState.RELEASE_READY,
        ProductionState.RELEASED,
    ]
    assert all(can_transition(a, b) for a, b in zip(path, path[1:]))


def test_failure_can_recover_without_terminal_stop():
    assert can_transition(ProductionState.RUNNING, ProductionState.RECOVERING)
    assert can_transition(ProductionState.RECOVERING, ProductionState.READY_FOR_EXECUTION)


def test_illegal_transition_rejected():
    assert not can_transition(ProductionState.INTAKE, ProductionState.RELEASED)
