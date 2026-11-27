"""Tests for SQLite run manifest registry."""
from __future__ import annotations

from uuid import uuid4

import pytest

from nilcenter.run_manifest import RunManifest
from nilcenter.run_registry import RunRegistry


def sample(**kwargs: object) -> RunManifest:
    return RunManifest("exp-one", str(uuid4()), "2026-01-01T00:00:00+00:00", **kwargs)  # type: ignore[arg-type]


def test_roundtrip_and_idempotent_save(tmp_path) -> None:
    registry = RunRegistry(tmp_path / "runs.sqlite")
    manifest = sample(configuration={"seed": 3})
    first = registry.save(manifest)
    second = registry.save(manifest)
    assert first == second
    assert registry.get(manifest.job_id).manifest == manifest.to_dict()


def test_duplicate_job_id_with_changed_manifest_rejected(tmp_path) -> None:
    registry = RunRegistry(tmp_path / "runs.sqlite")
    job_id = str(uuid4())
    one = RunManifest("exp-one", job_id, "2026-01-01T00:00:00+00:00", configuration={"v": 1})
    two = RunManifest("exp-one", job_id, "2026-01-01T00:00:00+00:00", configuration={"v": 2})
    registry.save(one)
    with pytest.raises(ValueError):
        registry.save(two)


def test_list_filters_by_experiment_and_limit(tmp_path) -> None:
    registry = RunRegistry(tmp_path / "runs.sqlite")
    a = sample()
    b = sample()
    registry.save(a)
    registry.save(b)
    assert len(registry.list(experiment_id="exp-one")) == 2
    assert len(registry.list(limit=1)) == 1
    assert len(registry.list(experiment_id="missing")) == 0


def test_missing_record_and_invalid_limit(tmp_path) -> None:
    registry = RunRegistry(tmp_path / "runs.sqlite")
    with pytest.raises(KeyError):
        registry.get(str(uuid4()))
    with pytest.raises(ValueError):
        registry.list(limit=0)
