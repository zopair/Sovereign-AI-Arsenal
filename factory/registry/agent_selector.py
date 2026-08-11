"""Select agents by capability and evidence, not popularity."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentCandidate:
    name: str
    capabilities: frozenset[str]
    tests_passed: bool
    security_checked: bool
    license_checked: bool
    score: float


def rank(candidates: list[AgentCandidate], required: frozenset[str]) -> list[AgentCandidate]:
    eligible = [
        c for c in candidates
        if required.issubset(c.capabilities)
        and c.tests_passed and c.security_checked and c.license_checked
    ]
    return sorted(eligible, key=lambda c: c.score, reverse=True)
