# VM Worker Agent

The factory now has a worker-agent contract that can run on a VM, container, or other isolated compute host.

## Reference implementations

- `nektos/act`: local GitHub Actions execution through Docker; use as a workflow simulation reference.
- Actions Runner Controller ecosystem: runner provisioning and autoscaling patterns for Kubernetes.

## Factory contract

`VMWorkerAgent` exposes:

- capability matching
- worker lifecycle state
- bounded operation dispatch
- health/build/test operations
- deterministic simulator for CI

## Production path

1. Provision an isolated VM/container from a trusted image.
2. Bootstrap the Factory Worker Agent.
3. Register capabilities and health endpoint.
4. Register the worker with the Execution Broker.
5. Dispatch project jobs through the worker.
6. Collect artifacts/reports.
7. Tear down or recycle the worker according to policy.

The simulator intentionally does not pretend to be a real VM. A production VM provider must be connected before claiming real remote compute execution.
