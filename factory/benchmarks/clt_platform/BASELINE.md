# Factory Benchmark: CLT-Platform

## Purpose

First real-world benchmark of the Application Factory against an existing project. This benchmark intentionally excludes InWork.

Repository under test: `zopair/CLT-Platform`
Branch inspected: `main`
Inspection method: direct GitHub Contents + Git Trees API; no code-search index dependency.

## Direct inspection

The repository currently contains 8 Python source files plus a short README. The recursive Git tree was complete and not truncated.

Observed structure:

- `main.py`
- `automation/refactor_engine.py`
- `core/github_client/client.py`
- `core/logging/logger.py`
- `orchestration/dispatcher.py`
- `orchestration/health_monitor.py`
- `services/hunter_ai_adapter.py`
- `services/sinc_os_adapter.py`

The README describes the repository as the Sovereign Orchestrator for the CLT ecosystem.

## Runtime baseline

A local reproduction of the exact inspected source tree was compiled with Python `compileall` and passed with exit code 0. Running `python main.py` exited 0 and printed the orchestrator banner and monitoring message.

This proves a basic Python startup path, but **does not prove production readiness**.

## Findings

### Critical / blocking for production

1. **No dependency manifest discovered**: no `requirements.txt`, `pyproject.toml`, `Pipfile`, or equivalent was present in the inspected tree. Reproducible installation is therefore not defined.
2. **No automated test suite discovered**: no test files or test configuration were present in the inspected tree.
3. **HealthMonitor is a stub**: `evaluate()` always returns score 100 / Healthy and performs no actual health, security, or technical-debt checks.
4. **Dispatcher is a stub**: `assign_task()` only prints a message and performs no task execution, queueing, acknowledgement, retry, timeout, or result handling.
5. **Both service adapters are empty shells**: `HunterAIAdapter` and `SINCOSAdapter` contain no integration behavior.
6. **RefactorEngine is a no-op**: `analyze()` always returns an empty action list and `optimized=True`.

### High-risk engineering gaps

7. `GitHubClient` constructs an Authorization header from `GITHUB_TOKEN` without validating that the credential exists. It also performs HTTP requests without timeout/status validation/error handling.
8. `main.py` instantiates `GitHubClient` and `HealthMonitor`, but does not use their outputs to drive orchestration.
9. Logging is minimal and configures global logging on every `get_logger()` call.
10. No explicit package configuration, environment contract, health endpoint, structured telemetry, artifact contract, or release pipeline was discovered.

## Factory capabilities exercised

- Direct repository discovery: PASS
- Direct recursive tree acquisition: PASS
- Source inspection without code-search index: PASS
- Local syntax/compile verification: PASS
- Basic process startup verification: PASS
- Production dependency verification: BLOCKED by missing manifest
- Automated test verification: BLOCKED by missing test suite
- Functional orchestration verification: BLOCKED by stub implementations
- Real provider integration verification: BLOCKED by empty adapters
- Health scoring verification: BLOCKED by hard-coded healthy result

## Baseline assessment

The repository is a **valid skeleton/prototype**, not a production orchestrator at the inspected commit.

The important Factory finding is not merely that CLT-Platform has gaps. The test exposed a missing Factory capability: the Factory needs a **source-truth inventory layer** that can distinguish real implementations from stubs, identify missing build/test manifests, and prevent optimistic health claims.

## Required Factory improvements discovered by this benchmark

1. Add a `source_truth`/implementation-depth detector: real | partial | stub | missing.
2. Add dependency/build-system discovery and reproducibility gate.
3. Add test-discovery gate.
4. Add stub/no-op detection for critical components.
5. Add runtime smoke-test adapter with captured stdout/stderr/exit code.
6. Add evidence-backed health scoring; reject hard-coded health claims.
7. Add benchmark report and machine-readable index generation.
8. Add repository-access fallback: Contents API -> Git Tree/API -> clone/runner when search indexing is unavailable.
9. Add a Production Readiness blocker list rather than a single optimistic score.
10. Record verified findings as reusable Factory knowledge/recipes.

## Next benchmark action

The Factory should automatically ingest this report into its repository knowledge index, then generate a remediation plan for CLT-Platform. The remediation must be performed in a separate branch/PR and re-tested by the Factory; `main` must not be modified by the benchmark itself.
