"""Celery configuration for durable repository-analysis jobs."""

from __future__ import annotations

import os

from celery import Celery


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "sovereign_ai_arsenal",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.core.repository_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=False,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=1700,
    task_time_limit=1800,
    result_expires=86400,
    task_default_queue="repository",
    task_default_delivery_mode="persistent",
    task_routes={
        "backend.repository_discovery": {"queue": "repository"},
        "backend.repository_analysis": {"queue": "repository"},
    },
    broker_transport_options={"visibility_timeout": 3600},
    result_backend_transport_options={"visibility_timeout": 3600},
    broker_connection_retry_on_startup=True,
    task_publish_retry=True,
    timezone="UTC",
    enable_utc=True,
)
