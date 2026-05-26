import pytest

from filewise.errors import NoExtractableText, UnsupportedFormat
from filewise.ingestion.loaders import load


def test_loads_text() -> None:
    doc = load("notes.txt", b"hello world\nsecond line\n")
    assert doc.name == "notes.txt"
    assert doc.page_count == 1
    assert "hello world" in doc.full_text


def test_loads_markdown_with_sections() -> None:
    text = "# Title\n\nintro\n\n## Sub\n\nbody text here\n"
    doc = load("notes.md", text.encode("utf-8"))
    sections = [b.section for b in doc.blocks if b.section]
    assert "Title" in sections
    assert any(s == "Title > Sub" for s in sections)


def test_markdown_without_headings() -> None:
    doc = load("flat.md", b"just text, no headings.\n")
    assert len(doc.blocks) == 1
    assert doc.blocks[0].section is None


def test_rejects_unsupported() -> None:
    with pytest.raises(UnsupportedFormat):
        load("image.png", b"\x89PNG\r\n")


def test_rejects_empty_text() -> None:
    with pytest.raises(NoExtractableText):
        load("blank.txt", b"   \n  \n")


def test_loads_pdf(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    pdf_path = tmp_path / "blank.pdf"
    with pdf_path.open("wb") as fh:
        writer.write(fh)
    data = pdf_path.read_bytes()
    with pytest.raises(NoExtractableText):
        load("blank.pdf", data)
