from __future__ import annotations

from nilcenter.cli import main


def test_cli_creates_and_lists_experiments(tmp_path, capsys):
    store = tmp_path / "experiments.json"
    assert main([
        "experiments", "--store", str(store), "create",
        "scientific-computing", "Integration baseline",
        "--hypothesis", "Compare methods",
    ]) == 0
    created = capsys.readouterr().out
    assert "Created " in created
    assert main(["experiments", "--store", str(store), "list"]) == 0
    listed = capsys.readouterr().out
    assert "Integration baseline" in listed
    assert "scientific-computing" in listed


def test_cli_updates_experiment_status(tmp_path, capsys):
    store = tmp_path / "experiments.json"
    assert main([
        "experiments", "--store", str(store), "create",
        "scientific-computing", "Prime gaps",
    ]) == 0
    created = capsys.readouterr().out
    experiment_id = created.split()[1].rstrip(":")
    assert main([
        "experiments", "--store", str(store), "status",
        experiment_id, "planned",
    ]) == 0
    assert "planned" in capsys.readouterr().out
