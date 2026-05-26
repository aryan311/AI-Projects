"""Per-format ingestion + metadata preservation through the API.

Fake embedder, so we don't assert *which* chunk wins ranking — only that
the right structural facts come back (pages, sections, citations exist).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("client")


def _upload(c: TestClient, fixtures: Path, rel: str, mime: str) -> dict:
    name = Path(rel).name
    data = (fixtures / rel).read_bytes()
    r = c.post("/documents", files={"file": (name, data, mime)})
    assert r.status_code == 201, r.text
    return r.json()


def test_pdf_3_pages_extracted(client: TestClient, fixtures_dir: Path) -> None:
    body = _upload(client, fixtures_dir, "pdf/handbook.pdf", "application/pdf")
    assert body["pages"] == 3
    assert body["char_count"] > 500
    assert body["chunks"] >= 3


def test_pdf_2_pages_extracted(client: TestClient, fixtures_dir: Path) -> None:
    body = _upload(client, fixtures_dir, "pdf/security_policy.pdf", "application/pdf")
    assert body["pages"] == 2
    assert body["chunks"] >= 2


def test_pdf_citations_carry_page_number(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "pdf/handbook.pdf", "application/pdf")
    r = client.post("/ask", json={"query": "anything", "k": 10, "threshold": -1.0})
    citations = r.json()["citations"]
    assert citations
    assert any(c["page"] is not None for c in citations)
    pages_seen = {c["page"] for c in citations if c["page"] is not None}
    assert pages_seen <= {1, 2, 3}


def test_markdown_section_path_propagated(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    r = client.post("/ask", json={"query": "anything", "k": 10, "threshold": -1.0})
    citations = r.json()["citations"]
    sections = {c.get("section") for c in citations}
    assert any(
        s and "Acme Employee Handbook" in s for s in sections if s
    ), f"no markdown section path in citations: {sections}"


def test_txt_has_no_section_or_page_beyond_1(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "release_notes.txt", "text/plain")
    r = client.post("/ask", json={"query": "anything", "k": 10, "threshold": -1.0})
    for c in r.json()["citations"]:
        assert c["page"] in (None, 1)


def test_all_three_formats_coexist(client: TestClient, fixtures_dir: Path) -> None:
    _upload(client, fixtures_dir, "handbook.md", "text/markdown")
    _upload(client, fixtures_dir, "pdf/handbook.pdf", "application/pdf")
    _upload(client, fixtures_dir, "release_notes.txt", "text/plain")

    r = client.post("/ask", json={"query": "anything", "k": 20, "threshold": -1.0})
    docs = {c["doc"] for c in r.json()["citations"]}
    assert {"handbook.md", "handbook.pdf", "release_notes.txt"} <= docs
