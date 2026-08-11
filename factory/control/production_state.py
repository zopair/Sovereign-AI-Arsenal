"""Provider-neutral production lifecycle states."""
from enum import Enum


class ProductionState(str, Enum):
    INTAKE = "intake"
    ANALYZING = "analyzing"
    PLANNED = "planned"
    READY_FOR_EXECUTION = "ready_for_execution"
    WAITING_FOR_WORKER = "waiting_for_worker"
    RUNNING = "running"
    TESTING = "testing"
    RECOVERING = "recovering"
    VERIFYING = "verifying"
    RELEASE_READY = "release_ready"
    RELEASED = "released"
    BLOCKED = "blocked"


ALLOWED_TRANSITIONS = {
    ProductionState.INTAKE: {ProductionState.ANALYZING},
    ProductionState.ANALYZING: {ProductionState.PLANNED},
    ProductionState.PLANNED: {ProductionState.READY_FOR_EXECUTION},
    ProductionState.READY_FOR_EXECUTION: {ProductionState.WAITING_FOR_WORKER, ProductionState.RUNNING},
    ProductionState.WAITING_FOR_WORKER: {ProductionState.RUNNING, ProductionState.BLOCKED},
    ProductionState.RUNNING: {ProductionState.TESTING, ProductionState.RECOVERING},
    ProductionState.TESTING: {ProductionState.VERIFYING, ProductionState.RECOVERING},
    ProductionState.RECOVERING: {ProductionState.READY_FOR_EXECUTION, ProductionState.BLOCKED},
    ProductionState.VERIFYING: {ProductionState.RELEASE_READY, ProductionState.RECOVERING},
    ProductionState.RELEASE_READY: {ProductionState.RELEASED},
}


def can_transition(current: ProductionState, target: ProductionState) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())
