import pytest
from fastapi.testclient import TestClient

import app as research_api
from app import app, parse_csv_strict

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(research_api, "DB_PATH", tmp_path / "test.sqlite3")
    research_api.init_db()
    with research_api.connect_db() as db:
        db.execute("DELETE FROM experiments")
        db.execute("DELETE FROM datasets")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_csv_parser_handles_quotes_and_multiline():
    headers, rows = parse_csv_strict(b'name,note\nAda,"line one\nline two"\n')
    assert headers == ["name", "note"]
    assert rows == [["Ada", "line one\nline two"]]


def test_parser_rejects_ragged_rows_and_duplicate_headers():
    with pytest.raises(ValueError, match="column count"):
        parse_csv_strict(b"a,b\n1\n")
    with pytest.raises(ValueError, match="unique"):
        parse_csv_strict(b"a,a\n1,2\n")


def test_upload_and_stats():
    upload = client.post("/datasets", content=b"x,y,label\n1,10,a\n3,20,b\n")
    assert upload.status_code == 200
    dataset_id = upload.json()["id"]
    analysis = client.post(f"/datasets/{dataset_id}/analyze").json()
    assert analysis["numeric_columns"]["x"]["mean"] == 2
    assert analysis["numeric_columns"]["y"]["max"] == 20
    assert "label" not in analysis["numeric_columns"]


def test_missing_dataset_returns_404():
    assert client.get("/datasets/missing").status_code == 404
    assert client.post("/datasets/missing/analyze").status_code == 404


def test_experiment_metadata_creation_and_retrieval():
    dataset = client.post("/datasets", content=b"x\n1\n").json()
    response = client.post("/experiments", json={
        "name": "Test run", "hypothesis": "Check x distribution",
        "dataset_id": dataset["id"]
    })
    assert response.status_code == 201
    experiment_id = response.json()["id"]
    assert response.json()["status"] == "queued"
    fetched = client.get(f"/experiments/{experiment_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Test run"


def test_dataset_persists_after_request():
    upload = client.post("/datasets", content=b"value\n7\n")
    dataset_id = upload.json()["id"]
    assert client.get(f"/datasets/{dataset_id}").status_code == 200
    # New HTTP request retrieves the dataset from SQLite, not an in-memory cache.
    assert client.post(f"/datasets/{dataset_id}/analyze").json()["numeric_columns"]["value"]["mean"] == 7
