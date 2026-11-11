# Capability Discovery

The factory searches for solutions by **what they do**, not by what they are called.

## Discovery inputs

- required behavior
- interfaces (CLI/API/library/service)
- runtime requirements
- isolation model
- persistence model
- scaling model
- supported workloads
- license/security constraints
- integration cost

## Candidate vocabulary

A capability such as `isolated_job_execution` may be implemented by a runner, worker, executor, build farm, sandbox, task engine, container service, Kubernetes job controller, CI engine, or another system. Names are discovery hints only.

## Selection

Candidates are normalized into capabilities, verified against project requirements, benchmarked where possible, and registered with provenance and alternatives.
