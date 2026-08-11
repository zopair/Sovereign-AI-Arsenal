# Factory OS

## Principle

Git hosting is a source/synchronization adapter, not a production dependency.
After intake, every project receives a factory-owned workspace, execution backends, recovery policy, provenance, reports, and artifact storage.

## Runtime planes

1. **Workspace plane** — isolated project workspaces and state.
2. **Execution plane** — capability-driven local, container, hosted, self-hosted, VM, GPU, or other compatible executors.
3. **Agent plane** — planners, builders, testers, reviewers, repair agents, and release agents.
4. **Tool plane** — dynamically discovered tools/APIs selected by capability.
5. **Knowledge plane** — OSS capability registry, recipes, benchmarks, failure history, and provenance.
6. **Recovery plane** — retry, failover, alternative implementation, isolation, and approval boundaries.
7. **Verification plane** — tests, security, SBOM/provenance, reproducibility, and release gates.

## Independence rule

A loss of GitHub, GitHub Actions, a provider, an agent, or an execution backend must not terminate unrelated project work. The factory should fail over or continue independent tasks whenever safe.

## Source sync

Projects may be imported from Git hosting and synchronized back when desired. The factory workspace remains the execution source of truth during production.
