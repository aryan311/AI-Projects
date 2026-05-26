"""Shared fixtures for E2E suite.

Each test gets its own TestClient with an isolated vector store path.
Env vars are reset around the suite so leakage from earlier unit tests
cannot poison the FastAPI lifespan.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for k in list(os.environ):
        if k.startswith("FILEWISE_"):
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("FILEWISE_EMBED_MODEL", "fake")
    monkeypatch.setenv("FILEWISE_LLM", "fake:echo")
    monkeypatch.setenv("FILEWISE_VECTORS_PATH", str(tmp_path / "v.pkl"))
    monkeypatch.setenv("FILEWISE_DB_PATH", str(tmp_path / "db.sqlite"))
    monkeypatch.setenv("FILEWISE_CHUNK_SIZE", "200")
    monkeypatch.setenv("FILEWISE_CHUNK_OVERLAP", "40")


@pytest.fixture
def client() -> Iterator[TestClient]:
    from filewise.api.main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent.parent / "fixtures"


def make_text_pdf(path: Path, pages: list[str]) -> bytes:
    """Write a multi-page PDF with the given page texts. Returns raw bytes."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        for line in page_text.splitlines() or [""]:
            pdf.multi_cell(0, 8, line)
    pdf.output(str(path))
    return path.read_bytes()
