# NILcenter.ai Tool and Module Contract

## Goals

Every built-in tool, external integration and laboratory module must be discoverable, versioned, auditable and usable through a consistent interface. Python is the preferred extension API; native tools remain supported through reviewed adapters.

## Required manifest fields

A module manifest must include:

- `id`: stable reverse-DNS identifier (for example `org.nilcenter.net.packet-inspector`).
- `name`, `summary`, `laboratory`.
- `version`: semantic version.
- `publisher`, `license`, `source`, `maintainer`.
- `entrypoint`: declared adapter, not an arbitrary string passed to a shell.
- `supported_platforms` and `python_requires`.
- `capabilities`: exact permissions requested.
- `risk_level`: `low`, `moderate`, `high` or `critical`.
- `inputs` and `outputs`: typed JSON-compatible schemas.
- `dependencies`: pinned or constrained dependencies with hashes in lock data.
- `tests`, `documentation`, `provenance` and `signature`.

## Python API shape

A module exposes a typed adapter implementing a documented protocol. The host validates its manifest, checks capabilities, provisions an isolated workspace and supplies a scoped context. Modules must not gain ambient access to user files, credentials, devices or the network.

Illustrative future interface:

```python
from nilcenter_sdk import ToolContext, ToolResult

def run(context: ToolContext, parameters: dict[str, object]) -> ToolResult:
    context.require_capability("workspace.read")
    # Operate only on files explicitly mounted into this workspace.
    return ToolResult.ok({"files_inspected": 0})
```

This is a target contract, not a currently executable plugin API.

## Compatibility

- Public APIs are versioned and have deprecation windows.
- Manifests are schema-validated before installation.
- Dependencies are resolved into isolated, reproducible environments.
- No module may silently modify another module's environment.
- Native binaries must declare architecture, source and checksum.
- Tools must support cancellation, timeouts and bounded resource use.

## Distribution

The future NIL Module Registry will publish signed metadata and immutable artifacts. The client verifies signatures and hashes before installation. Registry availability must not be required to use already-installed offline tools.

## Acceptance checklist

- [ ] Manifest validates against the published schema.
- [ ] License and provenance are reviewed.
- [ ] Unit and integration tests pass.
- [ ] Permission requests are minimal and explained.
- [ ] Sandbox profile and resource limits are defined.
- [ ] Documentation and examples are available.
- [ ] Security contact and maintenance owner are recorded.
- [ ] Reproducible build or artifact provenance is published.
