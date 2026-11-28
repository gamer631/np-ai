# NIL Research API 0.2

FastAPI research service with SQLite-backed datasets and experiment metadata. The API does not execute user-supplied code.

## Local run

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Browse interactive docs at http://127.0.0.1:8000/docs.

## Routes

- `GET /health`
- `POST /datasets` — upload CSV bytes; returns dataset ID
- `GET /datasets/{id}` — metadata and first 20 rows
- `POST /datasets/{id}/analyze` — descriptive numeric statistics
- `POST /experiments` — create hypothesis/method record
- `GET /experiments/{id}` — retrieve experiment

## Persistence and limits

- SQLite database file: `nil_research.sqlite3` in this folder by default; override with `NIL_DATABASE_PATH`.
- Default limits: 2 MB CSV, 50,000 rows, 200 columns. Configure with `NIL_MAX_UPLOAD_BYTES`, `NIL_MAX_ROWS`, and `NIL_MAX_COLUMNS`.
- Numeric statistics skip blank cells. Columns with non-numeric cells are not included.
- Dataset records persist locally. Experiments reference datasets and are removed if their dataset is deleted (cascade).
- Experiments are metadata only; no background scientific execution exists yet.
- Keep this service bound to localhost. Before network exposure, implement authentication, authorization, tenant isolation, rate limiting, audit logging, secure deployment configuration, and backups.

## Tests

```bash
pytest -q
```
