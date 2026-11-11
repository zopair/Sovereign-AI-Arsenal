from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

MODELS_API = "https://models.github.ai"


def github_models_catalog(limit: int = 50) -> list[dict[str, Any]]:
    """Return a normalized slice of the GitHub Models catalog.

    Authentication is read only from GITHUB_MODELS_TOKEN. No token is persisted.
    """
    token = os.getenv("GITHUB_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_MODELS_TOKEN or GITHUB_TOKEN to query the GitHub Models catalog")

    req = urllib.request.Request(f"{MODELS_API}/catalog/models")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2026-03-10")
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)

    models = data if isinstance(data, list) else data.get("models", [])
    normalized = []
    for model in models[:limit]:
        normalized.append(
            {
                "id": model.get("id"),
                "publisher": model.get("publisher"),
                "capabilities": model.get("capabilities", []),
                "input_modalities": model.get("supported_input_modalities", []),
                "output_modalities": model.get("supported_output_modalities", []),
                "rate_limit_tier": model.get("rate_limit_tier"),
                "limits": model.get("limits", {}),
            }
        )
    return normalized
