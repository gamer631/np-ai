# NILcenter Python SDK

The Python SDK provides an offline-first laboratory catalog, metadata-only tool
registry, strict tool-manifest validation, local experiment metadata storage,
and an application-level capability-grant primitive.

## Install for development

```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check src tests
```

## Python API

```python
from pathlib import Path

from nilcenter import NIL, ExperimentStore

nil = NIL()

for lab in nil.labs.list():
    print(lab.id, lab.name)

for lab in nil.labs.search("security"):
    print(lab.summary)

math_lab = nil.lab("scientific-computing")
store = ExperimentStore(Path.home() / ".local/share/nilcenter/experiments.json")
experiment = store.create(
    "Numerical integration baseline",
    math_lab.id,
    hypothesis="Compare numerical integration methods",
    tags=("numerics", "baseline"),
    metadata={"seed": 42},
)
print(experiment.id, experiment.status)
```

The capability policy primitive is deny-by-default and requires explicit
approval, exact subject/capability/resource scope, a bounded expiry and
revocation. It is not an OS security boundary and does not make code execution
safe.

## CLI

```bash
nilcenter labs list
nilcenter labs search security
nilcenter tools list
nilcenter tools validate ./tool-manifest.json
nilcenter experiments create scientific-computing "Integration baseline" --hypothesis "Compare methods"
nilcenter experiments list
```

The experiment CLI stores metadata by default in
`~/.local/share/nilcenter/experiments.json`. Use the `--store` option to
select a different local path.

## Current limitations

- No tool installation or arbitrary tool execution.
- No plugin auto-loading.
- No privileged operations.
- No Linux permission enforcement or production sandbox.
- The experiment JSON store is a single-user prototype, not a multi-process
  database or encrypted research vault.
- No production desktop shell or bootable OS image is included in this SDK.

These restrictions are intentional. Untrusted execution requires a separately
reviewed OS broker, disposable sandbox, resource limits and audit implementation.

## Transactional experiment store

For a transactional local database with lifecycle event history, use
`SQLiteExperimentStore`:

```python
from pathlib import Path
from nilcenter import SQLiteExperimentStore

store = SQLiteExperimentStore(Path.home() / ".local/share/nilcenter/experiments.db")
run = store.create("Baseline", "mathematics", metadata={"seed": 42})
store.set_status(run.id, "planned")
print(store.events(run.id))
```

SQLite stores experiment metadata and lifecycle events in transactions. This is
still a local prototype; it does not encrypt data or provide tamper-proof audit.


## Runtime policy contract (validation only)

The SDK exposes `ExecutionRequest`, `ResourceLimits`, and `RuntimePolicy` as a fail-closed request validation contract for future isolated execution. Network access and capabilities are denied unless explicitly allowed by policy, and source size and resource limit values are validated. **This module does not execute code, isolate processes, enforce OS limits, or constitute a sandbox.**

