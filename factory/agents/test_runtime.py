from factory.agents.runtime import AgentRuntime, Tool


def test_agent_can_discover_and_call_capability_tool():
    agent = AgentRuntime("builder")
    agent.register(Tool("calculator", frozenset({"compute"}), lambda value: value * 2))
    assert [t.name for t in agent.available_tools(frozenset({"compute"}))] == ["calculator"]
    assert agent.call("calculator", value=21) == 42


def test_agent_budget_is_enforced():
    agent = AgentRuntime("builder", budget=1)
    agent.register(Tool("noop", frozenset({"test"}), lambda: "ok"))
    assert agent.call("noop") == "ok"
    try:
        agent.call("noop")
    except RuntimeError as exc:
        assert "budget" in str(exc)
    else:
        raise AssertionError("expected budget exhaustion")
