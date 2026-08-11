"""Provider-neutral worker implementation used as the first non-GitHub execution backend.

It intentionally executes only an allow-listed operation set. A real VM provider can
implement the same contract without changing the broker or production state machine.
"""
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile


@dataclass
class LocalWorker:
    worker_id: str = "local-worker"
    capabilities: frozenset[str] = frozenset({"linux", "python", "ci", "isolated"})

    def run_self_check(self) -> dict[str, object]:
        with tempfile.TemporaryDirectory(prefix="factory-worker-") as directory:
            root = Path(directory)
            probe = root / "probe.py"
            probe.write_text("print('factory-worker-ok')\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(probe)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            return {
                "ok": completed.returncode == 0 and completed.stdout.strip() == "factory-worker-ok",
                "worker_id": self.worker_id,
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
