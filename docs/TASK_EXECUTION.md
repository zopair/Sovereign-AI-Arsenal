# Repository Task Execution

## Architecture

The FastAPI API publishes JSON-only jobs to Celery. Redis is the broker and short-lived result backend. A separate worker process consumes the repository queue and writes repository records to PostgreSQL and embeddings to the shared Chroma data directory.

~~~mermaid
flowchart LR
    Client[API Client] --> API[FastAPI]
    API -->|JSON task + ID| Redis[(Redis AOF)]
    Redis --> Worker[Celery Worker]
    Worker --> GitHub[GitHub API]
    Worker --> PostgreSQL[(PostgreSQL)]
    Worker --> Chroma[(Persistent Chroma)]
    API -->|GET task ID| Redis
~~~

The worker uses the same backend image, PostgreSQL, Redis, vector-data volume, and model-cache volume as the API. It runs with concurrency 1 to avoid loading multiple embedding models and to keep writes to the local Chroma store serialized.

## API flow

- POST /api/v1/repositories/discover queues discovery and returns task_id.
- POST /api/v1/repositories/{repo_id}/analyze queues analysis and returns task_id.
- GET /api/v1/tasks/{task_id} returns PENDING, STARTED, RETRY, SUCCESS, or FAILURE (lowercase in the JSON response).

All routes remain behind the existing API-key middleware.

## Reliability settings

- JSON-only task and result serialization; pickle is not accepted.
- Redis AOF is enabled with appendfsync always, and the existing named Redis volume persists its data across container restarts.
- Late acknowledgements are enabled.
- Task exceptions use exponential backoff with jitter and at most 3 retries.
- Soft and hard task limits are 1,700 and 1,800 seconds.
- Worker prefetch is 1; worker concurrency is 1.
- Result records expire after 24 hours.
- Vector records use Chroma upsert, and daily trend snapshots are updated in place so ordinary retries do not duplicate them.
- The GitHub token is read from the worker environment; the YAML config no longer contains an unexpanded ${GITHUB_TOKEN} placeholder.

## Important limitations

This is a durable background queue for the repository discovery and analysis operations, not a general-purpose arbitrary-code executor.

Celery with Redis does not provide exactly-once execution. Task handlers must remain idempotent. Ordinary task exceptions are retried; hard worker-process loss is not guaranteed to be replayed in every failure mode because the worker is configured to avoid unbounded redelivery loops. Redis AOF improves persistence but does not replace tested backups or a highly available broker.

Task status is retained only for the configured 24-hour result window. A PENDING status can also mean the task ID is unknown or its result has expired.

The gVisor Docker sandbox module is separate and is not called by these tasks. The worker only performs GitHub API discovery and repository analysis; it does not execute repository scripts.

## Local operation

Start the stack:

~~~bash
docker compose up --build -d
docker compose ps
docker compose logs -f worker
~~~

The worker service starts automatically with the API, PostgreSQL, and Redis. No separate Celery broker, paid queue service, or Cloudflare deployment is required.

## Proof of Concept & Enterprise Customization Readiness

**Status:** Working PoC queue integration; not an exactly-once workflow engine or multi-tenant job scheduler.

Enterprise customization should add durable audit records in PostgreSQL, per-tenant quotas, cancellation, dead-letter handling, worker health monitoring, and tested disaster recovery before exposing the queue to untrusted multi-tenant clients.

## Intellectual Property & Authorship

Authored for the Zubair AI ecosystem by **Aly Hussein Zopair (علي حسين زبير ALY HUSSEIN ZOPAIR)**.
