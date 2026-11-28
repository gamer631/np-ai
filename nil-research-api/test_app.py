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


def test_local_workbench_origin_has_cors_access():
    response = client.get("/health", headers={"Origin": "http://127.0.0.1:5500"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"


def test_csv_parser_handles_quotes_and_multiline():
    headers, rows = parse_csv_strict(b'name,note\nAda,"line one\nline two"\n')
    assert headers == ["name", "note"]
    assert rows == [["Ada", "line one\nline two"]]


def test_parser_rejects_ragged_rows_and_duplicate_headers():
    with pytest.raises(ValueError, match="column count"):
        parse_csv_strict(b"a,b\n1\n")
    with pytest.raises(ValueError, match="unique"):
        parse_csv_strict(b"a,a\n1,2\n")


def test_upload_returns_sha256_and_statistics():
    raw = b"x,y,label\n1,10,a\n3,20,b\n"
    upload = client.post("/datasets", content=raw)
    assert upload.status_code == 200
    dataset_id = upload.json()["id"]
    assert len(upload.json()["sha256"]) == 64
    dataset = client.get(f"/datasets/{dataset_id}")
    assert dataset.json()["sha256"] == upload.json()["sha256"]
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


def test_experiment_run_and_result_are_persisted():
    dataset = client.post("/datasets", content=b"value\n7\n9\n").json()
    experiment = client.post("/experiments", json={
        "name": "Mean check", "hypothesis": "Values have a mean of eight",
        "dataset_id": dataset["id"]
    }).json()
    run = client.post(f"/experiments/{experiment['id']}/run")
    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["result"]["numeric_columns"]["value"]["mean"] == 8
    assert client.get(f"/experiments/{experiment['id']}").json()["status"] == "completed"
    saved = client.get(f"/experiments/{experiment['id']}/result")
    assert saved.status_code == 200
    assert saved.json()["result"]["dataset_sha256"] == dataset["sha256"]


def test_run_rejects_unknown_method():
    dataset = client.post("/datasets", content=b"x\n2\n").json()
    experiment = client.post("/experiments", json={
        "name": "Unknown method", "hypothesis": "test", "dataset_id": dataset["id"],
        "method": "execute-python"
    }).json()
    assert client.post(f"/experiments/{experiment['id']}/run").status_code == 400


def test_dataset_persists_in_sqlite():
    upload = client.post("/datasets", content=b"value\n7\n")
    dataset_id = upload.json()["id"]
    assert client.get(f"/datasets/{dataset_id}").status_code == 200
    assert client.post(f"/datasets/{dataset_id}/analyze").json()["numeric_columns"]["value"]["mean"] == 7


def test_report_requires_completed_run_and_contains_provenance():
    dataset = client.post("/datasets", content=b"measure\n2\n4\n").json()
    experiment = client.post("/experiments", json={
        "name": "Report test", "hypothesis": "Mean should be three",
        "dataset_id": dataset["id"]
    }).json()
    report_url = f"/experiments/{experiment['id']}/report"
    assert client.get(report_url).status_code == 409
    assert client.post(f"/experiments/{experiment['id']}/run").status_code == 200
    report = client.get(report_url)
    assert report.status_code == 200
    markdown = report.json()["report_markdown"]
    assert "# NIL Research Report" in markdown
    assert dataset["sha256"] in markdown
    assert "| measure | 2 | 3 | 2 | 4 |" in markdown


def test_experiment_rejects_blank_trimmed_fields():
    dataset = client.post("/datasets", content=b"x\n1\n").json()
    response = client.post("/experiments", json={
        "name": "   ", "hypothesis": "  ", "dataset_id": dataset["id"]
    })
    assert response.status_code == 422
