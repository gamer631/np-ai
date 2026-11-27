"""Content-addressed local artifact storage for NIL research runs."""
from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    """Metadata for an immutable content-addressed artifact."""

    sha256: str
    size_bytes: int
    created_at: str

    @property
    def id(self) -> str:
        return self.sha256


class ArtifactStore:
    """Bounded local artifact store with atomic blob writes and SQLite metadata.

    This is a local single-host storage primitive, not a multi-tenant cloud service.
    """

    def __init__(self, root: Path | str, *, max_bytes: int = 20_000_000) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.root = Path(root).expanduser().absolute()
        self.max_bytes = max_bytes
        self.blobs = self.root / "blobs"
        self.metadata_path = self.root / "artifacts.sqlite3"
        self._lock = RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs.mkdir(exist_ok=True)
        if self.root.is_symlink() or self.blobs.is_symlink():
            raise ValueError("artifact store directories must not be symlinks")
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.metadata_path, timeout=10)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS artifacts (
                sha256 TEXT PRIMARY KEY,
                size_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )""")

    def _blob_path(self, digest: str) -> Path:
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("invalid SHA-256 identifier")
        return self.blobs / digest[:2] / digest[2:]

    def put(self, data: bytes) -> StoredArtifact:
        """Atomically store bytes and return digest metadata."""
        if not isinstance(data, bytes):
            raise TypeError("artifact content must be bytes")
        if len(data) > self.max_bytes:
            raise ValueError("artifact exceeds store size limit")
        digest = hashlib.sha256(data).hexdigest()
        path = self._blob_path(digest)
        with self._lock:
            path.parent.mkdir(exist_ok=True)
            if path.parent.is_symlink():
                raise ValueError("blob shard must not be a symlink")
            if not path.exists():
                fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temp_name, path)
                finally:
                    if os.path.exists(temp_name):
                        os.unlink(temp_name)
            now = datetime.now(UTC).isoformat()
            with self._connect() as db:
                db.execute("INSERT OR IGNORE INTO artifacts (sha256,size_bytes,created_at) VALUES(?,?,?)", (digest,len(data),now))
                row=db.execute("SELECT sha256,size_bytes,created_at FROM artifacts WHERE sha256=?", (digest,)).fetchone()
            if row is None or row[1] != len(data):
                raise IOError("artifact metadata integrity check failed")
            return StoredArtifact(row[0],row[1],row[2])

    def get(self, digest: str) -> bytes:
        """Load and hash-verify content; raise KeyError for missing blobs."""
        path = self._blob_path(digest)
        with self._lock:
            with self._connect() as db:
                row = db.execute("SELECT size_bytes FROM artifacts WHERE sha256=?", (digest,)).fetchone()
            if row is None:
                raise KeyError(digest)
            if path.is_symlink() or not path.is_file():
                raise IOError("artifact blob is missing or unsafe")
            if path.stat().st_size != row[0] or row[0] > self.max_bytes:
                raise IOError("artifact size metadata mismatch")
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise IOError("artifact content hash mismatch")
            return data

    def metadata(self, digest: str) -> StoredArtifact:
        """Return metadata for a digest or raise KeyError."""
        self._blob_path(digest)
        with self._connect() as db:
            row = db.execute("SELECT sha256,size_bytes,created_at FROM artifacts WHERE sha256=?", (digest,)).fetchone()
        if row is None:
            raise KeyError(digest)
        return StoredArtifact(row[0], row[1], row[2])

    def delete(self, digest: str) -> bool:
        """Delete one blob and metadata; returns false when absent."""
        path = self._blob_path(digest)
        with self._lock:
            with self._connect() as db:
                row = db.execute("SELECT sha256 FROM artifacts WHERE sha256=?", (digest,)).fetchone()
                if row is None:
                    return False
                if path.is_symlink():
                    raise IOError("refusing to delete symlink blob")
                db.execute("DELETE FROM artifacts WHERE sha256=?", (digest,))
            if path.exists():
                path.unlink()
            try:
                path.parent.rmdir()
            except OSError:
                pass
            return True
