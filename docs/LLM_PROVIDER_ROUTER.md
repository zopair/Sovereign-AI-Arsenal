# Unified LLM Provider Router

The backend exposes an OpenAI-compatible chat-completions endpoint backed by a small provider failover pool.

## Configure providers

Set provider credentials as environment variables. Store no real keys in Git.

```dotenv
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
ZI_LLM_PROVIDERS='[{"name":"groq","base_url":"https://api.groq.com/openai/v1","api_key_env":"GROQ_API_KEY","model":"<current-model-id>","timeout_seconds":45,"cooldown_seconds":60}]'
```

Use model IDs and endpoints from each provider's current official documentation. The example model placeholder is intentional because provider catalogs and free quotas change.

A provider entry supports:
- `name`: unique stable identifier.
- `base_url`: OpenAI-compatible API root, normally ending in `/v1`.
- `api_key_env`: environment variable containing that provider's credential. It may be omitted only for an officially anonymous endpoint.
- `model`: model identifier accepted by that provider.
- `timeout_seconds` and `cooldown_seconds`: optional operational limits.

Remote endpoints must use HTTPS. Plain HTTP is accepted only for loopback development endpoints.

## Use the endpoint

All API routes require the existing `X-API-Key: $API_AUTH_TOKEN` application credential.

```bash
curl http://127.0.0.1:8000/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_AUTH_TOKEN" \
  -d '{"messages":[{"role":"user","content":"Summarize this task"}]}'
```

Inspect provider health/counters:

```bash
curl http://127.0.0.1:8000/api/v1/llm/providers/status \
  -H "X-API-Key: $API_AUTH_TOKEN"
```

## Routing and failover policy

- Providers are attempted in round-robin order.
- HTTP 429, 408, 425, 5xx, timeouts, and network errors trigger provider cooldown and failover.
- The router honors `Retry-After` when supplied.
- Invalid client requests (for example HTTP 400) are returned immediately rather than retried against every provider.
- When all providers are unavailable, the API returns HTTP 503.
- Provider keys are read from environment variables and are never returned by the status endpoint.
- The current implementation keeps health/cooldown counters in process memory. Restarting the service resets this state; shared Redis persistence is a future enhancement for multi-worker deployments.

**Quota and terms compliance:** this router fails over between distinct providers and models according to their published plans. It does not create accounts, rotate multiple keys to evade a provider's limits, bypass authentication, or claim free capacity is unlimited. Configure only endpoints and credentials you are authorized to use, and review each provider's commercial-use and data-retention terms before sending customer data.

## Current limitations

This first implementation handles non-streaming chat-completions JSON responses. It does not yet implement streaming, embeddings, image/audio APIs, per-model token accounting, persistent quota ledgers, or provider-specific tool-call normalization. Do not advertise those capabilities until implemented and tested.

## Open-source implementation references

These repositories were reviewed as implementation references, not copied into this project:

- [shihabshahrier/freelm](https://github.com/shihabshahrier/freelm) — MIT; multi-provider client, free-tier-aware failover, and OpenAI-compatible local endpoint.
- [nabinkhadka/free-llm-api](https://github.com/nabinkhadka/free-llm-api) — Apache-2.0; Python router with provider plugins, cooldowns, and weighted rotation.
- [TheMrguiller/Free-LLM-Router](https://github.com/TheMrguiller/Free-LLM-Router) — MIT; provider selection with cost and quota controls.

The account's [public-apis catalog](https://github.com/zopair/public-apis) is also useful for API discovery, but it is a directory rather than an inference gateway; individual API providers have separate pricing, license, commercial-use, and data-retention terms. LiteLLM was not selected as a dependency in this first version; verify its current license and dependency footprint before considering adoption.
