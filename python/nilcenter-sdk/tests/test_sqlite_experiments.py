from __future__ import annotations

import pytest

from nilcenter.sqlite_experiments import SQLiteExperimentStore


def test_sqlite_store_persists_and_filters(tmp_path):
    store = SQLiteExperimentStore(tmp_path / "data" / "experiments.db")
    a = store.create("Run A", "math", tags=("algebra",), metadata={"seed": 7})
    store.create("Run B", "physics")
    reopened = SQLiteExperimentStore(store.path)
    assert reopened.get(a.id).metadata == {"seed": 7}
    assert reopened.list("math")[0].name == "Run A"
    assert len(reopened.list()) == 2


def test_lifecycle_events_are_append_only_records(tmp_path):
    store = SQLiteExperimentStore(tmp_path / "experiments.db")
    item = store.create("Demo", "math")
    store.set_status(item.id, "planned")
    store.set_status(item.id, "running")
    events = store.events(item.id)
    assert [e.event_type for e in events] == ["created", "status_changed", "status_changed"]
    assert events[1].payload == {"from": "draft", "to": "planned"}
    assert events[2].payload == {"from": "planned", "to": "running"}


def test_unknown_experiment_and_invalid_status_rejected(tmp_path):
    store = SQLiteExperimentStore(tmp_path / "experiments.db")
    with pytest.raises(KeyError):
        store.get("missing")
    item = store.create("Test", "math")
    with pytest.raises(ValueError):
        store.set_status(item.id, "invalid")
