"""Deterministic scenarios for the factory production gate."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AcceptanceScenario:
    name: str
    required_capabilities: frozenset[str]
    injected_failure: str | None = None
    expected_recovery: str | None = None


SCENARIOS = (
    AcceptanceScenario("happy-path", frozenset({"linux", "python"})),
    AcceptanceScenario("worker-loss", frozenset({"linux", "python"}), "worker_lost", "reschedule"),
    AcceptanceScenario("test-failure", frozenset({"linux", "python"}), "test_failed", "repair-and-retest"),
    AcceptanceScenario("dependency-failure", frozenset({"linux", "python"}), "dependency_failed", "repair-and-rebuild"),
)
