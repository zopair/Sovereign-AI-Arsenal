"""Small deterministic release gate for factory-produced artifacts."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    tests_passed: bool
    security_checked: bool
    provenance_recorded: bool

    @property
    def releasable(self) -> bool:
        return self.tests_passed and self.security_checked and self.provenance_recorded


def verify_release(*, tests_passed: bool, security_checked: bool, provenance_recorded: bool) -> VerificationResult:
    result = VerificationResult(tests_passed, security_checked, provenance_recorded)
    if not result.releasable:
        raise RuntimeError("release gate failed: required verification evidence is missing")
    return result
