# AI Application Factory

The Factory layer turns `Sovereign-AI-Arsenal` into a reusable application-production infrastructure.

## What it does now

- Inspects any public GitHub repository by `owner/name`.
- Detects common application capabilities from repository files.
- Builds a deterministic capability report without requiring an LLM.
- Maintains a component registry with licensing and role metadata.
- Provides GitHub Actions entry points for repeatable intake scans.
- Keeps provider integrations optional so the factory can fall back to local/open tooling.

## Architecture

```text
Request / Repository
        |
        v
   Intake Manager
        |
        +--> Repository Inspector
        +--> Capability Detector
        +--> License Guard
        +--> Component Registry
        +--> Architecture Planner (future)
        +--> Builder Agents (future)
        +--> Test / UI / APK Gates (future)
        +--> Release Agent (future)
```

## Design rules

1. Prefer open-source and self-hostable components where practical.
2. Never treat an available repository as automatically compatible: inspect its license, activity, runtime, APIs, and dependencies.
3. Never hard-code one AI provider. Providers are adapters in the registry.
4. A successful build is not a successful product. Runtime/UI verification is a release gate.
5. Every discovered tool becomes reusable knowledge in the registry, not a one-off dependency.

## Quick start

```bash
python -m factory.manager owner/repository
```

Optional environment variable:

```bash
export GITHUB_TOKEN=...
python -m factory.manager owner/repository
```

The command prints a JSON report and writes no credentials into the repository.
