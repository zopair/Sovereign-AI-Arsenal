# CLT-Platform Recovery Plan

## Purpose

This benchmark must measure whether the factory continues toward completion after discovering implementation gaps. A discovered defect is an input to recovery, not an automatic terminal state.

## Baseline findings

- The repository can be inspected directly through GitHub APIs without relying on code-search indexing.
- The source compiles and the entry point can execute, but several components are prototype shells/stubs.
- Health reporting, dispatch, refactoring, and adapters require executable implementations before production readiness.

## Required factory behavior

1. Record each finding with source evidence and a failure fingerprint.
2. Classify the finding as recoverable, complex, or dangerous.
3. Continue independent project work while a blocked node is being repaired.
4. Try bounded recovery strategies in order: known recipe, local repair, alternative implementation, provider/agent rotation, repository/OSS alternative, then architectural change.
5. Verify every proposed repair with executable checks.
6. Persist successful repairs as reusable recipes.
7. Re-run the benchmark after each recovery wave.
8. Mark the project blocked only when recovery budgets are exhausted or an approval boundary is reached.

## Completion criteria

CLT-Platform is considered recovered only when its critical orchestration path has executable health, dispatch, adapter, and refactoring behavior, the benchmark passes, and the evidence is reproducible.

The benchmark must report:

- recovery attempts and successful strategy;
- independent work completed during recovery;
- verification evidence;
- remaining blockers and why they could not be safely automated;
- time, cost, and intervention counts when available.
