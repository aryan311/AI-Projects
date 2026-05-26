"""VectorStore Protocol + scored result type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from filewise.ingestion.types import Chunk


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@runtime_checkable
class VectorStore(Protocol):
    embedder_name: str
    dim: int

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...
    def search(self, vector: list[float], k: int) -> list[ScoredChunk]: ...
    def delete_doc(self, doc_id: str) -> None: ...
    def doc_count(self) -> int: ...
    def register_doc(self, doc_id: str, name: str) -> None: ...
    def doc_names(self) -> dict[str, str]: ...
