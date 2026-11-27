"""Local, reproducible experiment metadata storage.

This store records metadata only. It does not execute code or persist arbitrary
research datasets. The JSON file is user-owned local state, not a secure
multi-user database.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_EXPERIMENT_STATES = frozenset({"draft", "planned", "running", "succeeded", "failed", "cancelled"})


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class Experiment:
    """A traceable research experiment record."""

    id: str
    name: str
    laboratory: str
    status: str
    created_at: str
    updated_at: str
    hypothesis: str = ""
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class ExperimentStore:
    """Thread-safe, atomic JSON store for local experiment metadata."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()
        self._lock = threading.RLock()

    def _read(self) -> dict[str, Experiment]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise TypeError("Experiment store must contain a JSON array")
        records: dict[str, Experiment] = {}
        for item in payload:
            if not isinstance(item, dict):
                raise TypeError("Experiment entries must be JSON objects")
            item["tags"] = tuple(item.get("tags", ()))
            experiment = Experiment(**item)
            records[experiment.id] = experiment
        return records

    def _write(self, records: dict[str, Experiment]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(item) for item in sorted(records.values(), key=lambda x: x.created_at)]
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def create(
        self,
        name: str,
        laboratory: str,
        *,
        hypothesis: str = "",
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> Experiment:
        """Create a draft experiment after validating JSON-compatible metadata."""
        clean_name = name.strip()
        clean_lab = laboratory.strip().lower()
        if not clean_name:
            raise ValueError("Experiment name cannot be empty")
        if not clean_lab:
            raise ValueError("Laboratory identifier cannot be empty")
        safe_metadata = dict(metadata or {})
        json.dumps(safe_metadata)
        now = _now()
        experiment = Experiment(
            id=str(uuid4()),
            name=clean_name,
            laboratory=clean_lab,
            status="draft",
            created_at=now,
            updated_at=now,
            hypothesis=hypothesis.strip(),
            tags=tuple(tag.strip() for tag in tags if tag.strip()),
            metadata=safe_metadata,
        )
        with self._lock:
            records = self._read()
            records[experiment.id] = experiment
            self._write(records)
        return experiment

    def list(self, laboratory: str | None = None) -> tuple[Experiment, ...]:
        """List experiments, optionally restricted to a laboratory."""
        with self._lock:
            records = self._read()
        values = records.values()
        if laboratory is not None:
            values = (item for item in values if item.laboratory == laboratory.strip().lower())
        return tuple(sorted(values, key=lambda item: item.created_at, reverse=True))

    def get(self, experiment_id: str) -> Experiment:
        """Get one experiment by ID."""
        with self._lock:
            try:
                return self._read()[experiment_id]
            except KeyError as exc:
                raise KeyError(f"Unknown experiment: {experiment_id}") from exc

    def set_status(self, experiment_id: str, status: str) -> Experiment:
        """Update an experiment lifecycle status."""
        if status not in _EXPERIMENT_STATES:
            raise ValueError(f"Unsupported experiment status: {status}")
        with self._lock:
            records = self._read()
            try:
                current = records[experiment_id]
            except KeyError as exc:
                raise KeyError(f"Unknown experiment: {experiment_id}") from exc
            updated = Experiment(**{**asdict(current), "updated_at": _now(), "status": status})
            records[experiment_id] = updated
            self._write(records)
            return updated
