from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import PurePosixPath
from typing import Any

GITHUB_API = "https://api.github.com"

SIGNALS: dict[str, tuple[str, ...]] = {
    "web": ("package.json", "vite.config", "next.config", "nuxt.config", "angular.json"),
    "mobile": ("pubspec.yaml", "android/", "ios/", "build.gradle", "settings.gradle", "capacitor.config"),
    "python": ("pyproject.toml", "requirements.txt", "poetry.lock", "uv.lock"),
    "node": ("package.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock"),
    "docker": ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml"),
    "github_actions": (".github/workflows/",),
    "database": ("supabase/", "prisma/", "drizzle/", "alembic/", "migrations/", "schema.prisma"),
    "ai": ("openai", "anthropic", "gemini", "transformers", "langchain", "llamaindex", "ollama"),
    "agents": ("agent", "autogen", "crewai", "langgraph", "mcp", "a2a"),
    "automation": ("n8n", "activepieces", "workflow", "airbyte"),
    "testing": ("tests/", "__tests__/", "playwright", "vitest", "jest", "pytest"),
    "android": ("androidmanifest.xml", "build.gradle", "gradlew", "settings.gradle", "android/"),
}


def github_get(path: str) -> Any:
    token = os.getenv("GITHUB_TOKEN")
    req = urllib.request.Request(f"{GITHUB_API}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "sovereign-ai-arsenal-factory")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def repo_identity(value: str) -> tuple[str, str]:
    value = value.strip().removeprefix("https://github.com/").strip("/")
    parts = value.split("/")
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts):
        raise ValueError("Repository must be owner/name")
    return parts[0], parts[1]


def detect_capabilities(paths: list[str], readme: str) -> list[dict[str, Any]]:
    haystack = "\n".join(paths).lower() + "\n" + readme.lower()
    result: list[dict[str, Any]] = []
    for capability, patterns in SIGNALS.items():
        evidence = [pattern for pattern in patterns if pattern.lower() in haystack]
        if evidence:
            result.append({
                "capability": capability,
                "confidence": "high" if len(evidence) >= 2 else "medium",
                "evidence": evidence[:8],
            })
    return sorted(result, key=lambda x: (x["confidence"] != "high", x["capability"]))


def inspect(owner: str, repo: str) -> dict[str, Any]:
    base = f"/repos/{owner}/{repo}"
    metadata = github_get(base)
    branch = metadata.get("default_branch") or "main"
    ref = github_get(f"{base}/git/ref/heads/{branch}")
    tree_sha = ref["object"]["sha"]
    tree = github_get(f"{base}/git/trees/{tree_sha}?recursive=1")
    paths = [item["path"] for item in tree.get("tree", [])]

    try:
        readme_obj = github_get(f"{base}/readme")
        readme = base64.b64decode(readme_obj.get("content", "")).decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, KeyError, ValueError):
        readme = ""

    license_files = [
        path for path in paths
        if PurePosixPath(path).name.lower() in {"license", "license.md", "license.txt", "copying"}
    ]
    signals = detect_capabilities(paths, readme[:50000])
    return {
        "repository": f"{owner}/{repo}",
        "default_branch": branch,
        "visibility": metadata.get("visibility"),
        "archived": metadata.get("archived"),
        "stars": metadata.get("stargazers_count"),
        "forks": metadata.get("forks_count"),
        "language": metadata.get("language"),
        "topics": metadata.get("topics", []),
        "license": (metadata.get("license") or {}).get("spdx_id"),
        "license_files": license_files,
        "path_count": len(paths),
        "capabilities": signals,
        "factory_recommendations": recommendations(signals, metadata, license_files),
    }


def recommendations(signals: list[dict[str, Any]], metadata: dict[str, Any], license_files: list[str]) -> list[str]:
    caps = {item["capability"] for item in signals}
    rec: list[str] = []
    if "github_actions" not in caps:
        rec.append("Add a CI workflow before release")
    if "testing" not in caps:
        rec.append("Create unit/integration tests and a runtime verification gate")
    if "docker" not in caps:
        rec.append("Consider a reproducible container/development environment")
    if not license_files and not metadata.get("license"):
        rec.append("Review licensing before incorporating external components")
    if "mobile" in caps or "android" in caps:
        rec.append("Require device/emulator launch verification before declaring mobile release")
    if "ai" in caps:
        rec.append("Keep AI providers behind an adapter and avoid provider lock-in")
    if "agents" in caps:
        rec.append("Add an agent safety policy and tool permission boundary")
    return rec


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m factory.manager owner/repository", file=sys.stderr)
        return 2
    try:
        owner, repo = repo_identity(sys.argv[1])
        report = inspect(owner, repo)
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "report": report}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
