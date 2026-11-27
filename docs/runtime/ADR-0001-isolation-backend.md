# ADR-0001: Isolated experiment execution backend

- Status: Proposed
- Date: 2026-11-27
- Scope: Experiment Runtime v0.1

## Context

NILcenter's runtime request policy validates requests but does not isolate or execute code. Running user-supplied Python in the API process, a plain subprocess, or a container with default privileges is not an acceptable security boundary.

## Decision

Prototype a container-backed worker for development, with a narrowly configured rootless container engine (Podman rootless preferred; Docker rootless acceptable if the required controls are verified). The worker must not start if the backend is unavailable or if any required security setting cannot be applied.

Containers share the host kernel and are not equivalent to microVM isolation. This prototype is for controlled, single-host research and must not be presented as production multi-tenant sandboxing. A future higher-assurance deployment should evaluate a microVM boundary (e.g. Firecracker) or a sandboxed kernel (e.g. gVisor) and undergo independent review.

## Required worker profile

- Non-root UID/GID inside the container; rootless engine.
- No network namespace connectivity (backend's network-none setting).
- Read-only root filesystem.
- Explicitly bounded writable workspace/tmpfs only.
- Drop all Linux capabilities; enable no-new-privileges.
- No host socket mounts, host home, repository checkout, secrets, or environment passthrough.
- CPU quota, memory limit, PID limit, wall-clock timeout, and output-byte limits.
- Resource limits must be verified by integration tests against the actual backend; unsupported controls fail closed.
- Image pinned by digest; no package installation during execution.
- Input/output transferred only through manifest-approved files.
- Worker and all descendants terminated on timeout/cancel; workspace cleanup is best-effort and logged.
- Audit record for request, policy, backend/image identity, start/end times, result, exit code, resource usage when available, and artifact digests.

## Threat model

### In scope
- Malicious or malformed Python submitted by a researcher.
- Attempts to escape workspace, access host files, inherit secrets, open network connections, spawn excess processes, exhaust memory/CPU, or produce oversized outputs.
- Worker crash, timeout, cancellation, invalid policy and setup failures.

### Out of scope for v0.1
- Defending against kernel/container runtime vulnerabilities.
- Production multi-tenant hosting or hostile workloads at scale.
- Privileged execution, network-enabled code, arbitrary package installation, persistent user state.
- Guarantees against side-channel attacks.

## Fail-closed conditions

Reject before execution if the backend is unavailable, image digest is not pinned, any mandatory security option is unsupported, workspace is invalid, limits are missing/out of range, or capability policy denies the request. Never silently fall back to local execution.

## Verification gates

- Integration tests verify network denial, read-only rootfs, workspace-only mounts, UID, capability drop, no-new-privileges, CPU/memory/PID limits, timeout/cancel behavior and artifact/output caps.
- Tests document which controls are asserted by backend configuration versus measured/observed at runtime.
- Security review before enabling execution from any public-facing service.

## Alternatives

- Plain subprocess: rejected; no meaningful filesystem/network/credential isolation.
- Docker/Podman default profile: rejected; default settings alone are insufficient.
- MicroVM: stronger isolation potential but deferred due operational complexity for the initial prototype.
- gVisor: candidate for a later hardened profile after compatibility and performance evaluation.
