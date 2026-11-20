"""Fail-closed policy helpers for executing untrusted repository code."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


MANAGED_LABELS = {
    "com.zopair.application": "sovereign-ai-arsenal",
    "com.zopair.component": "sandbox",
}


def validate_clone_url(url: str, allowed_domains: set[str]) -> bool:
    """Accept only canonical HTTPS repository URLs on explicitly allowed hosts."""
    if not isinstance(url, str) or not url or len(url) > 2048:
        return False

    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if (
            parsed.scheme != "https"
            or host not in {domain.lower().rstrip(".") for domain in allowed_domains}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or parsed.query
            or parsed.fragment
        ):
            return False

        segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
        if len(segments) != 2:
            return False
        if any(segment in {".", ".."} for segment in segments):
            return False
        if segments[-1].endswith(".git"):
            segments[-1] = segments[-1][:-4]
        return all(re.fullmatch(r"[A-Za-z0-9_.-]+", segment) for segment in segments)
    except (TypeError, ValueError):
        return False


def build_container_security_options(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return mandatory gVisor controls; never downgrade to the default OCI runtime."""
    config = config or {}
    runtime = config.get("runtime", "runsc")
    if runtime != "runsc":
        raise ValueError("Untrusted repository execution requires the gVisor runsc runtime")

    memory_limit = config.get("memory_limit", "512m")
    cpu_limit = float(config.get("cpu_limit", "1.0"))
    if not re.fullmatch(r"[1-9][0-9]*[kKmMgG]?", str(memory_limit)):
        raise ValueError("Invalid sandbox memory limit")
    if not 0 < cpu_limit <= 2:
        raise ValueError("Sandbox CPU limit must be greater than 0 and at most 2")

    return {
        "runtime": "runsc",
        "network_disabled": not bool(config.get("allow_network_for_install", False)),
        "read_only": True,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "pids_limit": 128,
        "mem_limit": memory_limit,
        "nano_cpus": int(cpu_limit * 1_000_000_000),
        "user": "65532:65532",
        "tmpfs": {
            "/tmp": "rw,noexec,nosuid,size=64m",
            "/home/nonroot": "rw,nosuid,nodev,size=32m",
        },
        "environment": {
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUSERBASE": "/tmp/python-user",
            "PIP_CACHE_DIR": "/tmp/pip-cache",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTEST_ADDOPTS": "-p no:cacheprovider",
        },
        "labels": dict(MANAGED_LABELS),
    }


def managed_container_filters() -> dict[str, list[str]]:
    """Restrict cleanup to containers created by this application component."""
    return {
        "label": [
            f"{key}={value}"
            for key, value in MANAGED_LABELS.items()
        ]
    }
