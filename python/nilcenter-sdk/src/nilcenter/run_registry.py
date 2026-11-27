"""SQLite persistence for validated reproducibility run manifests."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nilcenter.run_manifest import RunManifest


@dataclass(frozen=True, slots=True)
class RunRecord:
    """Persisted manifest snapshot keyed by its job UUID."""

    job_id: str
    experiment_id: str
    fingerprint: str
    created_at: str
    manifest: dict[str, Any]


class RunRegistry:
    """Persist immutable manifest snapshots and query them by experiment/job.

    The job ID is the primary key; saving a different manifest for an existing
    job is rejected rather than silently overwriting provenance.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS run_manifests (
                job_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL,
                manifest_json TEXT NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS run_manifests_by_experiment "
                       "ON run_manifests(experiment_id, created_at)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @staticmethod
    def _record(row: tuple[Any, ...]) -> RunRecord:
        return RunRecord(row[0], row[1], row[2], row[3], json.loads(row[4]))

    def save(self, manifest: RunManifest) -> RunRecord:
        """Validate and save; identical duplicate writes are idempotent."""
        data = manifest.to_dict()
        fingerprint = manifest.fingerprint()
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT fingerprint, manifest_json FROM run_manifests WHERE job_id=?",
                             (manifest.job_id,)).fetchone()
            if row:
                if row[0] != fingerprint or row[1] != encoded:
                    raise ValueError("job_id already exists with different run metadata")
                existing = db.execute("SELECT job_id,experiment_id,fingerprint,created_at,manifest_json "
                                     "FROM run_manifests WHERE job_id=?", (manifest.job_id,)).fetchone()
                return self._record(existing)
            db.execute("INSERT INTO run_manifests VALUES(?,?,?,?,?)",
                      (manifest.job_id, manifest.experiment_id, fingerprint, manifest.created_at, encoded))
            row = db.execute("SELECT job_id,experiment_id,fingerprint,created_at,manifest_json "
                             "FROM run_manifests WHERE job_id=?", (manifest.job_id,)).fetchone()
        if row is None:
            raise RuntimeError("manifest persistence failed")
        return self._record(row)

    def get(self, job_id: str) -> RunRecord:
        """Retrieve a manifest snapshot by job ID."""
        with self._connect() as db:
            row = db.execute("SELECT job_id,experiment_id,fingerprint,created_at,manifest_json "
                             "FROM run_manifests WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._record(row)

    def list(self, *, experiment_id: str | None = None, limit: int = 100) -> tuple[RunRecord, ...]:
        """List records newest-first, optionally filtered by experiment."""
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with self._connect() as db:
            if experiment_id is None:
                rows = db.execute("SELECT job_id,experiment_id,fingerprint,created_at,manifest_json "
                                  "FROM run_manifests ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = db.execute("SELECT job_id,experiment_id,fingerprint,created_at,manifest_json "
                                  "FROM run_manifests WHERE experiment_id=? ORDER BY created_at DESC LIMIT ?",
                                  (experiment_id, limit)).fetchall()
        return tuple(self._record(row) for row in rows)
