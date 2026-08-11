"""Classify and recover GitHub Actions failures using observed evidence.

The controller treats GitHub Actions as a replaceable control/execution backend.
A run with failed jobs but no steps/logs is classified as pre-execution or runner
infrastructure failure rather than a factory-code failure.
"""
from dataclasses import dataclass
from enum import Enum


class FailureClass(str, Enum):
    PRE_EXECUTION = "pre_execution"
    RUNNER_INFRA = "runner_infrastructure"
    WORKFLOW = "workflow"
    TEST = "test"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class JobEvidence:
    conclusion: str | None
    steps_present: bool
    logs_available: bool


@dataclass(frozen=True)
class RecoveryDecision:
    classification: FailureClass
    retry_job: bool
    retry_limit: int
    alternate_backend: bool
    reason: str


def classify_job(evidence: JobEvidence) -> FailureClass:
    if evidence.conclusion in {"failure", "cancelled", "timed_out"} and not evidence.steps_present:
        return FailureClass.PRE_EXECUTION
    if evidence.conclusion == "failure" and not evidence.logs_available:
        return FailureClass.RUNNER_INFRA
    if evidence.conclusion == "failure":
        return FailureClass.TEST
    return FailureClass.UNKNOWN


def decide_recovery(evidence: JobEvidence) -> RecoveryDecision:
    classification = classify_job(evidence)
    if classification in {FailureClass.PRE_EXECUTION, FailureClass.RUNNER_INFRA}:
        return RecoveryDecision(
            classification, retry_job=True, retry_limit=1, alternate_backend=True,
            reason="No executable-step evidence; retry once, then fail over to another backend.",
        )
    return RecoveryDecision(
        classification, retry_job=False, retry_limit=0, alternate_backend=False,
        reason="Evidence points beyond pre-execution infrastructure; preserve evidence for targeted repair.",
    )
