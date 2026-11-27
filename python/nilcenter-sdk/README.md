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

## Safe mathematical expressions

The SDK provides a bounded expression evaluator for quick numerical work. It accepts arithmetic operators, `pi` and `e`, and a small set of math functions (`sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `exp`, `abs`, `floor`, `ceil`). It parses expressions as an AST and does not execute Python code. Expression length, AST node count, nesting, exponent magnitude, and finite results are checked.


```python
from nilcenter import calculate

print(calculate("sqrt(81) + sin(pi / 2)"))  # 10.0
```

This is a small calculator primitive, not a symbolic algebra engine or arbitrary Python execution environment.

## Statistical analysis

The SDK includes bounded descriptive statistics, Pearson correlation, simple linear regression, and equal-width histograms without third-party dependencies. Input data is limited to 100,000 values per series and histogram bins to 512.

```python
from nilcenter import describe, correlation, linear_regression, histogram

print(describe([2, 4, 6, 8]))
print(correlation([1, 2, 3], [2, 4, 6]))
print(linear_regression([1, 2, 3], [3, 5, 7]))
print(histogram([1, 2, 3, 4], bins=4))
```

These are baseline numeric utilities, not a substitute for a full scientific library.


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



## CSV datasets

Load bounded CSV text into a validated immutable table, inspect string columns, and convert numeric columns for analysis. Input is limited to 2 MB, 100,000 rows, and 256 columns; missing cells and duplicate headers are rejected.


```python
from nilcenter import DataTable, describe

table = DataTable.from_csv("time,value\\n0,1.2\\n1,2.4\\n2,3.1\\n")
print(table.columns, table.row_count)
print(describe(table.numeric_column("value")))
```
