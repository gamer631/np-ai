from fastapi.testclient import TestClient

from app import app, datasets, experiments, parse_csv_strict

client = TestClient(app)


def setup_function():
    datasets.clear()
    experiments.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_csv_parser_handles_quotes_and_multiline():
    headers, rows = parse_csv_strict(b'name,note\nAda,"line one\nline two"\n')
    assert headers == ["name", "note"]
    assert rows == [["Ada", "line one\nline two"]]


def test_parser_rejects_ragged_rows_and_duplicate_headers():
    try:
        parse_csv_strict(b"a,b\n1\n")
        assert False, "expected malformed row to fail"
    except ValueError as exc:
        assert "column count" in str(exc)
    try:
        parse_csv_strict(b"a,a\n1,2\n")
        assert False, "expected duplicate header to fail"
    except ValueError as exc:
        assert "unique" in str(exc)


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


def test_experiment_metadata_creation():
    dataset = client.post("/datasets", content=b"x\n1\n").json()
    response = client.post("/experiments", json={
        "name": "Test run", "hypothesis": "Check x distribution",
        "dataset_id": dataset["id"]
    })
    assert response.status_code == 201
    assert response.json()["status"] == "queued"
