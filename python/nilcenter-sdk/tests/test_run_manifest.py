"""Tests for portable run manifest validation and stable fingerprints."""
from __future__ import annotations

from uuid import uuid4

import pytest

from nilcenter.run_manifest import Dependency, RunArtifact, RunManifest


def manifest(**kwargs: object) -> RunManifest:
    return RunManifest("experiment-demo", str(uuid4()), "2026-01-01T00:00:00+00:00", **kwargs)  # type: ignore[arg-type]


def test_fingerprint_is_stable_for_sorted_dependencies_and_artifacts() -> None:
    a = manifest(dependencies=(Dependency("zlib", "1"), Dependency("numpy", "2")), inputs=(RunArtifact("input.txt", "a" * 64, 2),))
    b = manifest(dependencies=(Dependency("numpy", "2"), Dependency("zlib", "1")), inputs=(RunArtifact("input.txt", "a" * 64, 2),))
    assert a.fingerprint() == b.fingerprint()


def test_fingerprint_changes_when_configuration_changes() -> None:
    a = manifest(configuration={"precision": 4})
    b = manifest(configuration={"precision": 8})
    assert a.fingerprint() != b.fingerprint()


@pytest.mark.parametrize("path", ["../escape", "/absolute", "a/../b", "a//b", "."])
def test_artifact_path_validation(path: str) -> None:
    with pytest.raises(ValueError):
        RunArtifact(path, "b" * 64, 1).validate()


def test_hash_and_size_validation() -> None:
    with pytest.raises(ValueError):
        RunArtifact("out.bin", "not-hash", 0).validate()
    with pytest.raises(ValueError):
        RunArtifact("out.bin", "b" * 64, -1).validate()


def test_manifest_rejects_invalid_job_id() -> None:
    bad = RunManifest("experiment", "not-a-uuid", "2026-01-01T00:00:00+00:00")
    with pytest.raises(ValueError):
        bad.fingerprint()


def test_manifest_rejects_non_json_and_nan_configuration() -> None:
    with pytest.raises(ValueError):
        manifest(configuration={"not_json": object()}).validate()
    with pytest.raises(ValueError):
        manifest(configuration={"nan": float("nan")}).validate()
