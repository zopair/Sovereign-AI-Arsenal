# Execution Broker

The factory must select execution infrastructure by **capability**, not by a repository/tool name.

A task declares requirements such as:

- `linux`
- `python`
- `android`
- `gpu`
- `isolated`
- `reproducible`
- `persistent-tooling`

The broker chooses the highest-priority healthy backend that satisfies all requirements and can produce a failover order when a backend becomes unavailable.

This intentionally leaves the concrete implementation open: GitHub-hosted Actions, self-hosted workers, containerized workers, Kubernetes/ephemeral workers, local preflight, or another compatible executor can be registered later without changing the task contract.
