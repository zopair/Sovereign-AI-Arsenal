# Smart Provider Routing

The Factory separates **task intent** from **provider choice**.

A project asks for a capability such as `chat`, `tool-calling`, `local`, or `gpu`. The router then selects an available provider using a policy.

## Policies

- `priority`: deterministic order from the registry.
- `round_robin`: spreads requests across eligible providers.
- `lowest_latency`: prefers the fastest provider observed by the router.
- `smart`: combines configured priority, observed success rate, and latency.

## Failover

A failed provider is placed in a short cooldown and excluded from the current request's retry chain. The router then selects the next eligible provider. This prevents a dead endpoint from consuming every attempt.

## Credential boundary

Provider tokens are environment variables or runner secrets. They are never stored in `providers.json` and never committed to the repository.

Example variables:

```text
GITHUB_MODELS_TOKEN
OPENAI_API_KEY
VLLM_API_KEY
LITELLM_API_KEY
```

## GitHub Models

The registry includes GitHub Models as a provider because GitHub exposes a model inference API and a model catalog. This gives the Factory a GitHub-native model option in addition to external and local endpoints.

The current implementation uses the OpenAI-compatible chat-completions shape, which also makes local Ollama/vLLM and gateway deployments interchangeable at the router boundary.

## Open-source gateway option

LiteLLM is tracked as an optional gateway. It can unify many upstream LLM providers behind a common API and supports retry/fallback, load balancing, spend tracking, and observability. The Factory can therefore use either direct provider adapters or delegate routing to an OSS gateway.

The Factory deliberately keeps its own routing layer small and deterministic. A gateway can be added when centralized provider translation, accounting, or policy enforcement is more valuable than direct calls.
