"""Bounded Celery tasks for repository discovery and analysis.

Task arguments are JSON primitives only. Repository code is never executed here.
"""

from __future__ import annotations

import asyncio
import importlib
import uuid
from pathlib import Path
from typing import Any

from .celery_app import celery_app


class InvalidTaskPayload(ValueError):
    """Raised for malformed task arguments that must not be retried."""


def _validate_discovery_payload(
    queries: list[str] | None,
    max_repos_per_query: int,
    auto_analyze: bool,
) -> None:
    if queries is not None:
        if not isinstance(queries, list) or len(queries) > 25:
            raise InvalidTaskPayload("queries must contain at most 25 items")
        if any(
            not isinstance(query, str)
            or not query.strip()
            or len(query) > 200
            for query in queries
        ):
            raise InvalidTaskPayload("each query must be a non-empty string of at most 200 characters")
    if (
        not isinstance(max_repos_per_query, int)
        or isinstance(max_repos_per_query, bool)
        or not 1 <= max_repos_per_query <= 500
    ):
        raise InvalidTaskPayload("max_repos_per_query must be between 1 and 500")
    if not isinstance(auto_analyze, bool):
        raise InvalidTaskPayload("auto_analyze must be a boolean")


def _validate_analysis_payload(repo_id: str, force_reanalyze: bool) -> None:
    if not isinstance(repo_id, str) or len(repo_id) > 64:
        raise InvalidTaskPayload("repo_id must be a UUID string")
    try:
        uuid.UUID(repo_id)
    except (ValueError, TypeError, AttributeError) as error:
        raise InvalidTaskPayload("repo_id must be a UUID string") from error
    if not isinstance(force_reanalyze, bool):
        raise InvalidTaskPayload("force_reanalyze must be a boolean")


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
    dont_autoretry_for=(InvalidTaskPayload,),
)
def discover_repositories_task(
    self,
    queries: list[str] | None,
    max_repos_per_query: int,
    auto_analyze: bool,
) -> dict[str, Any]:
    """Discover repositories using resources created inside the worker process."""
    _validate_discovery_payload(queries, max_repos_per_query, auto_analyze)
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
    dont_autoretry_for=(InvalidTaskPayload,),
)
def analyze_repository_task(self, repo_id: str, force_reanalyze: bool = False) -> None:
    """Run a single repository analysis in the dedicated worker process."""
    _validate_analysis_payload(repo_id, force_reanalyze)
    from backend.api.routes import perform_comprehensive_analysis

    _ensure_vector_store()
    return asyncio.run(perform_comprehensive_analysis(repo_id, force_reanalyze))
