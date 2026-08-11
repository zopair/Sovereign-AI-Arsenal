"""Runner-independent preflight for factory verification.

This is deliberately small and dependency-free. It gives the factory a way to
verify its own Python contracts even when GitHub-hosted execution is unavailable.
It never claims GitHub Actions succeeded; it records the backend explicitly.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path


def run() -> int:
    started = time.time()
    commands = [
        [sys.executable, "-m", "compileall", "-q", "factory"],
        [sys.executable, "-m", "factory.selftest"],
        [sys.executable, "-m", "factory.test_recovery"],
        [sys.executable, "-m", "factory.execution.test_runner_broker"],
    ]
    results = []
    for command in commands:
        completed = subprocess.run(command, text=True, capture_output=True)
        results.append({
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        })
        if completed.returncode:
            break

    report = {
        "backend": "local-preflight",
        "success": all(item["returncode"] == 0 for item in results),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "elapsed_seconds": round(time.time() - started, 3),
        "results": results,
    }
    output = Path("factory/reports/local_preflight.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
