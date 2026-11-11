# Factory Observability Contract

Every execution should emit structured events for:

- task accepted
- provider selected
- provider switched
- runner selected
- agent action
- tool call
- build/test result
- security result
- artifact created
- release decision
- rollback

Minimum fields: `event_id`, `timestamp`, `project`, `task_id`, `actor`, `provider`, `runner`, `action`, `status`, `duration_ms`, and `verification`.

Secrets and raw credentials must never be included.

The implementation is intentionally backend-neutral so OpenTelemetry, Prometheus, structured logs, or another OSS observability stack can be plugged in later without changing agent contracts.
