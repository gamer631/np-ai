"""NIL Research API — safe MVP for dataset statistics and experiment metadata.

This API intentionally does not execute user-supplied code. Data is held in memory
for this prototype; restart clears datasets and experiments.
"""
from __future__ import annotations

import csv
import io
import math
import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

MAX_UPLOAD_BYTES = int(os.getenv("NIL_MAX_UPLOAD_BYTES", "2000000"))
MAX_ROWS = int(os.getenv("NIL_MAX_ROWS", "50000"))
MAX_COLUMNS = int(os.getenv("NIL_MAX_COLUMNS", "200"))

app = FastAPI(title="NIL Research API", version="0.1.0")
datasets: dict[str, dict[str, Any]] = {}
experiments: dict[str, dict[str, Any]] = {}


class ExperimentInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    hypothesis: str = Field(min_length=1, max_length=2000)
    dataset_id: str
    method: str = Field(default="descriptive-statistics", max_length=80)


@app.middleware("http")
async def restrict_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Request exceeds upload size limit")
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nil-research-api", "version": "0.1.0"}


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


@app.post("/datasets")
async def upload_dataset(request: Request) -> dict[str, Any]:
    raw = await request.body()
    try:
        headers, rows = parse_csv_strict(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dataset_id = str(uuid.uuid4())
    datasets[dataset_id] = {"id": dataset_id, "columns": headers, "rows": rows}
    return {"id": dataset_id, "columns": headers, "row_count": len(rows)}


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str) -> dict[str, Any]:
    dataset = datasets.get(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"id": dataset["id"], "columns": dataset["columns"], "row_count": len(dataset["rows"]), "preview": dataset["rows"][:20]}


@app.post("/datasets/{dataset_id}/analyze")
def analyze_dataset(dataset_id: str) -> dict[str, Any]:
    dataset = datasets.get(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
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
            if math.isfinite(value):
                values.append(value)
            else:
                values = []
                break
        if values:
            total = math.fsum(values)
            result[column] = {"count": len(values), "mean": total / len(values), "min": min(values), "max": max(values)}
    return {"dataset_id": dataset_id, "numeric_columns": result}


@app.post("/experiments", status_code=201)
def create_experiment(payload: ExperimentInput) -> dict[str, Any]:
    if payload.dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    experiment_id = str(uuid.uuid4())
    record = {
        "id": experiment_id,
        "name": payload.name.strip(),
        "hypothesis": payload.hypothesis.strip(),
        "dataset_id": payload.dataset_id,
        "method": payload.method.strip(),
        "status": "queued",
    }
    experiments[experiment_id] = record
    return record


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict[str, Any]:
    experiment = experiments.get(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment
