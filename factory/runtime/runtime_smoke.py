"""Dependency-free smoke test for the factory-owned runtime."""
from pathlib import Path
import tempfile

from factory.runtime.agent_runtime import AgentContext, AgentRuntime, Tool
from factory.runtime.project_workspace import ProjectWorkspace
from factory.runtime.release_gate import ReleaseGate, VerificationEvidence
from factory.execution import DEFAULT_BACKENDS, ExecutionRequest, RunnerBroker


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = ProjectWorkspace(Path(tmp) / "smoke", "smoke")
        workspace.initialize()
    tool = Tool("smoke", frozenset({"local"}), lambda _: {"ok": True})
    runtime = AgentRuntime([tool])
    assert runtime.execute(AgentContext("smoke", frozenset({"local"}), 1), tool, {})["ok"]
    assert RunnerBroker(DEFAULT_BACKENDS).select(ExecutionRequest(frozenset({"linux", "ci"})))
    assert ReleaseGate().evaluate(VerificationEvidence(True, True, True))
    print("factory runtime smoke: PASS")


if __name__ == "__main__":
    main()
