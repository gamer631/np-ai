"""Portable metadata for reproducible NIL research runs.

No host environment is inspected automatically. Callers provide only approved,
non-secret metadata and can compute a stable fingerprint for comparison.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("manifest values must be finite, JSON-compatible data") from exc


@dataclass(frozen=True, slots=True)
class Dependency:
    """Pinned or explicitly identified software dependency."""

    name: str
    version: str

    def validate(self) -> None:
        if not self.name.strip() or not self.version.strip():
            raise ValueError("dependency name and version are required")


@dataclass(frozen=True, slots=True)
class RunArtifact:
    """Content-addressed artifact descriptor."""

    path: str
    sha256: str
    size_bytes: int

    def validate(self) -> None:
        if not self.path or self.path.startswith("/") or any(p in ("", ".", "..") for p in self.path.split("/")):
            raise ValueError("artifact path must be a normalized relative path")
        if not _HASH_RE.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        if self.size_bytes < 0:
            raise ValueError("artifact size cannot be negative")


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Immutable, JSON-safe summary of inputs and runtime configuration."""

    experiment_id: str
    job_id: str
    created_at: str
    code_revision: str = ""
    runtime_name: str = ""
    runtime_version: str = ""
    random_seed: int | None = None
    dependencies: tuple[Dependency, ...] = ()
    inputs: tuple[RunArtifact, ...] = ()
    outputs: tuple[RunArtifact, ...] = ()
    configuration: dict[str, Any] | None = None
    schema_version: int = 1

    @classmethod
    def create(cls, experiment_id: str, job_id: str, **kwargs: Any) -> RunManifest:
        """Construct a manifest with a UTC timestamp."""
        return cls(experiment_id, job_id, datetime.now(UTC).isoformat(), **kwargs)

    def validate(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id is required")
        try:
            UUID(self.job_id)
        except ValueError as exc:
            raise ValueError("job_id must be a UUID") from exc
        if self.schema_version != 1:
            raise ValueError("unsupported manifest schema version")
        try:
            datetime.fromisoformat(self.created_at)
        except ValueError as exc:
            raise ValueError("created_at must be ISO-8601") from exc
        if self.random_seed is not None and self.random_seed < 0:
            raise ValueError("random_seed cannot be negative")
        for dep in self.dependencies:
            dep.validate()
        for artifact in (*self.inputs, *self.outputs):
            artifact.validate()
        if self.configuration is not None:
            _canonical_json(self.configuration)

    def to_dict(self) -> dict[str, Any]:
        """Serialize into stable JSON-compatible structure."""
        self.validate()
        return {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "job_id": self.job_id,
            "created_at": self.created_at,
            "code_revision": self.code_revision,
            "runtime_name": self.runtime_name,
            "runtime_version": self.runtime_version,
            "random_seed": self.random_seed,
            "dependencies": [{"name": d.name, "version": d.version} for d in sorted(self.dependencies, key=lambda x: (x.name, x.version))],
            "inputs": [{"path": a.path, "sha256": a.sha256, "size_bytes": a.size_bytes} for a in sorted(self.inputs, key=lambda x: x.path)],
            "outputs": [{"path": a.path, "sha256": a.sha256, "size_bytes": a.size_bytes} for a in sorted(self.outputs, key=lambda x: x.path)],
            "configuration": self.configuration or {},
        }

    def fingerprint(self) -> str:
        """Return a stable hash of experiment configuration, excluding run identity/time."""
        data = self.to_dict()
        data.pop("job_id", None)
        data.pop("created_at", None)
        return hashlib.sha256(_canonical_json(data)).hexdigest()
