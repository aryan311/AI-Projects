from itertools import pairwise

from hypothesis import given, settings
from hypothesis import strategies as st

from filewise.ingestion.chunker import chunk_document
from filewise.ingestion.types import PageBlock, RawDocument


def _doc(text: str) -> RawDocument:
    return RawDocument(name="x.txt", blocks=(PageBlock(text=text, page=1),))


def test_offsets_round_trip() -> None:
    text = "abcdefghijklmnopqrstuvwxyz" * 10
    doc = _doc(text)
    chunks = chunk_document(doc, doc_id="d1", size=50, overlap=10)
    full = doc.full_text
    for c in chunks:
        assert full[c.char_start : c.char_end] == c.text


def test_overlap_shared() -> None:
    text = "a" * 200 + "b" * 200
    doc = _doc(text)
    chunks = chunk_document(doc, doc_id="d1", size=100, overlap=20)
    for prev, curr in pairwise(chunks):
        if prev.page != curr.page:
            continue
        shared = prev.char_end - curr.char_start
        assert shared >= 20


def test_determinism() -> None:
    text = "the quick brown fox " * 100
    doc = _doc(text)
    a = chunk_document(doc, doc_id="d1", size=80, overlap=20)
    b = chunk_document(doc, doc_id="d1", size=80, overlap=20)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
    assert [c.text for c in a] == [c.text for c in b]


def test_metadata_preserved_multi_page() -> None:
    doc = RawDocument(
        name="multi.pdf",
        blocks=(
            PageBlock(text="page one text here. " * 20, page=1),
            PageBlock(text="page two text here. " * 20, page=2),
        ),
    )
    chunks = chunk_document(doc, doc_id="d2", size=60, overlap=10)
    pages = {c.page for c in chunks}
    assert pages == {1, 2}
    for c in chunks:
        if c.page == 1:
            assert "page one" in c.text
        else:
            assert "page two" in c.text


def test_no_chunk_spans_block_boundary() -> None:
    doc = RawDocument(
        name="multi.pdf",
        blocks=(
            PageBlock(text="A" * 100, page=1),
            PageBlock(text="B" * 100, page=2),
        ),
    )
    chunks = chunk_document(doc, doc_id="d3", size=80, overlap=20)
    for c in chunks:
        assert set(c.text) <= {"A"} or set(c.text) <= {"B"}


@settings(max_examples=30)
@given(st.text(min_size=1, max_size=2000))
def test_property_offsets(text: str) -> None:
    doc = _doc(text)
    chunks = chunk_document(doc, doc_id="d", size=100, overlap=20)
    for c in chunks:
        assert doc.full_text[c.char_start : c.char_end] == c.text
