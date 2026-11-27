from __future__ import annotations

from uuid import uuid4

import pytest

from nilcenter.workspaces import WorkspaceError, WorkspaceManager


def test_create_and_write_input(tmp_path):
    manager = WorkspaceManager(tmp_path / "work")
    run_id = str(uuid4())
    workspace = manager.create(run_id)
    assert workspace.is_dir()
    assert manager.write_input(run_id, "inputs/data.txt", b"hello").read_bytes() == b"hello"


def test_rejects_traversal(tmp_path):
    manager = WorkspaceManager(tmp_path / "work")
    run_id = str(uuid4())
    manager.create(run_id)
    with pytest.raises(WorkspaceError):
        manager.resolve(run_id, "../escape.txt")


def test_rejects_absolute_path(tmp_path):
    manager = WorkspaceManager(tmp_path / "work")
    run_id = str(uuid4())
    manager.create(run_id)
    with pytest.raises(WorkspaceError):
        manager.resolve(run_id, str(tmp_path / "outside"))


def test_rejects_over_limit_file(tmp_path):
    manager = WorkspaceManager(tmp_path / "work", max_file_bytes=4)
    run_id = str(uuid4())
    manager.create(run_id)
    with pytest.raises(WorkspaceError):
        manager.write_input(run_id, "large.bin", b"12345")


def test_duplicate_run_id_rejected(tmp_path):
    manager = WorkspaceManager(tmp_path / "work")
    run_id = str(uuid4())
    manager.create(run_id)
    with pytest.raises(WorkspaceError):
        manager.create(run_id)


def test_cleanup_removes_workspace(tmp_path):
    manager = WorkspaceManager(tmp_path / "work")
    run_id = str(uuid4())
    workspace = manager.create(run_id)
    manager.write_input(run_id, "data.txt", b"data")
    manager.cleanup(run_id)
    assert not workspace.exists()
