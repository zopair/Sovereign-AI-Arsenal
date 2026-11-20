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
