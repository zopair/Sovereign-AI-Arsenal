from factory.runtime.agent_runtime import AgentContext, AgentRuntime, Tool
from factory.runtime.release_gate import ReleaseGate, VerificationEvidence


def test_agent_can_select_and_invoke_capable_tool():
    tool = Tool("echo", frozenset({"text", "local"}), lambda p: {"echo": p["value"]})
    runtime = AgentRuntime([tool])
    ctx = AgentContext("echo", frozenset({"text"}), budget=1)
    assert runtime.execute(ctx, tool, {"value": "ok"}) == {"echo": "ok"}
    assert ctx.budget == 0


def test_agent_budget_blocks_extra_execution():
    tool = Tool("echo", frozenset({"text"}), lambda p: p)
    runtime = AgentRuntime([tool])
    ctx = AgentContext("echo", frozenset({"text"}), budget=0)
    try:
        runtime.execute(ctx, tool, {})
    except RuntimeError:
        pass
    else:
        raise AssertionError("budget must block execution")


def test_release_gate_requires_evidence():
    gate = ReleaseGate()
    assert not gate.evaluate(VerificationEvidence(True, False, True))
    assert gate.explain(VerificationEvidence(True, False, True)) == ["security"]
    assert gate.evaluate(VerificationEvidence(True, True, True))
