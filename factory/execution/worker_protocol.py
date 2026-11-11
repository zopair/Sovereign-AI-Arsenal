"""Provider-neutral execution protocol for factory workers."""
from dataclasses import dataclass, field
from enum import Enum
from time import time


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class JobEvidence:
    job_id: str
    state: JobState
    worker_id: str | None = None
    logs: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    error_class: str | None = None
    started_at: float | None = None
    finished_at: float | None = None

    def has_execution_evidence(self) -> bool:
        return self.started_at is not None or bool(self.logs) or self.worker_id is not None


@dataclass(frozen=True)
class WorkerRecord:
    worker_id: str
    capabilities: frozenset[str]
    ready: bool = True
    heartbeat_at: float = 0.0


class ExecutionBroker:
    def __init__(self, heartbeat_timeout: float = 90.0):
        self.heartbeat_timeout = heartbeat_timeout
        self.workers: dict[str, WorkerRecord] = {}

    def register(self, worker: WorkerRecord) -> None:
        self.workers[worker.worker_id] = worker

    def healthy(self, worker: WorkerRecord, now: float | None = None) -> bool:
        now = time() if now is None else now
        return worker.ready and (worker.heartbeat_at == 0 or now - worker.heartbeat_at <= self.heartbeat_timeout)

    def select(self, required: frozenset[str], now: float | None = None) -> WorkerRecord:
        candidates = [w for w in self.workers.values() if self.healthy(w, now) and required.issubset(w.capabilities)]
        if not candidates:
            raise LookupError("no healthy worker satisfies required capabilities")
        return candidates[0]
