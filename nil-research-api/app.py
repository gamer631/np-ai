"""NIL Research API — persistent, safe MVP for datasets and experiment metadata.

The service stores records in SQLite and never executes user-provided Python.
"""
from __future__ import annotations

import csv
import hashlib
from contextlib import contextmanager
import io
import json
import math
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

MAX_UPLOAD_BYTES = int(os.getenv("NIL_MAX_UPLOAD_BYTES", "2000000"))
MAX_ROWS = int(os.getenv("NIL_MAX_ROWS", "50000"))
MAX_COLUMNS = int(os.getenv("NIL_MAX_COLUMNS", "200"))
DB_PATH = Path(os.getenv("NIL_DATABASE_PATH", str(Path(__file__).with_name("nil_research.sqlite3"))))

app = FastAPI(title="NIL Research API", version="0.2.0")


class ExperimentInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    hypothesis: str = Field(min_length=1, max_length=2000)
    dataset_id: str
    method: str = Field(default="descriptive-statistics", max_length=80)


@contextmanager
def connect_db() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            columns_json TEXT NOT NULL,
            rows_json TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS dataset_integrity (\n            dataset_id TEXT PRIMARY KEY REFERENCES datasets(id) ON DELETE CASCADE,\n            sha256 TEXT NOT NULL\n        )""
        )\n        db.execute("""CREATE TABLE IF NOT EXISTS experiment_results (\n            experiment_id TEXT PRIMARY KEY REFERENCES experiments(id) ON DELETE CASCADE,\n            result_json TEXT NOT NULL,\n            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n        )""
        )\n        db.execute("""CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

@app.on_event("startup")
def startup() -> None:
    init_db()


@app.middleware("http")
async def restrict_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Request exceeds upload size limit")
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nil-research-api", "version": "0.2.0"}


def parse_csv_strict(raw: bytes) -> tuple[list[str], list[list[str]]]:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError("CSV exceeds the upload size limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV: {exc}") from exc
    if not rows:
        raise ValueError("CSV is empty")
    headers = [h.strip() for h in rows[0]]
    if not headers or any(not h for h in headers):
        raise ValueError("Header cells must be non-empty")
    if len(headers) > MAX_COLUMNS:
        raise ValueError(f"CSV exceeds {MAX_COLUMNS} columns")
    if len(set(headers)) != len(headers):
        raise ValueError("Column names must be unique")
    data = rows[1:]
    if len(data) > MAX_ROWS:
        raise ValueError(f"CSV exceeds {MAX_ROWS} data rows")
    if any(len(row) != len(headers) for row in data):
        raise ValueError("Every data row must match the header column count")
    return headers, data


def dataset_record(dataset_id: str) -> dict[str, Any] | None:
    with connect_db() as db:
        row = db.execute("SELECT * FROM datasets WHERE id=?", (dataset_id,)).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "columns": json.loads(row["columns_json"]), "rows": json.loads(row["rows_json"])}


@app.post("/datasets")
async def upload_dataset(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        headers, rows = parse_csv_strict(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dataset_id = str(uuid.uuid4())
    with connect_db() as db:
        db.execute("INSERT INTO datasets(id,columns_json,rows_json,row_count) VALUES(?,?,?,?)",
                   (dataset_id, json.dumps(headers), json.dumps(rows), len(rows)))\n        db.execute("INSERT INTO dataset_integrity(dataset_id,sha256) VALUES(?,?)", (dataset_id, hashlib.sha256(raw).hexdigest()))
    return {"id": dataset_id, "columns": headers, "row_count": len(rows), "sha256": hashlib.sha256(raw).hexdigest()}


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str) -> dict[str, Any]:
    dataset = dataset_record(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    with connect_db() as db:\n        integrity = db.execute("SELECT sha256 FROM dataset_integrity WHERE dataset_id=?", (dataset_id,)).fetchone()\n    return {"id": dataset["id"], "columns": dataset["columns"], "row_count": len(dataset["rows"]), "preview": dataset["rows"][:20], "sha256": integrity["sha256"] if integrity else None}


def calculate_statistics(dataset: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for index, column in enumerate(dataset["columns"]):
        values: list[float] = []
        for row in dataset["rows"]:
            cell = row[index].strip()
            if cell == "":
                continue
            try:
                value = float(cell)
            except ValueError:
                values = []
                break
            if not math.isfinite(value):
                values = []
                break
            values.append(value)
        if values:
            total = math.fsum(values)
            result[column] = {"count": len(values), "mean": total / len(values), "min": min(values), "max": max(values)}
    return result


@app.post("/datasets/{dataset_id}/analyze")
def analyze_dataset(dataset_id: str) -> dict[str, Any]:
    dataset = dataset_record(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"dataset_id": dataset_id, "numeric_columns": calculate_statistics(dataset)}


@app.post("/experiments", status_code=201)
def create_experiment(payload: ExperimentInput) -> dict[str, Any]:
    if dataset_record(payload.dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    experiment_id = str(uuid.uuid4())
    record = {"id": experiment_id, "name": payload.name.strip(), "hypothesis": payload.hypothesis.strip(),
              "dataset_id": payload.dataset_id, "method": payload.method.strip(), "status": "queued"}
    with connect_db() as db:
        db.execute("INSERT INTO experiments(id,name,hypothesis,dataset_id,method,status) VALUES(?,?,?,?,?,?)",
                   (record["id"], record["name"], record["hypothesis"], record["dataset_id"], record["method"], record["status"]))
    return record


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict[str, Any]:
    with connect_db() as db:
        row = db.execute("SELECT id,name,hypothesis,dataset_id,method,status FROM experiments WHERE id=?", (experiment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return dict(row)
@app.post("/experiments/{experiment_id}/run")
def run_experiment(experiment_id: str) -> dict[str, Any]:
    with connect_db() as db:
        experiment = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment["method"] != "descriptive-statistics":
        raise HTTPException(status_code=400, detail="Unsupported safe method")
    dataset = dataset_record(experiment["dataset_id"])
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    result = {"method": experiment["method"], "dataset_id": dataset["id"],
              "numeric_columns": calculate_statistics(dataset)}
    with connect_db() as db:
        db.execute("INSERT OR REPLACE INTO experiment_results(experiment_id,result_json) VALUES(?,?)",
                  (experiment_id, json.dumps(result, allow_nan=False)))
        db.execute("UPDATE experiments SET status='completed' WHERE id=?", (experiment_id,))
    return {"experiment_id": experiment_id, "status": "completed", "result": result}


@app.get("/experiments/{experiment_id}/result")
def get_experiment_result(experiment_id: str) -> dict[str, Any]:
    with connect_db() as db:
        row = db.execute("SELECT result_json,completed_at FROM experiment_results WHERE experiment_id=?", (experiment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Experiment result not found")
    return {"experiment_id": experiment_id, "completed_at": row["completed_at"], "result": json.loads(row["result_json"])}


