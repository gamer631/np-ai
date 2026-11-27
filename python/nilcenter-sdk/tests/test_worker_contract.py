"""Tests for the metadata-only worker contract."""
from __future__ import annotations

from uuid import uuid4

import pytest

from nilcenter.worker_contract import ArtifactSpec, WorkerRequest, WorkerResult, WorkerStatus


def request(**kwargs: object) -> WorkerRequest:
    return WorkerRequest(job_id=str(uuid4()), experiment_id="exp-1", workspace_id=str(uuid4()), **kwargs)  # type: ignore[arg-type]


def test_request_validates_defaults() -> None:
    request().validate()


def test_request_rejects_network() -> None:
    with pytest.raises(PermissionError):
        request(network_access=True).validate()


@pytest.mark.parametrize("path", ["../escape", "/absolute", "a/../../b", "."])
def test_artifact_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(ValueError):
        ArtifactSpec(path, 1, "a" * 64).validate()


def test_artifact_size_and_hash_validation() -> None:
    with pytest.raises(ValueError):
        ArtifactSpec("output.txt", 5_000_001, "a" * 64).validate()
    with pytest.raises(ValueError):
        ArtifactSpec("output.txt", 1, "bad").validate()


def test_request_rejects_duplicate_artifacts() -> None:
    item = ArtifactSpec("out.txt", 1, "a" * 64)
    with pytest.raises(ValueError):
        request(artifacts=(item, item)).validate()


def test_result_requires_terminal_status_and_bounded_output() -> None:
    with pytest.raises(ValueError):
        WorkerResult(WorkerStatus.RUNNING).validate()
    with pytest.raises(ValueError):
        WorkerResult(WorkerStatus.SUCCEEDED, stdout="x" * 11).validate(max_output_chars=10)


def test_result_accepts_terminal_and_valid_artifact() -> None:
    WorkerResult(WorkerStatus.SUCCEEDED, exit_code=0, artifacts=(ArtifactSpec("result.csv", 4, "a" * 64),)).validate()
