from __future__ import annotations

import json

import pytest

from nilcenter.experiments import ExperimentStore


def test_create_and_reload_experiment(tmp_path):
    path = tmp_path / "state" / "experiments.json"
    store = ExperimentStore(path)
    created = store.create(
        "Prime distribution",
        "mathematics",
        hypothesis="Explore prime gaps",
        tags=("number-theory",),
        metadata={"seed": 42},
    )
    reloaded = ExperimentStore(path)
    assert reloaded.get(created.id).name == "Prime distribution"
    assert reloaded.get(created.id).metadata == {"seed": 42}
    assert reloaded.get(created.id).tags == ("number-theory",)


def test_status_transition_is_persisted(tmp_path):
    store = ExperimentStore(tmp_path / "experiments.json")
    created = store.create("Model baseline", "ai-ml")
    updated = store.set_status(created.id, "succeeded")
    assert updated.status == "succeeded"
    assert store.get(created.id).status == "succeeded"


def test_invalid_metadata_is_rejected_before_write(tmp_path):
    path = tmp_path / "experiments.json"
    store = ExperimentStore(path)
    with pytest.raises(TypeError):
        store.create("Bad metadata", "mathematics", metadata={"bad": object()})
    assert not path.exists()


def test_empty_name_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        ExperimentStore(tmp_path / "experiments.json").create(" ", "mathematics")


def test_corrupt_store_is_not_silently_overwritten(tmp_path):
    path = tmp_path / "experiments.json"
    path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    with pytest.raises(TypeError):
        ExperimentStore(path).create("New", "mathematics")
    assert json.loads(path.read_text(encoding="utf-8")) == {"not": "a list"}
