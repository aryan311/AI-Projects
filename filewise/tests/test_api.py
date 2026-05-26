import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from filewise.api.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FILEWISE_EMBED_MODEL", "fake")
    monkeypatch.setenv("FILEWISE_LLM", "fake:echo")
    monkeypatch.setenv("FILEWISE_VECTORS_PATH", str(tmp_path / "v.pkl"))
    monkeypatch.setenv("FILEWISE_DB_PATH", str(tmp_path / "db.sqlite"))
    monkeypatch.setenv("FILEWISE_SCORE_THRESHOLD", "-1.0")
    monkeypatch.setenv("FILEWISE_CHUNK_SIZE", "200")
    monkeypatch.setenv("FILEWISE_CHUNK_OVERLAP", "40")
    app = create_app()
    with TestClient(app) as c:
        yield c


def _upload_handbook(client: TestClient) -> str:
    data = (FIXTURES / "handbook.md").read_bytes()
    resp = client.post("/documents", files={"file": ("handbook.md", data, "text/markdown")})
    assert resp.status_code == 201, resp.text
    return resp.json()["document_id"]


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_returns_metadata(client: TestClient) -> None:
    data = (FIXTURES / "handbook.md").read_bytes()
    r = client.post("/documents", files={"file": ("handbook.md", data, "text/markdown")})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "handbook.md"
    assert body["chunks"] > 0
    assert body["char_count"] > 0
    assert body["embedding_model"] == "fake"


def test_ask_returns_answer_with_citations(client: TestClient) -> None:
    _upload_handbook(client)
    r = client.post("/ask", json={"query": "What is the leave policy?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert body["citations"]
    assert all(c["doc"] == "handbook.md" for c in body["citations"])


def test_ask_refusal_for_off_topic(client: TestClient) -> None:
    _upload_handbook(client)
    r = client.post(
        "/ask",
        json={"query": "What is the airspeed of an unladen swallow?", "threshold": 0.8},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "not_enough_evidence"
    assert body["answer"] is None
    assert body["citations"] == []
    assert body["hint"]


def test_unsupported_format_rejected(client: TestClient) -> None:
    r = client.post("/documents", files={"file": ("image.png", b"\x89PNG\r\n", "image/png")})
    assert r.status_code == 415
    assert r.json()["error"] == "unsupported_format"


def test_file_too_large(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILEWISE_MAX_UPLOAD_BYTES", "10")
    from filewise.api.main import create_app as _create

    app = _create()
    with TestClient(app) as c:
        r = c.post("/documents", files={"file": ("big.txt", b"this is longer than ten bytes", "text/plain")})
        assert r.status_code == 413
        assert r.json()["error"] == "file_too_large"


def test_delete_purges_chunks(client: TestClient) -> None:
    doc_id = _upload_handbook(client)
    r = client.delete(f"/documents/{doc_id}")
    assert r.status_code == 204
    r2 = client.post("/ask", json={"query": "What is the leave policy?", "threshold": -1.0})
    assert r2.status_code == 200
    assert r2.json()["citations"] == [] or r2.json()["status"] == "not_enough_evidence"


def test_get_document_not_found(client: TestClient) -> None:
    r = client.get("/documents/d_does_not_exist")
    assert r.status_code == 404
    assert r.json()["error"] == "document_not_found"


def teardown_module() -> None:
    for k in list(os.environ):
        if k.startswith("FILEWISE_"):
            del os.environ[k]
