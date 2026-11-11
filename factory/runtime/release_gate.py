"""Evidence-based release gate."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationEvidence:
    tests_passed: bool
    security_checked: bool
    provenance_recorded: bool
    reproducible: bool = False


class ReleaseGate:
    def evaluate(self, evidence: VerificationEvidence) -> bool:
        return all((evidence.tests_passed, evidence.security_checked, evidence.provenance_recorded))

    def explain(self, evidence: VerificationEvidence) -> list[str]:
        missing = []
        if not evidence.tests_passed:
            missing.append("tests")
        if not evidence.security_checked:
            missing.append("security")
        if not evidence.provenance_recorded:
            missing.append("provenance")
        return missing
