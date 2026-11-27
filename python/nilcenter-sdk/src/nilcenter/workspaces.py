"""Local workspace primitives for research jobs.

These helpers enforce path boundaries and basic file-size limits. They are not a
sandbox: use the isolated runtime backend for executing untrusted code.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import UUID, uuid4


class WorkspaceError(ValueError):
    """Workspace operation rejected by safety checks."""


class WorkspaceManager:
    """Manage disposable per-run directories under one configured root."""

    def __init__(self, root: Path | str, *, max_file_bytes: int = 5_000_000) -> None:
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        self.root = Path(root).expanduser().resolve()
        self.max_file_bytes = max_file_bytes
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise WorkspaceError("Workspace root must be a directory")

    def create(self, run_id: str | None = None) -> Path:
        """Create a unique workspace with restrictive permissions."""
        identifier = str(uuid4()) if run_id is None else run_id
        try:
            UUID(identifier)
        except (ValueError, AttributeError) as exc:
            raise WorkspaceError("run_id must be a UUID") from exc
        target = self.root / identifier
        if target.exists() or target.is_symlink():
            raise WorkspaceError("Workspace already exists")
        target.mkdir(mode=0o700)
        target.chmod(0o700)
        return target.resolve()

    def resolve(self, run_id: str, relative_path: str) -> Path:
        """Resolve a path while rejecting traversal and symlink components."""
        try:
            UUID(run_id)
        except ValueError as exc:
            raise WorkspaceError("run_id must be a UUID") from exc
        if not relative_path or Path(relative_path).is_absolute():
            raise WorkspaceError("Path must be a non-empty relative path")
        if "\\ " in relative_path:
            raise WorkspaceError("Invalid path")
        parts = Path(relative_path).parts
        if any(part in ("", ".", "..") for part in parts):
            raise WorkspaceError("Path traversal is not allowed")
        workspace = self.root / run_id
        if not workspace.exists() or workspace.is_symlink():
            raise WorkspaceError("Workspace does not exist")
        base = workspace.resolve()
        if base.parent != self.root:
            raise WorkspaceError("Workspace escaped configured root")
        current = base
        for part in parts[:-1]:
            current = current / part
            if current.exists() and current.is_symlink():
                raise WorkspaceError("Symlink directories are not allowed")
        candidate = current / parts[-1]
        if candidate.exists() and candidate.is_symlink():
            raise WorkspaceError("Symlink files are not allowed")
        resolved = candidate.resolve(strict=False)
        if resolved != base and base not in resolved.parents:
            raise WorkspaceError("Path escaped workspace")
        return resolved

    def write_input(self, run_id: str, relative_path: str, data: bytes) -> Path:
        """Write a bounded input file; reject links and paths outside the run."""
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) > self.max_file_bytes:
            raise WorkspaceError("Input exceeds configured file-size limit")
        target = self.resolve(run_id, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Re-resolve after creating parents and re-check containment.
        target = self.resolve(run_id, relative_path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(target, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def cleanup(self, run_id: str) -> None:
        """Remove a workspace only if its resolved location is directly under root."""
        try:
            UUID(run_id)
        except ValueError as exc:
            raise WorkspaceError("run_id must be a UUID") from exc
        target = self.root / run_id
        if not target.exists() and not target.is_symlink():
            return
        if target.is_symlink():
            raise WorkspaceError("Refusing to clean a symlink workspace")
        resolved = target.resolve()
        if resolved.parent != self.root:
            raise WorkspaceError("Refusing to clean outside workspace root")
        shutil.rmtree(resolved)
