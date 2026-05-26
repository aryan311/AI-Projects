"""Top-k retrieval with score threshold."""

from __future__ import annotations

from dataclasses import dataclass

from filewise.embedding.base import EmbeddingService
from filewise.store.base import ScoredChunk, VectorStore


@dataclass(frozen=True)
class RetrievalResult:
    hits: list[ScoredChunk]
    raw_top_score: float


class Retriever:
    def __init__(self, embedder: EmbeddingService, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def search(self, query: str, k: int, threshold: float) -> RetrievalResult:
        [vec] = self._embedder.embed([query])
        raw = self._store.search(vec, k=k)
        raw_top = max((r.score for r in raw), default=0.0)
        kept = [r for r in raw if r.score >= threshold]
        return RetrievalResult(hits=kept, raw_top_score=raw_top)
