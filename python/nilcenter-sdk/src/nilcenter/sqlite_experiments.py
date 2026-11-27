"""SQLite experiment repository with transactional event history."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_STATES = frozenset({"draft", "planned", "running", "succeeded", "failed", "cancelled"})


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    id: str
    name: str
    laboratory: str
    status: str
    created_at: str
    updated_at: str
    hypothesis: str
    tags: tuple[str, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExperimentEvent:
    id: int
    experiment_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]


class SQLiteExperimentStore:
    """Transactional SQLite store; records lifecycle changes as append-only events."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARYPRIMARY KEY,
                    name TEXT NOT NULL,
                    laboratory TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    hypothesis TEXT NOT NULL DEFAULT '',
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS experiment_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL REFERENCES experiments(id),
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS experiment_events_by_id
                    ON experiment_events(experiment_id, id);
            """)

    @staticmethod
    def _record(row: sqlite3.Row) -> ExperimentRecord:
        return ExperimentRecord(
            id=row["id"], name=row["name"], laboratory=row["laboratory"],
            status=row["status"], created_at=row["created_at"],
            updated_at=row["updated_at"], hypothesis=row["hypothesis"],
            tags=tuple(json.loads(row["tags_json"])),
            metadata=json.loads(row["metadata_json"]),
        )

    def create(self, name: str, laboratory: str, *, hypothesis: str = "",
                tags: tuple[str, ...] = (), metadata: dict[str, Any] | None = None) -> ExperimentRecord:
        name, laboratory = name.strip(), laboratory.strip().lower()
        if not name or not laboratory:
            raise ValueError("Experiment name and laboratory are required")
        metadata_json = json.dumps(metadata or {}, sort_keys=True)
        tags_json = json.dumps([tag.strip() for tag in tags if tag.strip()])
        now, experiment_id = _timestamp(), str(uuid4())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """INSERT INTO experiments
                (id,name,laboratory,status,created_at,updated_at,hypothesis,tags_json,metadata_json)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (experiment_id,name,laboratory,"draft",now,now,hypothesis.strip(),tags_json,metadata_json),
            )
            db.execute(
                "INSERT INTO experiment_events(experiment_id,event_type,occurred_at,payload_json) VALUES(?,?,?,?)",
                (experiment_id,"created",now,json.dumps({"status":"draft"})),
            )
            row = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        return self._record(row)

    def list(self, laboratory: str | None = None) -> tuple[ExperimentRecord, ...]:
        with self._connect() as db:
            if laboratory is None:
                rows = db.execute("SELECT * FROM experiments ORDER BY created_at DESC").fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM experiments WHERE laboratory=? ORDER BY created_at DESC",
                    (laboratory.strip().lower(),),
                ).fetchall()
        return tuple(self._record(row) for row in rows)

    def get(self, experiment_id: str) -> ExperimentRecord:
        with self._connect() as db:
            row = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown experiment: {experiment_id}")
        return self._record(row)

    def set_status(self, experiment_id: str, status: str) -> ExperimentRecord:
        if status not in _STATES:
            raise ValueError(f"Unsupported status: {status}")
        now = _timestamp()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM experiments WHERE id=?", (experiment_id,)).fetchone()
            if row is None:
                raise KeyError(f"Unknown experiment: {experiment_id}")
            old_status = row["status"]
            db.execute("UPDATE experiments SET status=?,updated_at=? WHERE id=?",
                       (status,now,experiment_id))
            db.execute(
                "INSERT INTO experiment_events(experiment_id,event_type,occurred_at,payload_json) VALUES(?,?,?,?)",
                (experiment_id,"status_changed",now,json.dumps({"from":old_status,"to":status})),
            )
            updated = db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        return self._record(updated)

    def events(self, experiment_id: str) -> tuple[ExperimentEvent, ...]:
        # Verify existence to avoid returning an ambiguous empty result.
        self.get(experiment_id)
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM experiment_events WHERE experiment_id=? ORDER BY id",
                (experiment_id,),
            ).fetchall()
        return tuple(ExperimentEvent(
            id=row["id"], experiment_id=row["experiment_id"],
            event_type=row["event_type"], occurred_at=row["occurred_at"],
            payload=json.loads(row["payload_json"]),
        ) for row in rows)
