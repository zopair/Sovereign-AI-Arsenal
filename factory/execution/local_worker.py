"""Provider-independent worker implementation used as the first non-GitHub backend."""
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .worker_protocol import JobEvidence, JobState, WorkerRecord


@dataclass
class LocalWorker:
    worker_id: str = "local-worker"
    capabilities: frozenset[str] = frozenset({"linux", "python", "ci", "isolated", "shell"})

    def record(self) -> WorkerRecord:
        return WorkerRecord(
            worker_id=self.worker_id,
            capabilities=self.capabilities,
            ready=True,
            heartbeat_at=time.time(),
        )

    def run_self_check(self) -> JobEvidence:
        started = time.time()
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
            ok = completed.returncode == 0 and completed.stdout.strip() == "factory-worker-ok"
            return JobEvidence(
                job_id="local-worker-self-check",
                state=JobState.SUCCEEDED if ok else JobState.FAILED,
                worker_id=self.worker_id,
                logs=[completed.stdout.strip(), completed.stderr.strip()],
                started_at=started,
                finished_at=time.time(),
                error_class=None if ok else "worker_self_check_failed",
            )
