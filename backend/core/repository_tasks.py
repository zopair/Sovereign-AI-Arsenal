"""Bounded Celery tasks for repository discovery and analysis.

Task arguments are JSON primitives only. Repository code is never executed here.
"""

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from typing import Any

from .celery_app import celery_app


def _ensure_vector_store() -> None:
    """Initialize the worker-local Chroma client and embedding model on demand."""
    module = importlib.import_module("backend.database.vector_store")
    if module.vector_store is not None:
        return

    import yaml

    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with config_path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
    module.init_vector_store(config.get("vector_store", {}))


@celery_app.task(
    bind=True,
    name="backend.repository_discovery",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def discover_repositories_task(
    self,
    queries: list[str],
    max_repos_per_query: int,
    auto_analyze: bool,
) -> dict[str, Any]:
    """Discover repositories using resources created inside the worker process."""
    from backend.api.routes import (
        discover_and_analyze_repositories,
        get_discovery_engine,
    )

    if auto_analyze:
        _ensure_vector_store()

    engine = get_discovery_engine()
    return asyncio.run(
        discover_and_analyze_repositories(
            engine,
            queries,
            max_repos_per_query,
            auto_analyze,
        )
    )


@celery_app.task(
    bind=True,
    name="backend.repository_analysis",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def analyze_repository_task(self, repo_id: str, force_reanalyze: bool = False) -> None:
    """Run a single repository analysis in the dedicated worker process."""
    from backend.api.routes import perform_comprehensive_analysis

    _ensure_vector_store()
    return asyncio.run(perform_comprehensive_analysis(repo_id, force_reanalyze))
