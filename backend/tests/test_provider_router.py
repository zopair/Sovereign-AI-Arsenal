import httpx
import pytest

from backend.core.provider_router import Provider, ProviderPool, ProviderUnavailable


def provider(name, url, key="test-key"):
    return Provider(
        name=name,
        base_url=url,
        api_key=key,
        model="test-model",
        timeout_seconds=2,
        cooldown_seconds=30,
    )


@pytest.mark.asyncio
async def test_pool_fails_over_after_rate_limit_and_cools_provider():
    calls = []

    def handler(request):
        calls.append(request.url.host)
        if request.url.host == "first.example":
            return httpx.Response(429, headers={"Retry-After": "12"}, json={"error": "limited"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    pool = ProviderPool(
        [provider("first", "https://first.example/v1"), provider("second", "https://second.example/v1")],
        client=client,
    )
    result = await pool.chat_completion({"messages": [{"role": "user", "content": "hello"}]})

    assert result["choices"][0]["message"]["content"] == "ok"
    assert calls == ["first.example", "second.example"]
    assert pool.status()["first"]["cooldown_remaining_seconds"] > 0
    await client.aclose()


@pytest.mark.asyncio
async def test_pool_does_not_fail_over_on_invalid_request():
    calls = []

    def handler(request):
        calls.append(request.url.host)
        return httpx.Response(400, json={"error": "bad request"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    pool = ProviderPool(
        [provider("first", "https://first.example/v1"), provider("second", "https://second.example/v1")],
        client=client,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await pool.chat_completion({"messages": []})

    assert calls == ["first.example"]
    await client.aclose()


@pytest.mark.asyncio
async def test_pool_reports_unavailable_when_all_providers_are_cooling_down():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(429)))
    pool = ProviderPool([provider("only", "https://only.example/v1")], client=client)

    with pytest.raises(ProviderUnavailable):
        await pool.chat_completion({"messages": []})

    with pytest.raises(ProviderUnavailable):
        await pool.chat_completion({"messages": []})

    await client.aclose()


def test_provider_rejects_non_https_remote_endpoint():
    with pytest.raises(ValueError):
        Provider(name="unsafe", base_url="http://remote.example/v1", api_key="x", model="m")

def test_local_ollama_provider_can_be_loaded_without_api_credentials(monkeypatch):
    import json

    from backend.core.provider_router import providers_from_environment

    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.setenv(
        "ZI_LLM_PROVIDERS",
        json.dumps([{
            "name": "ollama-local",
            "base_url": "http://localhost:11434/v1",
            "model": "gemma4:e2b",
        }]),
    )

    providers = providers_from_environment()

    assert len(providers) == 1
    assert providers[0].name == "ollama-local"
    assert providers[0].api_key == ""
    assert providers[0].base_url == "http://localhost:11434/v1"


@pytest.mark.asyncio
async def test_local_ollama_request_uses_openai_compatible_path_without_auth_header():
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "local response"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    local_provider = Provider(
        name="ollama-local",
        base_url="http://localhost:11434/v1",
        api_key="",
        model="gemma4:e2b",
        timeout_seconds=2,
        cooldown_seconds=0,
    )
    pool = ProviderPool([local_provider], client=client)

    result = await pool.chat_completion({
        "messages": [{"role": "user", "content": "hello"}],
    })

    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["authorization"] is None
    assert result["choices"][0]["message"]["content"] == "local response"
    await client.aclose()

