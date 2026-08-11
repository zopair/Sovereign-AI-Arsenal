from dataclasses import dataclass
from enum import Enum


class FailureClass(str, Enum):
    CODE = "code"
    DEPENDENCY = "dependency"
    WORKER = "worker"
    PROVIDER = "provider"
    TEST = "test"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    REPAIR = "repair"
    RESCHEDULE = "reschedule"
    SWITCH_PROVIDER = "switch_provider"
    RETEST = "retest"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class RecoveryBudget:
    max_attempts: int = 5
    max_repair_attempts: int = 3


@dataclass
class RecoveryContext:
    attempts: int = 0
    repair_attempts: int = 0


def classify_failure(message: str) -> FailureClass:
    text = message.lower()
    if any(x in text for x in ("runner", "worker", "heartbeat", "blobnotfound")):
        return FailureClass.WORKER
    if any(x in text for x in ("dependency", "pip", "npm", "package")):
        return FailureClass.DEPENDENCY
    if any(x in text for x in ("test", "assert")):
        return FailureClass.TEST
    if any(x in text for x in ("provider", "github actions", "api")):
        return FailureClass.PROVIDER
    if any(x in text for x in ("syntax", "compile", "exception")):
        return FailureClass.CODE
    return FailureClass.UNKNOWN


def next_action(failure: FailureClass, ctx: RecoveryContext, budget: RecoveryBudget) -> RecoveryAction:
    if ctx.attempts >= budget.max_attempts:
        return RecoveryAction.ESCALATE
    if failure == FailureClass.WORKER:
        return RecoveryAction.RESCHEDULE
    if failure == FailureClass.PROVIDER:
        return RecoveryAction.SWITCH_PROVIDER
    if failure == FailureClass.DEPENDENCY:
        return RecoveryAction.REPAIR if ctx.repair_attempts < budget.max_repair_attempts else RecoveryAction.ESCALATE
    if failure in (FailureClass.CODE, FailureClass.TEST):
        return RecoveryAction.REPAIR if ctx.repair_attempts < budget.max_repair_attempts else RecoveryAction.ESCALATE
    return RecoveryAction.REPAIR if ctx.repair_attempts < budget.max_repair_attempts else RecoveryAction.ESCALATE
