"""Bounded multi-repository inventory for scheduled GitHub Actions runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from factory.manager import inspect, repo_identity

MAX_TARGETS = 25
MAX_ERROR_LENGTH = 500


def load_targets(path: Path) -> list[tuple[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not 1 <= len(payload) <= MAX_TARGETS:
        raise ValueError(f"targets must be a list containing 1-{MAX_TARGETS} repositories")

    targets: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("each target must be an object with owner and repo")
        owner, repo = repo_identity(f"{item.get('owner', '')}/{item.get('repo', '')}")
        key = f"{owner.lower()}/{repo.lower()}"
        if key in seen:
            raise ValueError(f"duplicate repository target: {owner}/{repo}")
        seen.add(key)
        targets.append((owner, repo))
    return targets


def collect_report(
    targets: list[tuple[str, str]],
    inspector: Callable[[str, str], dict[str, Any]] = inspect,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for owner, repo in targets:
        repository = f"{owner}/{repo}"
        try:
            results.append({
                "ok": True,
                "repository": repository,
                "report": inspector(owner, repo),
            })
        except Exception as error:
            results.append({
                "ok": False,
                "repository": repository,
                "error": str(error)[:MAX_ERROR_LENGTH],
            })

    succeeded = sum(1 for item in results if item["ok"])
    failed = len(results) - succeeded
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(results),
            "succeeded": succeeded,
            "failed": failed,
        },
        "results": results,
    }


def write_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        targets = load_targets(args.targets)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))

    report = collect_report(targets)
    write_report(report, args.output)
    print(json.dumps(report["summary"], ensure_ascii=False))

    return 0 if report["summary"]["succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
