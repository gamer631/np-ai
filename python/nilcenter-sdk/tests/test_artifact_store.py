"""Tests for local content-addressed artifact storage."""
from __future__ import annotations

import hashlib

import pytest

from nilcenter.artifact_store import ArtifactStore


def test_put_get_and_metadata(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    content = b"scientific output"
    item = store.put(content)
    assert item.sha256 == hashlib.sha256(content).hexdigest()
    assert item.size_bytes == len(content)
    assert store.get(item.sha256) == content
    assert store.metadata(item.sha256) == item


def test_deduplicates_identical_content(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    first = store.put(b"same")
    second = store.put(b"same")
    assert first.sha256 == second.sha256
    assert first.created_at == second.created_at


def test_size_limit_and_type_validation(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store", max_bytes=3)
    with pytest.raises(ValueError):
        store.put(b"four")
    with pytest.raises(TypeError):
        store.put("text")  # type: ignore[arg-type]


def test_missing_blob_and_invalid_hash(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    with pytest.raises(KeyError):
        store.get("a" * 64)
    with pytest.raises(ValueError):
        store.get("../bad")


def test_delete_and_missing_delete(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    item = store.put(b"to delete")
    assert store.delete(item.sha256)
    with pytest.raises(KeyError):
        store.get(item.sha256)
    assert not store.delete(item.sha256)


def test_detects_blob_corruption(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    item = store.put(b"valid")
    blob = store._blob_path(item.sha256)
    blob.write_bytes(b"evil")
    with pytest.raises(IOError):
        store.get(item.sha256)
