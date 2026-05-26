import pytest

from filewise.embedding.fake import FakeEmbedding
from filewise.errors import EmbeddingDimMismatch
from filewise.ingestion.types import Chunk
from filewise.store.memory import MemoryVectorStore


def _chunk(cid: str, doc_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=cid, doc_id=doc_id, text=text,
        page=1, section=None, char_start=0, char_end=len(text),
    )


def test_upsert_and_search_returns_inserted() -> None:
    e = FakeEmbedding()
    store = MemoryVectorStore(e.name, e.dim)
    chunks = [_chunk("c1", "d1", "the leave policy is 21 days"),
              _chunk("c2", "d1", "the office is at baker street")]
    vecs = e.embed([c.text for c in chunks])
    store.upsert(chunks, vecs)
    [q] = e.embed(["how many days of leave"])
    results = store.search(q, k=1)
    assert len(results) == 1
    assert results[0].chunk.chunk_id in {"c1", "c2"}


def test_dim_mismatch_on_upsert() -> None:
    store = MemoryVectorStore("fake", dim=64)
    with pytest.raises(EmbeddingDimMismatch):
        store.upsert([_chunk("c1", "d1", "x")], [[0.0, 0.0, 0.0]])


def test_dim_mismatch_on_load(tmp_path) -> None:  # type: ignore[no-untyped-def]
    e = FakeEmbedding()
    path = tmp_path / "v.pkl"
    s1 = MemoryVectorStore.load_or_new(path, e.name, e.dim)
    s1.upsert([_chunk("c1", "d1", "x")], e.embed(["x"]))
    with pytest.raises(EmbeddingDimMismatch):
        MemoryVectorStore.load_or_new(path, "fake", dim=128)


def test_persist_round_trip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    e = FakeEmbedding()
    path = tmp_path / "v.pkl"
    s = MemoryVectorStore.load_or_new(path, e.name, e.dim)
    chunks = [_chunk("c1", "d1", "alpha beta gamma")]
    s.upsert(chunks, e.embed(["alpha beta gamma"]))
    s2 = MemoryVectorStore.load_or_new(path, e.name, e.dim)
    [q] = e.embed(["alpha"])
    results = s2.search(q, k=1)
    assert results and results[0].chunk.chunk_id == "c1"


def test_delete_doc_removes_chunks() -> None:
    e = FakeEmbedding()
    s = MemoryVectorStore(e.name, e.dim)
    chunks = [_chunk("c1", "d1", "alpha"), _chunk("c2", "d2", "beta")]
    s.upsert(chunks, e.embed([c.text for c in chunks]))
    s.delete_doc("d1")
    assert s.doc_count() == 1
    [q] = e.embed(["alpha"])
    results = s.search(q, k=5)
    assert all(r.chunk.doc_id == "d2" for r in results)


def test_upsert_replaces_existing_chunk_id() -> None:
    e = FakeEmbedding()
    s = MemoryVectorStore(e.name, e.dim)
    c1 = _chunk("c1", "d1", "original")
    s.upsert([c1], e.embed([c1.text]))
    c1b = _chunk("c1", "d1", "updated")
    s.upsert([c1b], e.embed([c1b.text]))
    [q] = e.embed(["updated"])
    [r] = s.search(q, k=1)
    assert r.chunk.text == "updated"
