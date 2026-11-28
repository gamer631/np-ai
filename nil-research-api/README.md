# NIL Research API (MVP)

Small FastAPI service for local dataset upload, descriptive statistics, and experiment metadata. **No arbitrary Python execution is provided.**

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. Upload raw CSV bytes to `POST /datasets`; the response gives a dataset ID. Then call `POST /datasets/{id}/analyze`.

## Tests

```bash
pytest -q
```

## Current limits

- Prototype memory storage: data disappears when the service restarts.
- CSV only; UTF-8; up to 2 MB, 50,000 rows, and 200 columns by default.
- Statistics skip missing values and report numeric columns only.
- Experiments are metadata records; no scientific execution/worker queue yet.
- This MVP is intended for localhost use, not public deployment. Add authentication, persistent storage, rate limiting, audit logs, and deployment controls before exposing it to a network.
