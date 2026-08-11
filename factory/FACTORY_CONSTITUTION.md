# Factory Constitution

The AI Application Factory is a provider-neutral, open-source-first production system.

## Non-negotiable rules

1. Prefer open-source and self-hostable components when capability, license, security, and quality are acceptable.
2. Never equate public availability with license compatibility. Record license evidence before reuse.
3. Separate task intent from provider, model, runner, and framework choice.
4. Never report success without executable verification evidence.
5. All changes must be attributable to a project, agent, task, commit, and source when applicable.
6. Secrets are injected at runtime and never persisted in source, reports, recipes, or logs.
7. Agents receive least-privilege permissions and must operate inside explicit policy boundaries.
8. Prefer reversible changes, isolated branches, snapshots, and rollback paths.
9. Verified fixes become reusable recipes; unverified guesses do not become factory knowledge.
10. Provider and component changes must be observable and auditable.
11. Production-impacting operations require an explicit approval gate unless a project policy says otherwise.
12. The factory must remain useful when any single AI provider, cloud, runner, repository, or gateway is unavailable.

## Completion and recovery rules

13. A discovered problem is not a terminal project state. Classify it, isolate its impact, and attempt an appropriate recovery strategy.
14. Failure of one provider, task, component, or project node must not unnecessarily stop unrelated work. Use dependency-aware scheduling and continue independent work whenever safe.
15. Recovery may rotate strategy, agent, provider, tool, repository implementation, or compute runner. Prefer the smallest reversible change that restores progress.
16. Every recovery attempt has explicit time, cost, and retry/strategy budgets. Avoid infinite retry loops.
17. A task may enter `BLOCKED` only after its allowed recovery strategies are exhausted or a safety/approval boundary is reached. `BLOCKED` is not equivalent to `PROJECT_FAILED`.
18. Successful recovery must be verified with executable evidence before the project advances.
19. Verified recoveries become reusable recipes with evidence, scope, and success history.
20. The factory's primary responsibility is completion of the requested production outcome, not merely diagnosis of failure.

## Quality principle

A green build is necessary but not sufficient. Release evidence should include the relevant runtime, API, UI, security, license, and platform checks for the project type.
