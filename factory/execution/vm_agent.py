"""Factory VM worker contract with a safe local simulator.

The simulator models a VM-backed execution worker without provisioning a real
VM. It is intentionally command-allowlisted and bounded so it can be used in
CI to validate orchestration before a real compute provider is connected.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class WorkerState(str, Enum):
    OFFLINE = "offline"
    READY = "ready"
    BUSY = "busy"
    FAILED = "failed"


@dataclass(frozen=True)
class VMProfile:
    name: str
    capabilities: frozenset[str]
    cpu: int = 2
    memory_mb: int = 4096


@dataclass
class VMWorkerAgent:
    profile: VMProfile
    state: WorkerState = WorkerState.READY
    executed: list[str] = field(default_factory=list)
    _handlers: dict[str, Callable[[dict], dict]] = field(default_factory=dict)

    def can_run(self, required: frozenset[str]) -> bool:
        return self.state == WorkerState.READY and required.issubset(self.profile.capabilities)

    def register(self, operation: str, handler: Callable[[dict], dict]) -> None:
        self._handlers[operation] = handler

    def execute(self, operation: str, payload: dict | None = None) -> dict:
        if self.state != WorkerState.READY:
            raise RuntimeError(f"worker is not ready: {self.state.value}")
        if operation not in self._handlers:
            raise LookupError(f"unsupported operation: {operation}")
        self.state = WorkerState.BUSY
        self.executed.append(operation)
        try:
            return self._handlers[operation](payload or {})
        finally:
            self.state = WorkerState.READY


def simulated_worker() -> VMWorkerAgent:
    worker = VMWorkerAgent(VMProfile("simulated-vm", frozenset({"linux", "python", "git", "isolated"})))
    worker.register("health", lambda _: {"ok": True, "worker": worker.profile.name})
    worker.register("build", lambda payload: {"ok": True, "artifact": payload.get("artifact", "unknown")})
    worker.register("test", lambda payload: {"ok": True, "suite": payload.get("suite", "default")})
    return worker
