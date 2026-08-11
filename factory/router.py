from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROVIDERS_PATH = ROOT / "registry" / "providers.json"


@dataclass
class ProviderState:
    provider_id: str
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    disabled_until: float = 0.0
    last_error: str | None = None

    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        return self.successes / total if total else 1.0

    @property
    avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.successes if self.successes else float("inf")


@dataclass
class ProviderRouter:
    config_path: Path = PROVIDERS_PATH
    states: dict[str, ProviderState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.providers: list[dict[str, Any]] = config.get("providers", [])
        for provider in self.providers:
            provider_id = provider["id"]
            self.states.setdefault(provider_id, ProviderState(provider_id))

    def candidates(self, required_capabilities: set[str], exclude: set[str] | None = None) -> list[dict[str, Any]]:
        exclude = exclude or set()
        now = time.time()
        candidates = []
        for provider in self.providers:
            pid = provider["id"]
            if pid in exclude or self.states[pid].disabled_until > now:
                continue
            capabilities = set(provider.get("capabilities", []))
            if not required_capabilities.issubset(capabilities):
                continue
            candidates.append(provider)
        return candidates

    def rank(self, providers: list[dict[str, Any]], policy: str = "smart") -> list[dict[str, Any]]:
        if policy == "round_robin":
            ordered = list(providers)
            random.shuffle(ordered)
            return ordered
        if policy == "priority":
            return sorted(providers, key=lambda p: p.get("priority", 100))
        if policy == "lowest_latency":
            return sorted(providers, key=lambda p: self.states[p["id"]].avg_latency_ms)

        # Smart: balance configured priority, reliability, and observed latency.
        def score(provider: dict[str, Any]) -> float:
            state = self.states[provider["id"]]
            priority = provider.get("priority", 100)
            reliability = state.success_rate
            latency_penalty = 0.0 if state.avg_latency_ms == float("inf") else min(state.avg_latency_ms / 1000.0, 20.0)
            return (priority / 100.0) + latency_penalty - (reliability * 2.0)

        return sorted(providers, key=score)

    def choose(self, required_capabilities: set[str], policy: str = "smart", exclude: set[str] | None = None) -> dict[str, Any] | None:
        candidates = self.candidates(required_capabilities, exclude)
        ranked = self.rank(candidates, policy)
        return ranked[0] if ranked else None

    def record_success(self, provider_id: str, latency_ms: float) -> None:
        state = self.states[provider_id]
        state.successes += 1
        state.total_latency_ms += latency_ms
        state.last_error = None

    def record_failure(self, provider_id: str, error: str, cooldown_seconds: int = 15) -> None:
        state = self.states[provider_id]
        state.failures += 1
        state.last_error = error[:500]
        state.disabled_until = time.time() + cooldown_seconds

    def invoke_openai_compatible(
        self,
        provider: dict[str, Any],
        *,
        model: str,
        messages: list[dict[str, Any]],
        timeout: int = 60,
    ) -> dict[str, Any]:
        endpoint = provider["endpoint"].rstrip("/") + "/chat/completions"
        env_name = provider.get("api_key_env")
        api_key = os.getenv(env_name) if env_name else None
        if provider.get("requires_api_key", True) and not api_key:
            raise RuntimeError(f"Missing credentials for {provider['id']}: {env_name}")
        payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
        request = urllib.request.Request(endpoint, data=payload, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        if api_key:
            request.add_header("Authorization", f"Bearer {api_key}")
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.load(response)
            self.record_success(provider["id"], (time.perf_counter() - started) * 1000)
            return body
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            self.record_failure(provider["id"], str(exc))
            raise

    def complete_with_failover(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        required_capabilities: set[str] | None = None,
        policy: str = "smart",
        max_attempts: int | None = None,
    ) -> tuple[dict[str, Any], str, list[dict[str, str]]]:
        required_capabilities = required_capabilities or {"chat"}
        excluded: set[str] = set()
        failures: list[dict[str, str]] = []
        attempts = 0
        limit = max_attempts or len(self.providers)
        while attempts < limit:
            provider = self.choose(required_capabilities, policy, excluded)
            if not provider:
                break
            excluded.add(provider["id"])
            attempts += 1
            try:
                return self.invoke_openai_compatible(provider, model=model, messages=messages), provider["id"], failures
            except Exception as exc:
                failures.append({"provider": provider["id"], "error": str(exc)[:500]})

        raise RuntimeError(json.dumps({"error": "No provider succeeded", "failures": failures}))

    def snapshot(self) -> dict[str, Any]:
        return {
            provider_id: {
                "successes": state.successes,
                "failures": state.failures,
                "success_rate": round(state.success_rate, 4),
                "avg_latency_ms": None if state.avg_latency_ms == float("inf") else round(state.avg_latency_ms, 2),
                "disabled_until": state.disabled_until,
                "last_error": state.last_error,
            }
            for provider_id, state in self.states.items()
        }
