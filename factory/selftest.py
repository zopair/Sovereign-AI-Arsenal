from factory.manager import detect_capabilities, repo_identity
from factory.planner import plan
from factory.router import ProviderRouter
from factory.execution import ExecutionRequest, RunnerBroker, DEFAULT_BACKENDS


def test_repo_identity() -> None:
    assert repo_identity("https://github.com/zopair/demo") == ("zopair", "demo")


def test_capability_detection() -> None:
    result = detect_capabilities(
        ["package.json", "android/build.gradle", ".github/workflows/ci.yml", "tests/example.test.ts"],
        "This application uses Gemini, LangChain and Supabase.",
    )
    capabilities = {item["capability"] for item in result}
    assert {"node", "android", "github_actions", "testing", "ai", "database"}.issubset(capabilities)


def test_planner() -> None:
    result = plan(["web", "ai", "agents", "database"])
    selected = {item["capability"] for item in result["selected"]}
    assert selected == {"web", "ai", "agents", "database"}
    assert all(item["repository"] and item["license"] for item in result["selected"])


def test_provider_router() -> None:
    router = ProviderRouter()
    selected = router.choose({"chat"}, policy="smart")
    assert selected is not None
    assert "chat" in selected["capabilities"]

    before = router.snapshot()[selected["id"]]["failures"]
    router.record_failure(selected["id"], "synthetic test failure", cooldown_seconds=0)
    after = router.snapshot()[selected["id"]]["failures"]
    assert after == before + 1

    alternate = router.choose({"chat"}, policy="smart", exclude={selected["id"]})
    assert alternate is not None
    assert alternate["id"] != selected["id"]


def test_execution_broker() -> None:
    broker = RunnerBroker(DEFAULT_BACKENDS)
    selected = broker.select(ExecutionRequest(frozenset({"linux", "ci", "isolated"})))
    assert selected.name == "container"
    failover = broker.failover_order(ExecutionRequest(frozenset({"linux", "ci"})))
    assert len(failover) >= 2


if __name__ == "__main__":
    test_repo_identity()
    test_capability_detection()
    test_planner()
    test_provider_router()
    test_execution_broker()
    print("factory self-test: PASS")
