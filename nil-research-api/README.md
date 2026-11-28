# NIL Research Engine 0.3

Local FastAPI research service with SQLite persistence, dataset SHA-256 fingerprints, descriptive analysis, and safe experiment runs. No arbitrary user Python is executed.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

## Routes

- `GET /health`
- `POST /datasets` — CSV upload; returns SHA-256 content fingerprint
- `GET /datasets/{id}` — metadata, fingerprint, first 20 rows
- `POST /datasets/{id}/analyze` — descriptive statistics for numeric columns
- `POST /experiments` — create a hypothesis experiment (queued metadata)
- `GET /experiments/{id}` — experiment status
- `POST /experiments/{id}/run` — run the allowlisted descriptive-statistics method and persist results
- `GET /experiments/{id}/result` — retrieve stored result and timestamp
- `GET /experiments/{id}/report` — generate Markdown report for completed experiments
- `GET /experiments/{id}/report` — generate Markdown report for completed experiments

## Data and safety

- SQLite persistence; database path configurable via `NIL_DATABASE_PATH`.
- CSV defaults: 2 MB, 50,000 data rows, 200 columns. Set `NIL_MAX_UPLOAD_BYTES`, `NIL_MAX_ROWS`, `NIL_MAX_COLUMNS` to adjust limits.
- SHA-256 is calculated on the exact uploaded CSV bytes and returned with dataset metadata and experiment result provenance.
- Only the built-in descriptive-statistics method is runnable. Other method identifiers return 400. This is not a Python execution sandbox.
- Local development only. CORS permits the Workbench dev server at localhost/127.0.0.1:5500. Do not expose to the network without authentication, authorization, dataset isolation, request-size enforcement at the proxy, rate limits, audit trail, deployment hardening, and backup policy.

## Tests

```bash
pytest -q
```

Tests are authored but have not been run in a verified runtime in this development session.
