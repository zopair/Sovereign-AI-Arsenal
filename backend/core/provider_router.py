"""OpenAI-compatible multi-provider router with quota-aware failover.

Failover is between independently configured providers, not duplicate keys used
to evade one provider's published limits. Cooldown counters are process-local.
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.parse import urlparse

import httpx


class ProviderUnavailable(RuntimeError):
    """Raised when no configured provider is currently eligible."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 45.0
    cooldown_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.model.strip():
            raise ValueError("Provider name and model are required")
        parsed = urlparse(self.base_url)
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and parsed.hostname not in local_hosts:
            raise ValueError("Remote provider endpoints must use HTTPS")
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Provider base_url must be an absolute HTTP(S) URL")
        if self.timeout_seconds <= 0 or self.cooldown_seconds < 0:
            raise ValueError("Timeout must be positive and cooldown cannot be negative")


@dataclass
class _ProviderState:
    cooldown_until: float = 0.0
    last_error: str | None = None
    successes: int = 0
    failures: int = 0


@dataclass
class ProviderPool:
    providers: list[Provider]
    client: httpx.AsyncClient | None = None
    clock: Callable[[], float] = time.monotonic
    _states: dict[str, _ProviderState] = field(init=False, default_factory=dict)
    _cursor: int = field(init=False, default=0)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        if not self.providers:
            raise ValueError("At least one provider is required")
        names = [provider.name for provider in self.providers]
        if len(names) != len(set(names)):
            raise ValueError("Provider names must be unique")
        self._states = {name: _ProviderState() for name in names}

    async def _next_eligible(self) -> Provider:
        async with self._lock:
            now = self.clock()
            for offset in range(len(self.providers)):
                index = (self._cursor + offset) % len(self.providers)
                provider = self.providers[index]
                if self._states[provider.name].cooldown_until <= now:
                    self._cursor = (index + 1) % len(self.providers)
                    return provider
        raise ProviderUnavailable("All configured providers are cooling down")

    @staticmethod
    def _retry_after(response: httpx.Response, fallback: float) -> float:
        value = response.headers.get("Retry-After")
        if not value:
            return fallback
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                target = parsedate_to_datetime(value)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=timezone.utc)
                return max(0.0, (target - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return fallback

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a chat request and fail over on transient/provider configuration errors."""
        attempted: set[str] = set()
        last_error: Exception | None = None
        client = self.client or httpx.AsyncClient()
        owns_client = self.client is None
        try:
            while len(attempted) < len(self.providers):
                try:
                    provider = await self._next_eligible()
                except ProviderUnavailable:
                    if last_error:
                        raise ProviderUnavailable("No healthy provider remains") from last_error
                    raise
                if provider.name in attempted:
                    break
                attempted.add(provider.name)
                request_payload = dict(payload)
                request_payload["model"] = provider.model
                url = provider.base_url.rstrip("/") + "/chat/completions"
                headers = {"Content-Type": "application/json"}
                if provider.api_key:
                    headers["Authorization"] = "Bearer " + provider.api_key
                try:
                    response = await client.post(
                        url,
                        json=request_payload,
                        headers=headers,
                        timeout=provider.timeout_seconds,
                    )
                    status_code = response.status_code
                    retryable = (
                        status_code in {401, 403, 404, 408, 425, 429}
                        or status_code >= 500
                    )
                    if retryable:
                        fallback = max(provider.cooldown_seconds, 300.0) if status_code in {401, 403, 404} else provider.cooldown_seconds
                        delay = self._retry_after(response, fallback)
                        state = self._states[provider.name]
                        state.cooldown_until = self.clock() + delay
                        state.last_error = f"HTTP {status_code}"
                        state.failures += 1
                        last_error = httpx.HTTPStatusError(
                            f"Provider {provider.name} returned HTTP {status_code}",
                            request=response.request,
                            response=response,
                        )
                        continue
                    response.raise_for_status()
                    self._states[provider.name].successes += 1
                    self._states[provider.name].last_error = None
                    return response.json()
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    state = self._states[provider.name]
                    state.cooldown_until = self.clock() + provider.cooldown_seconds
                    state.last_error = type(exc).__name__
                    state.failures += 1
                    last_error = exc
                    continue
            if last_error:
                raise ProviderUnavailable("All eligible providers failed") from last_error
            raise ProviderUnavailable("No untried eligible provider remains")
        finally:
            if owns_client:
                await client.aclose()

    def status(self) -> dict[str, dict[str, Any]]:
        now = self.clock()
        return {
            name: {
                "cooldown_remaining_seconds": max(0.0, state.cooldown_until - now),
                "last_error": state.last_error,
                "successes": state.successes,
                "failures": state.failures,
            }
            for name, state in self._states.items()
        }


def providers_from_environment() -> list[Provider]:
    """Load provider metadata from JSON; API keys are read from named env vars."""
    import json

    raw = os.getenv("ZI_LLM_PROVIDERS", "[]")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("ZI_LLM_PROVIDERS must contain valid JSON") from exc
    if not isinstance(entries, list):
        raise ValueError("ZI_LLM_PROVIDERS must be a JSON array")

    providers = []
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("Each provider entry must be an object")
        key_env = item.get("api_key_env", "")
        providers.append(
            Provider(
                name=str(item["name"]),
                base_url=str(item["base_url"]),
                api_key=os.getenv(key_env, "") if key_env else "",
                model=str(item["model"]),
                timeout_seconds=float(item.get("timeout_seconds", 45)),
                cooldown_seconds=float(item.get("cooldown_seconds", 30)),
            )
        )
    return providers
