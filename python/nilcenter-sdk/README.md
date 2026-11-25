# NILcenter Python SDK

The first SDK milestone provides a typed, offline-first laboratory catalog, metadata-only tool registry, CLI and tool-manifest validation.

## Install for development

```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

## Python API

```python
from nilcenter import NIL

nil = NIL()

for lab in nil.labs.list():
    print(lab.id, lab.name)

for lab in nil.labs.search("security"):
    print(lab.summary)

cyber_lab = nil.lab("cybersecurity")
print(cyber_lab.name)
```

## CLI

```bash
nilcenter labs list
nilcenter labs search security
nilcenter tools list
nilcenter tools validate ./tool-manifest.json
```

## Current limitations

- No tool installation or execution.
- No plugin auto-loading.
- No privileged operations.
- No network access required for catalog discovery.
- Tool descriptors are registered by the host application in this initial version.

These restrictions are intentional. Safe isolated execution will be implemented only after the broker, sandbox and audit contracts are ready.
