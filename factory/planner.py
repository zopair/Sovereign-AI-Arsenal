from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "registry" / "components.json"

ROLE_BY_CAPABILITY = {
    "ai": ("llm", "local-inference", "api"),
    "agents": ("agents", "orchestration"),
    "database": ("database", "backend"),
    "automation": ("automation", "workflow"),
    "mobile": ("mobile", "ui"),
    "android": ("mobile", "release"),
    "web": ("ui",),
}


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def plan(capabilities: list[str]) -> dict[str, Any]:
    registry = load_registry()["components"]
    chosen: list[dict[str, Any]] = []
    for capability in capabilities:
        desired = set(ROLE_BY_CAPABILITY.get(capability, ()))
        candidates = []
        for component in registry:
            roles = set(component.get("role", []))
            score = len(desired & roles)
            if score:
                candidates.append((score, component))
        candidates.sort(key=lambda item: (-item[0], item[1]["id"]))
        if candidates:
            score, component = candidates[0]
            chosen.append({
                "capability": capability,
                "component": component["id"],
                "repository": component["repository"],
                "license": component["license"],
                "score": score,
            })
    return {
        "capabilities": capabilities,
        "selected": chosen,
        "selection_policy": [
            "role_match",
            "license_visibility",
            "provider_neutrality",
            "replaceability",
        ],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plan an initial stack from factory capabilities")
    parser.add_argument("capabilities", nargs="+", help="capabilities such as web ai database agents")
    args = parser.parse_args()
    print(json.dumps(plan(args.capabilities), indent=2, ensure_ascii=False))
