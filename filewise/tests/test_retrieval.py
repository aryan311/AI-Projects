from pathlib import Path

import pytest
import yaml

from filewise.embedding.fake import FakeEmbedding
from filewise.ingestion.chunker import chunk_document
from filewise.ingestion.loaders import load
from filewise.retrieval.retriever import Retriever
from filewise.store.memory import MemoryVectorStore

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def retriever() -> Retriever:
    raw = load("handbook.md", (FIXTURES / "handbook.md").read_bytes())
    chunks = chunk_document(raw, doc_id="handbook", size=200, overlap=40)
    e = FakeEmbedding()
    store = MemoryVectorStore(e.name, e.dim)
    store.upsert(chunks, e.embed([c.text for c in chunks]))
    return Retriever(e, store)


def test_threshold_filters_results(retriever: Retriever) -> None:
    high = retriever.search("anything", k=5, threshold=1.5)
    assert high.hits == []
    low = retriever.search("leave policy", k=5, threshold=-1.0)
    assert len(low.hits) > 0


def test_raw_top_score_exposed_even_on_refusal(retriever: Retriever) -> None:
    """Even when threshold rejects everything, raw_top_score reports the
    actual best similarity so callers can diagnose."""
    result = retriever.search("leave policy", k=5, threshold=1.5)
    assert result.hits == []
    assert result.raw_top_score != 0.0


def test_top_chunk_substring(retriever: Retriever) -> None:
    questions = yaml.safe_load((FIXTURES / "handbook_questions.yaml").read_text())
    expected_refusal_q = next(q for q in questions if q.get("expect_refusal"))
    results = retriever.search(expected_refusal_q["question"], k=5, threshold=0.40)
    assert results.hits == []


def test_answerable_questions_return_expected_chunks(retriever: Retriever) -> None:
    questions = yaml.safe_load((FIXTURES / "handbook_questions.yaml").read_text())
    answerable = [q for q in questions if not q.get("expect_refusal")]
    for entry in answerable:
        result = retriever.search(entry["question"], k=5, threshold=entry["min_score"])
        assert result.hits, f"no chunks above threshold for: {entry['question']}"
        top_texts = " ".join(r.chunk.text for r in result.hits)
        assert entry["must_contain"] in top_texts, (
            f"expected substring '{entry['must_contain']}' not in retrieved chunks "
            f"for '{entry['question']}'"
        )
