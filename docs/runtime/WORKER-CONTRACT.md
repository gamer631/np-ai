# NIL Runtime Worker Contract v0.1

This contract defines the boundary between NIL job orchestration and a future
isolated execution backend. It is **not an execution engine or sandbox**.

## Request

A worker request contains UUID job/workspace identifiers, an experiment reference,
bounded resource limits, a network flag (currently rejected when enabled), and a
validated relative artifact manifest.

## Backend interface

Implementations of WorkerBackend must provide:

- launch(request): return an opaque backend handle only after isolation setup succeeds.
- poll(handle): report the backend's observed state.
- cancel(handle): request cancellation; do not report CANCELLED before the worker stops.
- collect(handle): return terminal status, bounded stdout/stderr, and validated artifact metadata.

## Fail-closed requirements for future backends

A backend must reject execution if it cannot enforce isolation, resource limits,
workspace boundaries, output caps, and network policy. No host execution fallback
is allowed. Prefer rootless container isolation with a read-only base, non-root
identity, dropped capabilities, no host mounts, no network by default, seccomp,
and explicit CPU/memory/process/time limits. These controls still require threat
model review and verification; containers alone are not a complete security boundary.

## Current implementation

The Python SDK exposes typed request/result objects and a protocol only. No worker
launches, code runs, processes are spawned, or sandbox guarantees are made.
WorkerRequest.validate() rejects network access and validates limits, IDs,
artifact paths, duplicates, and file metadata. Results are terminal-only and
output length is bounded.


## Coordinator layer

`WorkerCoordinator` joins the job registry, workspace manager, and injected backend. It validates requests, provisions a workspace, launches through the backend interface, synchronizes observed backend state, requests cancellation without claiming a stop prematurely, and permits output collection only after the job is terminal. The coordinator is tested with a stub backend; it is not a sandbox and does not ship a process-execution backend.
