"""Retrieval *quality* tests using real sentence-transformers embeddings.

These tests are marked ``sbert`` and skipped by default. Run with::

    pytest -m sbert

The model is downloaded by sentence-transformers on first run (~80MB) and
cached under ``~/.cache/huggingface``. CI does not run this marker.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

pytestmark = pytest.mark.sbert

SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@pytest.fixture(scope="module")
def sbert_client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    pytest.importorskip("sentence_transformers")
    tmp = tmp_path_factory.mktemp("sbert")
    import os

    for k in list(os.environ):
        if k.startswith("FILEWISE_"):
            del os.environ[k]
    os.environ.update(
        {
            "FILEWISE_EMBED_MODEL": SBERT_MODEL,
            "FILEWISE_LLM": "fake:echo",
            "FILEWISE_VECTORS_PATH": str(tmp / "v.pkl"),
            "FILEWISE_DB_PATH": str(tmp / "db.sqlite"),
            "FILEWISE_CHUNK_SIZE": "180",
            "FILEWISE_CHUNK_OVERLAP": "40",
            "FILEWISE_SCORE_THRESHOLD": "0.35",
        }
    )
    from filewise.api.main import create_app

    fixtures = Path(__file__).parent.parent / "fixtures"

    client = TestClient(create_app())
    client.__enter__()

    uploads = [
        ("handbook.md", fixtures / "handbook.md", "text/markdown"),
        ("handbook.pdf", fixtures / "pdf" / "handbook.pdf", "application/pdf"),
        ("security_policy.pdf", fixtures / "pdf" / "security_policy.pdf", "application/pdf"),
        ("release_notes.txt", fixtures / "release_notes.txt", "text/plain"),
    ]
    for name, path, mime in uploads:
        r = client.post(
            "/documents", files={"file": (name, path.read_bytes(), mime)}
        )
        assert r.status_code == 201, f"{name}: {r.text}"

    yield client
    client.__exit__(None, None, None)


def _flatten_questions() -> list[tuple[str, dict]]:
    fixtures = Path(__file__).parent.parent / "fixtures"
    raw = yaml.safe_load((fixtures / "e2e_questions.yaml").read_text())
    out: list[tuple[str, dict]] = []
    label_to_doc = {
        "handbook_md": "handbook.md",
        "handbook_pdf": "handbook.pdf",
        "security_pdf": "security_policy.pdf",
        "release_notes_txt": "release_notes.txt",
    }
    for label, entries in raw.items():
        doc_name = label_to_doc.get(label)
        for entry in entries:
            out.append((doc_name or label, entry))
    return out


@pytest.mark.parametrize(("expected_doc", "entry"), _flatten_questions())
def test_quality(expected_doc: str, entry: dict, sbert_client: TestClient) -> None:
    """For each fixture row: answerable Qs return the right doc with the
    expected substring in a top-3 citation; refusal Qs trigger refusal."""
    r = sbert_client.post(
        "/ask",
        json={"query": entry["question"], "k": 5},
    )
    assert r.status_code == 200
    body = r.json()

    if entry.get("expect_refusal"):
        assert body["status"] == "not_enough_evidence", (
            f"expected refusal for '{entry['question']}' got status={body['status']} "
            f"max_score={body['retrieval']['max_score']}"
        )
        return

    assert body["status"] == "answered", (
        f"expected answer for '{entry['question']}' got status={body['status']} "
        f"max_score={body['retrieval']['max_score']}"
    )
    top3 = body["citations"][:3]
    assert top3, "expected at least one citation"

    docs_top3 = [c["doc"] for c in top3]
    assert expected_doc in docs_top3, (
        f"expected doc '{expected_doc}' missing from top-3 {docs_top3} "
        f"for '{entry['question']}'"
    )

    must = entry["must_contain"]
    assert any(must in c["snippet"] for c in top3), (
        f"substring '{must}' not in any top-3 snippet for '{entry['question']}'; "
        f"snippets={[c['snippet'][:60] for c in top3]}"
    )

    if "expected_page" in entry:
        pages_top3 = [c.get("page") for c in top3 if c["doc"] == expected_doc]
        assert entry["expected_page"] in pages_top3, (
            f"expected page {entry['expected_page']} not in {pages_top3} "
            f"for '{entry['question']}'"
        )


def test_refusal_max_score_is_actually_below_threshold(sbert_client: TestClient) -> None:
    r = sbert_client.post(
        "/ask",
        json={"query": "What is the airspeed of an unladen swallow?"},
    )
    body = r.json()
    assert body["status"] == "not_enough_evidence"
    assert body["retrieval"]["max_score"] < body["retrieval"]["threshold"]


def test_strong_hit_max_score_above_threshold(sbert_client: TestClient) -> None:
    r = sbert_client.post("/ask", json={"query": "What is the leave policy?"})
    body = r.json()
    assert body["status"] == "answered"
    assert body["retrieval"]["max_score"] >= body["retrieval"]["threshold"]
