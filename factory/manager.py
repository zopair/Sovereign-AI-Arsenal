from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import quote

GITHUB_API = "https://api.github.com"
MAX_TREE_OBJECTS = 1000
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_MAX_RETRY_DELAY_SECONDS = 10.0

SIGNALS: dict[str, tuple[str, ...]] = {
    "web": ("package.json", "vite.config", "next.config", "nuxt.config", "angular.json"),
    "mobile": ("pubspec.yaml", "android/", "ios/", "build.gradle", "settings.gradle", "capacitor.config"),
    "python": ("pyproject.toml", "requirements.txt", "poetry.lock", "uv.lock"),
    "node": ("package.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock"),
    "docker": ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml"),
    "github_actions": (".github/workflows/",),
    "database": ("supabase", "prisma", "drizzle", "alembic", "migrations/", "schema.prisma"),
    "ai": ("openai", "anthropic", "gemini", "transformers", "langchain", "llamaindex", "ollama"),
    "agents": ("agent", "autogen", "crewai", "langgraph", "mcp", "a2a"),
    "automation": ("n8n", "activepieces", "workflow", "airbyte"),
    "testing": ("tests/", "__tests__/", "playwright", "vitest", "jest", "pytest"),
    "android": ("androidmanifest.xml", "build.gradle", "gradlew", "settings.gradle", "android/"),
}


class GitHubRateLimitError(RuntimeError):
    """Raised when GitHub's retry window exceeds the inspector's bounded wait budget."""


def _retry_delay(
    error: urllib.error.HTTPError,
    *,
    time_fn: Any,
) -> float | None:
    headers = error.headers or {}
    retry_after = headers.get("Retry-After")
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            pass

    reset_at = headers.get("X-RateLimit-Reset")
    remaining = headers.get("X-RateLimit-Remaining")
    if reset_at is not None and remaining == "0":
        try:
            return max(0.0, float(reset_at) - time_fn())
        except (TypeError, ValueError):
            pass
    return None


def github_get(
    path: str,
    *,
    opener: Any = None,
    sleep_fn: Any = time.sleep,
    time_fn: Any = time.time,
    max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY_SECONDS,
) -> Any:
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("GitHub API path must be an absolute API path")
    if max_attempts < 1 or max_retry_delay < 0:
        raise ValueError("GitHub retry limits are invalid")

    request = urllib.request.Request(f"{GITHUB_API}{path}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", "sovereign-ai-arsenal-factory")
    token = os.getenv("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    request_opener = opener or urllib.request.urlopen
    for attempt in range(max_attempts):
        try:
            with request_opener(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            remaining = (error.headers or {}).get("X-RateLimit-Remaining")
            retry_after = (error.headers or {}).get("Retry-After")
            retryable = error.code == 429 or (
                error.code == 403 and (remaining == "0" or retry_after is not None)
            ) or error.code >= 500
            if not retryable or attempt + 1 >= max_attempts:
                raise

            delay = _retry_delay(error, time_fn=time_fn)
            if delay is None:
                delay = min(0.25 * (2 ** attempt), 2.0)
            if delay > max_retry_delay:
                raise GitHubRateLimitError(
                    f"GitHub requested a {delay:.1f}s wait; "
                    f"the configured retry budget is {max_retry_delay:.1f}s"
                ) from error
            sleep_fn(delay)
        except urllib.error.URLError:
            if attempt + 1 >= max_attempts:
                raise
            sleep_fn(min(0.25 * (2 ** attempt), 2.0))

    raise RuntimeError("GitHub request exhausted its retry budget")


def repo_identity(value: str) -> tuple[str, str]:
    value = value.strip().removeprefix("https://github.com/").strip("/")
    if value.endswith(".git"):
        value = value[:-4]
    parts = value.split("/")
    if len(parts) != 2 or any(part in {".", ".."} for part in parts) or not all(
        re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in parts
    ):
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
    return sorted(result, key=lambda item: (item["confidence"] != "high", item["capability"]))


def _recover_tree_paths(base: str, root_tree_sha: str) -> list[str]:
    pending = deque([(root_tree_sha, "")])
    visited: set[tuple[str, str]] = set()
    paths: list[str] = []

    while pending:
        tree_sha, prefix = pending.popleft()
        visit_key = (tree_sha, prefix)
        if visit_key in visited:
            continue
        visited.add(visit_key)
        if len(visited) > MAX_TREE_OBJECTS:
            raise RuntimeError("GitHub tree recovery exceeded the directory traversal limit")

        tree = github_get(f"{base}/git/trees/{quote(tree_sha, safe='')}")
        entries = tree.get("tree")
        if not isinstance(entries, list):
            raise RuntimeError("GitHub returned an invalid directory tree")
        if tree.get("truncated") is True:
            raise RuntimeError("GitHub returned a truncated directory during fallback traversal")

        for entry in entries:
            name = entry.get("path")
            if not isinstance(name, str) or not name:
                continue
            full_path = f"{prefix}/{name}" if prefix else name
            if entry.get("type") == "blob":
                paths.append(full_path)
            elif entry.get("type") == "tree":
                child_sha = entry.get("sha")
                if not isinstance(child_sha, str) or not child_sha:
                    raise RuntimeError("GitHub returned a directory without a tree SHA")
                pending.append((child_sha, full_path))

    return sorted(paths)


def inspect(owner: str, repo: str) -> dict[str, Any]:
    owner, repo = repo_identity(f"{owner}/{repo}")
    base = f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
    metadata = github_get(base)
    branch = metadata.get("default_branch") or "main"
    ref = github_get(f"{base}/git/ref/heads/{quote(branch, safe='')}")
    commit_sha = ref["object"]["sha"]
    commit = github_get(f"{base}/git/commits/{quote(commit_sha, safe='')}")
    tree_sha = commit["tree"]["sha"]
    tree = github_get(f"{base}/git/trees/{quote(tree_sha, safe='')}?recursive=1")

    entries = tree.get("tree")
    if not isinstance(entries, list):
        raise RuntimeError("GitHub repository tree is unavailable")

    recovered_from_truncation = tree.get("truncated") is True
    if recovered_from_truncation:
        root_tree_sha = tree.get("sha") or tree_sha
        paths = _recover_tree_paths(base, root_tree_sha)
    else:
        paths = [
            item["path"]
            for item in entries
            if item.get("type") == "blob" and isinstance(item.get("path"), str)
        ]

    try:
        readme_obj = github_get(f"{base}/readme")
        readme_content = readme_obj.get("content", "")
        readme = base64.b64decode(readme_content).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        readme = ""
    except (KeyError, TypeError, ValueError):
        readme = ""

    license_files = [
        path for path in paths
        if PurePosixPath(path).name.lower()
        in {"license", "license.md", "license.txt", "copying"}
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
        "tree_truncated": False,
        "tree_recovered_from_truncation": recovered_from_truncation,
        "capabilities": signals,
        "factory_recommendations": recommendations(signals, metadata, license_files),
    }


def recommendations(
    signals: list[dict[str, Any]],
    metadata: dict[str, Any],
    license_files: list[str],
) -> list[str]:
    capabilities = {item["capability"] for item in signals}
    result: list[str] = []
    if "github_actions" not in capabilities:
        result.append("Add a CI workflow before release")
    if "testing" not in capabilities:
        result.append("Create unit/integration tests and a runtime verification gate")
    if "docker" not in capabilities:
        result.append("Consider a reproducible container/development environment")
    if not license_files and not metadata.get("license"):
        result.append("Review licensing before incorporating external components")
    if "mobile" in capabilities or "android" in capabilities:
        result.append("Require device/emulator launch verification before declaring mobile release")
    if "ai" in capabilities:
        result.append("Keep AI providers behind an adapter and avoid provider lock-in")
    if "agents" in capabilities:
        result.append("Add an agent safety policy and tool permission boundary")
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m factory.manager owner/repository", file=sys.stderr)
        return 2
    try:
        owner, repo = repo_identity(sys.argv[1])
        report = inspect(owner, repo)
    except (
        ValueError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        KeyError,
        RuntimeError,
    ) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "report": report}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
