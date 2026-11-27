"""Safe, backend-neutral contract for isolated NIL research workers.

This module defines data exchange and lifecycle interfaces only. It deliberately
contains no process launcher and cannot execute submitted source code.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Protocol
from uuid import UUID


class WorkerStatus(StrEnum):
    """Backend-reported worker states."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


_TERMINAL = frozenset({WorkerStatus.SUCCEEDED, WorkerStatus.FAILED, WorkerStatus.TIMED_OUT, WorkerStatus.CANCELLED})


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    """Validated relative artifact metadata; content is staged separately."""

    path: str
    size_bytes: int
    sha256: str

    def validate(self, *, max_bytes: int = 5_000_000) -> None:
        path = PurePosixPath(self.path)
        if not self.path or path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
            raise ValueError("artifact path must be a safe relative path")
        if self.size_bytes < 0 or self.size_bytes > max_bytes:
            raise ValueError("artifact size exceeds limit")
        if len(self.sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")


@dataclass(frozen=True, slots=True)
class WorkerRequest:
    """Immutable worker launch intent; a backend must apply isolation controls."""

    job_id: str
    experiment_id: str
    workspace_id: str
    artifacts: tuple[ArtifactSpec, ...] = ()
    timeout_seconds: int = 30
    memory_mb: int = 256
    cpu_seconds: int = 15
    network_access: bool = False

    def validate(self) -> None:
        for name, value in (("job_id", self.job_id), ("experiment_id", self.experiment_id), ("workspace_id", self.workspace_id)):
            if not value.strip():
                raise ValueError(f"{name} is required")
        try:
            UUID(self.job_id)
            UUID(self.workspace_id)
        except ValueError as exc:
            raise ValueError("job_id and workspace_id must be UUIDs") from exc
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be between 1 and 300")
        if not 32 <= self.memory_mb <= 4096:
            raise ValueError("memory_mb must be between 32 and 4096")
        if not 1 <= self.cpu_seconds <= 300:
            raise ValueError("cpu_seconds must be between 1 and 300")
        if self.network_access:
            raise PermissionError("network access is disabled in the worker contract")
        seen: set[str] = set()
        for artifact in self.artifacts:
            artifact.validate()
            if artifact.path in seen:
                raise ValueError("duplicate artifact path")
            seen.add(artifact.path)


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Bounded execution outcome returned by an isolated backend."""

    status: WorkerStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    artifacts: tuple[ArtifactSpec, ...] = ()

    def validate(self, *, max_output_chars: int = 100_000) -> None:
        if len(self.stdout) > max_output_chars or len(self.stderr) > max_output_chars:
            raise ValueError("worker output exceeds limit")
        if self.status not in _TERMINAL:
            raise ValueError("result must have a terminal worker status")
        for artifact in self.artifacts:
            artifact.validate()


class WorkerBackend(Protocol):
    """Interface future sandbox backends must implement.

    Implementations must not report cancellation until the worker is actually
    stopped, and must fail closed if isolation or resource limits cannot apply.
    """

    def launch(self, request: WorkerRequest) -> str:
        """Start an isolated worker and return an opaque backend handle."""
        ...

    def poll(self, handle: str) -> WorkerStatus:
        """Return current backend status."""
        ...

    def cancel(self, handle: str) -> WorkerStatus:
        """Request stop and report actual status; may remain RUNNING."""
        ...

    def collect(self, handle: str) -> WorkerResult:
        """Collect bounded output and validated artifact metadata."""
        ...
