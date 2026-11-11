# GitHub Actions Reliability Record

## Incident

The `factory-v1` branch had failing GitHub Actions runs. The failing `Factory Intake` run had a completed `self-test` job with failure, while the intake job was correctly skipped for a push event. A separate legacy `daily-update` workflow was also failing and is not a valid dependency for the factory CI path.

## Evidence

- Factory Intake workflow run: `31456175160`, attempt 2, conclusion `failure`.
- Failed job: `self-test` (`93670301730`).
- The connector could not retrieve the job log blob, so the root cause of that historical run cannot be claimed with certainty.
- The historical workflow used `ubuntu-latest` and had no runner diagnostics.

## Remediation adopted

1. Pin the factory CI runner to `ubuntu-24.04` instead of `ubuntu-latest` to reduce image drift.
2. Add explicit runner, Python, Git, disk, and architecture diagnostics before tests.
3. Add timeouts and workflow concurrency cancellation.
4. Keep permissions least-privilege (`contents: read`).
5. Compile the factory before executing tests.
6. Execute both the factory self-test and recovery contract tests.
7. Validate the CLT benchmark records during CI.
8. Keep repository intake as a separate manually dispatched job so external repository access cannot make the local factory self-test fail.
9. Record that a workflow edit is not proof of health; only a successful observed run is evidence of recovery.
10. Classify runner/infrastructure failure separately from factory/project failure.

## Open-source / upstream reference

GitHub's open-source `actions/runner` is the reference runner implementation. GitHub's `actions/actions-runner-controller` (ARC) is the open-source Kubernetes controller for autoscaling self-hosted runners. GitHub recommends ephemeral self-hosted runners for autoscaling and ARC as the Kubernetes reference implementation.

Reference repositories:

- https://github.com/actions/runner
- https://github.com/actions/actions-runner-controller

Reference guidance:

- Use ephemeral runners for isolated jobs when self-hosting.
- Preserve runner logs externally for troubleshooting.
- Use runner groups/scale sets to control routing.
- Prefer GitHub App authentication for ARC where applicable.

## Factory rule

A GitHub Actions failure must be classified into one of:

- workflow/configuration failure
- runner/infrastructure failure
- dependency/toolchain failure
- factory test failure
- external provider failure

The factory must attempt the appropriate recovery path instead of treating every Actions failure as a project-level blocker.

## Future hardening

When compute infrastructure is available, add an ephemeral self-hosted runner pool through ARC/runner scale sets and route heavy Android/GPU/browser workloads there. Keep GitHub-hosted runners as the default control-plane CI path until the self-hosted pool is verified.

## Operational rule

Never report "GitHub Actions fixed" merely because YAML changed. The factory must observe a successful run and preserve the run identifier/result as evidence. If a hosted runner cannot execute, route eligible work to an alternative verified runner backend instead of fabricating success.
