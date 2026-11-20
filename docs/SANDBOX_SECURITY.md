# Repository Sandbox Security

## Execution boundary

The repository analyzer separates static inspection from executing repository-controlled code.

- Static file and README inspection does not require Docker or gVisor.
- Dependency installation and test execution require Docker configured with the gVisor OCI runtime `runsc`.
- The runner refuses to fall back to Docker's default `runc` runtime.
- The source checkout is mounted read-only inside the container and copied into an ephemeral tmpfs workspace.
- Host-side static scanners reject symlinks and any resolved path outside the temporary checkout, preventing repository-controlled links from exposing host files.
- Containers run as an unprivileged UID, with all Linux capabilities dropped, `no-new-privileges`, a read-only root filesystem, PID/CPU/memory limits, and an application-owned label.
- Cleanup only targets containers bearing the application and sandbox labels. It never prunes images or unrelated containers.

gVisor is an application kernel for containers, not a full virtual machine. Review its threat model and deployment guidance before using it for hostile multi-tenant workloads.

## Integration status

The Docker sandbox module is not currently wired to a public API route or a background worker. This change hardens its execution boundary but does not claim that repository test execution is live in the default Compose deployment. The durable worker integration is tracked separately; until a dedicated gVisor worker host is configured, use GitHub Actions for bounded repository CI tasks and keep the Docker sandbox disabled.

## Network policy

Network access is disabled by default. When disabled, the analyzer performs static inspection and explicitly skips dependency installation and test execution.

To enable network access for dependency installation and tests, set:

```yaml
sandbox:
  allow_network_for_install: true
```

This is an explicit trust decision, not an egress allowlist. It permits outbound network access from the gVisor container. The `allowed_domains` setting validates the initial Git clone URL only; it does not filter container egress. Do not enable this setting for unknown or adversarial repositories without a separate egress-control layer.

## Host requirements

1. Use a Linux host with Docker Engine.
2. Install and configure gVisor's `runsc` runtime using the official installation guide: https://gvisor.dev/docs/user_guide/install/
3. Verify that Docker reports `runsc` under its configured OCI runtimes.
4. Run the analyzer with a pinned, reviewed base image and resource limits.
5. If `runsc` is unavailable, execution fails closed. The static inspection features remain available.

The default Docker Compose stack does not install gVisor or mount the Docker socket into the API container. A deployment must deliberately provide a sandbox worker host and its Docker access; do not expose the host Docker socket to the public API container.

## Proof of Concept & Enterprise Customization Readiness

**Status:** Hardened PoC boundary; not a certified multi-tenant sandbox.

The runner now enforces gVisor and conservative container settings, but this does not replace a dedicated sandbox service, outbound firewall policy, workload quotas, image provenance checks, or independent security review. For higher-risk workloads, evaluate Firecracker or a managed isolated worker fleet.

## Intellectual Property & Authorship

Authored for the Zubair AI ecosystem by **Aly Hussein Zopair (علي حسين زبير ALY HUSSEIN ZOPAIR)**.
