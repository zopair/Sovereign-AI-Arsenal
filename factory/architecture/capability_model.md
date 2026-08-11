# Factory Capability Model

The production path is organized around four independent concepts:

`Capability -> Agent -> Worker -> Evidence`

## Capability
A required outcome or technical ability. Examples: `python-build`, `android-build`, `dependency-repair`.

## Agent
A decision-maker selected for the capability. Agents propose plans, repairs, and tool calls; they do not own compute.

## Worker
A replaceable execution backend: VM, container, GPU worker, or GitHub Actions adapter. Worker loss must not terminate the project.

## Evidence
Every execution stage must emit verifiable evidence: state transition, worker identity, timestamps, logs, tests, artifact references, and verification status.

## Recovery rule
A failure is classified before it is retried. The recovery engine may retry, reschedule, switch worker, switch skill/agent, or repair and retest. A bounded retry/time/cost budget prevents infinite loops.

## Provider independence
GitHub Actions is an adapter/provider, not the factory runtime. The factory must remain executable through an independent worker backend.