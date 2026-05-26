from pathlib import Path

from filewise.answer.answerer import Answerer
from filewise.answer.llm import FakeLLM
from filewise.answer.validator import CitationValidator
from filewise.embedding.fake import FakeEmbedding
from filewise.ingestion.chunker import chunk_document
from filewise.ingestion.loaders import load
from filewise.retrieval.retriever import Retriever
from filewise.store.memory import MemoryVectorStore

FIXTURES = Path(__file__).parent / "fixtures"


def _wire(threshold: float, llm: FakeLLM | None = None) -> Answerer:
    raw = load("handbook.md", (FIXTURES / "handbook.md").read_bytes())
    chunks = chunk_document(raw, doc_id="handbook", size=200, overlap=40)
    e = FakeEmbedding()
    store = MemoryVectorStore(e.name, e.dim)
    store.upsert(chunks, e.embed([c.text for c in chunks]))
    retriever = Retriever(e, store)
    return Answerer(retriever, llm or FakeLLM(), CitationValidator(), threshold=threshold, k=5)


def _docmap() -> dict[str, str]:
    return {"handbook": "handbook.md"}


def test_strong_hit_returns_answer_with_citations() -> None:
    answerer = _wire(threshold=-1.0)
    result = answerer.answer("What is the leave policy?", _docmap())
    assert result.status == "answered"
    assert result.answer
    assert result.citations
    assert all(c.doc == "handbook.md" for c in result.citations)


def test_weak_hit_returns_refusal_without_llm_call() -> None:
    answerer = _wire(threshold=2.0)
    result = answerer.answer("What is the leave policy?", _docmap())
    assert result.status == "not_enough_evidence"
    assert result.answer is None
    assert result.citations == []


def test_validator_downgrades_answer_with_empty_citations() -> None:
    answerer = _wire(threshold=-1.0, llm=FakeLLM(force_empty=True))
    result = answerer.answer("What is the leave policy?", _docmap())
    assert result.status == "not_enough_evidence"
    assert result.answer is None


def test_citation_snippet_truncated() -> None:
    answerer = _wire(threshold=-1.0)
    result = answerer.answer("What is the leave policy?", _docmap())
    for c in result.citations:
        assert len(c.snippet) <= 200
