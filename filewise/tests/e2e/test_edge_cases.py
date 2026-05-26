"""Failure modes + adversarial inputs.

Each test states the contract being defended.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_unsupported_format_returns_415(client: TestClient) -> None:
    r = client.post("/documents", files={"file": ("a.png", b"\x89PNG\r\n", "image/png")})
    assert r.status_code == 415
    assert r.json()["error"] == "unsupported_format"


def test_corrupt_pdf_returns_safe_error(client: TestClient) -> None:
    bogus = b"%PDF-1.4\n%nope-this-is-not-a-pdf\n"
    r = client.post("/documents", files={"file": ("broken.pdf", bogus, "application/pdf")})
    assert r.status_code >= 400
    assert r.status_code < 600


def test_empty_text_rejected(client: TestClient) -> None:
    r = client.post("/documents", files={"file": ("blank.txt", b"   \n\n  \n", "text/plain")})
    assert r.status_code == 415
    assert r.json()["error"] == "no_extractable_text"


def test_oversized_upload_returns_413(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILEWISE_MAX_UPLOAD_BYTES", "32")
    from filewise.api.main import create_app

    with TestClient(create_app()) as c:
        r = c.post(
            "/documents",
            files={"file": ("big.txt", b"a" * 1024, "text/plain")},
        )
        assert r.status_code == 413
        assert r.json()["error"] == "file_too_large"


def test_query_validation_empty_string(client: TestClient) -> None:
    r = client.post("/ask", json={"query": ""})
    assert r.status_code == 422


def test_query_validation_too_long(client: TestClient) -> None:
    r = client.post("/ask", json={"query": "x" * 5000})
    assert r.status_code == 422


def test_query_validation_invalid_threshold(client: TestClient) -> None:
    r = client.post("/ask", json={"query": "ok", "threshold": 2.0})
    assert r.status_code == 422


def test_query_validation_invalid_k(client: TestClient) -> None:
    r = client.post("/ask", json={"query": "ok", "k": 0})
    assert r.status_code == 422


def test_get_unknown_doc_404(client: TestClient) -> None:
    r = client.get("/documents/d_definitely_missing")
    assert r.status_code == 404
    assert r.json()["error"] == "document_not_found"


def test_persistence_round_trip_across_app_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fixtures_dir: Path
) -> None:
    """Vectors persisted by app instance #1 are usable by app instance #2."""
    vp = tmp_path / "v.pkl"
    monkeypatch.setenv("FILEWISE_VECTORS_PATH", str(vp))

    from filewise.api.main import create_app

    with TestClient(create_app()) as c1:
        data = (fixtures_dir / "handbook.md").read_bytes()
        c1.post("/documents", files={"file": ("handbook.md", data, "text/markdown")})
        r = c1.post("/ask", json={"query": "anything", "threshold": -1.0})
        assert r.json()["citations"]

    assert vp.exists()

    with TestClient(create_app()) as c2:
        r = c2.post("/ask", json={"query": "anything", "threshold": -1.0})
        assert r.json()["citations"], "vectors should persist across app restarts"


def test_embedding_dim_mismatch_on_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fixtures_dir: Path
) -> None:
    """Switching embedding model with a pre-existing store must refuse to load."""
    vp = tmp_path / "v.pkl"
    monkeypatch.setenv("FILEWISE_VECTORS_PATH", str(vp))
    monkeypatch.setenv("FILEWISE_EMBED_MODEL", "fake")

    from filewise.api.main import create_app

    with TestClient(create_app()) as c:
        data = (fixtures_dir / "handbook.md").read_bytes()
        c.post("/documents", files={"file": ("handbook.md", data, "text/markdown")})

    with vp.open("rb") as fh:
        persisted = pickle.load(fh)
    persisted.embedder_name = "different-model"
    persisted.dim = 128
    with vp.open("wb") as fh:
        pickle.dump(persisted, fh)

    with pytest.raises(Exception) as exc_info, TestClient(create_app()) as _:
        pass
    assert "mismatch" in str(exc_info.value).lower() or "embedding" in str(exc_info.value).lower()


def test_citation_never_orphaned_to_deleted_doc(
    client: TestClient, fixtures_dir: Path
) -> None:
    """After deleting a doc, no /ask response should cite it."""
    data = (fixtures_dir / "handbook.md").read_bytes()
    r = client.post("/documents", files={"file": ("handbook.md", data, "text/markdown")})
    doc_id = r.json()["document_id"]

    r2 = client.post("/ask", json={"query": "test", "threshold": -1.0})
    assert any(c["doc"] == "handbook.md" for c in r2.json()["citations"])

    client.delete(f"/documents/{doc_id}")
    r3 = client.post("/ask", json={"query": "test", "threshold": -1.0})
    for cit in r3.json()["citations"]:
        assert cit["doc"] != "handbook.md", (
            f"orphaned citation to deleted doc: {cit}"
        )
