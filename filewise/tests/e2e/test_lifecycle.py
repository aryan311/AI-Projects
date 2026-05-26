"""Black-box lifecycle through HTTP boundary (TestClient, fake embedder).

Asserts plumbing only: status codes, response shapes, citation discipline,
state transitions. Retrieval *quality* lives in test_sbert_quality.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("client")


def _upload(c: TestClient, fixtures: Path, name: str, mime: str) -> dict:
    data = (fixtures / name).read_bytes()
    r = c.post("/documents", files={"file": (name, data, mime)})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["chunks"] > 0
    assert body["document_id"].startswith("d_")
    return body


def test_health_then_metadata(client: TestClient) -> None:
    h = client.get("/healthz")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"


def test_upload_md_then_get_then_delete(client: TestClient, fixtures_dir: Path) -> None:
    doc = _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    doc_id = doc["document_id"]

    g = client.get(f"/documents/{doc_id}")
    assert g.status_code == 200
    assert g.json()["document_id"] == doc_id

    d = client.delete(f"/documents/{doc_id}")
    assert d.status_code == 204

    g2 = client.get(f"/documents/{doc_id}")
    assert g2.status_code == 404
    assert g2.json()["error"] == "document_not_found"

    d2 = client.delete(f"/documents/{doc_id}")
    assert d2.status_code == 404


def test_ask_returns_well_formed_envelope(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    r = client.post("/ask", json={"query": "leave policy", "threshold": -1.0})
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) >= {"status", "answer", "citations", "retrieval"}
    assert body["status"] in {"answered", "not_enough_evidence"}
    assert isinstance(body["citations"], list)
    assert set(body["retrieval"].keys()) == {"k", "threshold", "max_score"}
    for c in body["citations"]:
        assert {"doc", "snippet", "score"} <= set(c.keys())
        assert isinstance(c["score"], (int, float))


def test_refusal_when_threshold_unreachable(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    r = client.post("/ask", json={"query": "anything", "threshold": 0.9999})
    body = r.json()
    assert body["status"] == "not_enough_evidence"
    assert body["answer"] is None
    assert body["citations"] == []
    assert body["hint"]


def test_ask_with_no_documents_refuses(client: TestClient) -> None:
    r = client.post("/ask", json={"query": "anything", "threshold": -1.0})
    assert r.status_code == 200
    assert r.json()["status"] == "not_enough_evidence"


def test_multi_doc_upload_and_isolated_delete(client: TestClient, fixtures_dir: Path) -> None:
    doc_a = _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    doc_b = _upload(client, fixtures_dir, "release_notes.txt", "text/plain")

    r1 = client.post("/ask", json={"query": "any question", "threshold": -1.0, "k": 10})
    docs_returned = {c["doc"] for c in r1.json()["citations"]}
    assert "handbook.md" in docs_returned
    assert "release_notes.txt" in docs_returned

    client.delete(f"/documents/{doc_a['document_id']}")
    r2 = client.post("/ask", json={"query": "any question", "threshold": -1.0, "k": 10})
    docs_after = {c["doc"] for c in r2.json()["citations"]}
    assert "handbook.md" not in docs_after
    assert "release_notes.txt" in docs_after

    client.delete(f"/documents/{doc_b['document_id']}")
    r3 = client.post("/ask", json={"query": "any question", "threshold": -1.0})
    assert r3.json()["status"] == "not_enough_evidence"


def test_request_overrides_take_effect(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    r = client.post("/ask", json={"query": "anything", "k": 2, "threshold": -1.0})
    body = r.json()
    assert body["retrieval"]["k"] == 2
    assert body["retrieval"]["threshold"] == -1.0
    assert len(body["citations"]) <= 2


def test_pdf_upload_extracts_pages(client: TestClient, fixtures_dir: Path) -> None:
    doc = _upload(client, fixtures_dir, "pdf/handbook.pdf", "application/pdf")
    assert doc["pages"] == 3
    assert doc["chunks"] >= 3
