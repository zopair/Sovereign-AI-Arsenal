from factory.manager import detect_capabilities, repo_identity


def test_repo_identity() -> None:
    assert repo_identity("https://github.com/zopair/demo") == ("zopair", "demo")


def test_capability_detection() -> None:
    result = detect_capabilities(
        ["package.json", "android/build.gradle", ".github/workflows/ci.yml", "tests/example.test.ts"],
        "This application uses Gemini, LangChain and Supabase.",
    )
    capabilities = {item["capability"] for item in result}
    assert {"node", "android", "github_actions", "testing", "ai", "database"}.issubset(capabilities)


if __name__ == "__main__":
    test_repo_identity()
    test_capability_detection()
    print("factory self-test: PASS")
