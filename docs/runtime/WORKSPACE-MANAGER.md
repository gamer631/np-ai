# Workspace helper: implementation notes

The SDK workspace helper provides per-run staging and cleanup for NILcenter
experiments. It is a filesystem utility, **not an execution sandbox**.

## API

```python
from nilcenter import WorkspaceManager

manager = WorkspaceManager(".nil-workspaces", max_file_bytes=5_000_000)
workspace = manager.create()  # returns a UUID-named directory
manager.write_input(workspace.name, "inputs/data.csv", b"a,b\\n1,2\\n")
manager.cleanup(workspace.name)
```

- Workspace IDs are UUIDs and duplicate IDs are rejected.
- Workspace directories use restrictive permissions where supported.
- Relative paths are checked against the workspace boundary.
- Existing symlink path components and symlink files are rejected.
- Inputs are capped by `max_file_bytes`; writes are exclusive and no-overwrite.
- Cleanup refuses a symlink workspace and verifies the workspace is directly under the configured root.

## Limitations and next gate

Filesystem checks are defense-in-depth, not a race-free isolation boundary. This helper
does not execute code, deny network access, constrain CPU/memory, or protect against
kernel/runtime vulnerabilities. Before any user-submitted code execution, the runtime
must use a separately verified isolation backend and pass integration tests for
network denial, resource limits, cancellation, descendant process cleanup, output
limits, and artifact handling. The runtime should fail closed if any control cannot
be applied. See ADR-0001.
