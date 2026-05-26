"""Process-level singletons for the FastAPI app.

Kept tiny on purpose: docs metadata lives in memory in v0.1.0. SQLite is a
later upgrade — the interface (`StateStore`) is what matters for swapping.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from filewise.answer.answerer import Answerer
from filewise.answer.llm import LLM, make_llm
from filewise.answer.validator import CitationValidator
from filewise.config import Config
from filewise.embedding.base import EmbeddingService, make_embedder
from filewise.errors import DocumentNotFound
from filewise.ingestion.chunker import chunk_document
from filewise.ingestion.loaders import load
from filewise.retrieval.retriever import Retriever
from filewise.store.memory import MemoryVectorStore


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    name: str
    pages: int
    char_count: int
    chunks: int


class AppState:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.embedder: EmbeddingService = make_embedder(config.embed_model)
        self.store = MemoryVectorStore.load_or_new(
            Path(config.vectors_path), self.embedder.name, self.embedder.dim
        )
        self.retriever = Retriever(self.embedder, self.store)
        self.llm: LLM = make_llm(config.llm)
        self.answerer = Answerer(
            self.retriever,
            self.llm,
            CitationValidator(),
            threshold=config.score_threshold,
            k=config.retrieval_k,
        )
        self._docs: dict[str, DocumentRecord] = {}
        for doc_id, name in self.store.doc_names().items():
            self._docs[doc_id] = DocumentRecord(
                document_id=doc_id, name=name, pages=0, char_count=0, chunks=0
            )

    def ingest(self, name: str, data: bytes) -> DocumentRecord:
        raw = load(name, data)
        doc_id = f"d_{uuid.uuid4().hex[:12]}"
        chunks = chunk_document(
            raw, doc_id=doc_id,
            size=self.config.chunk_size, overlap=self.config.chunk_overlap,
        )
        vectors = self.embedder.embed([c.text for c in chunks])
        self.store.upsert(chunks, vectors)
        self.store.register_doc(doc_id, name)
        record = DocumentRecord(
            document_id=doc_id, name=name,
            pages=raw.page_count, char_count=raw.char_count, chunks=len(chunks),
        )
        self._docs[doc_id] = record
        return record

    def get_doc(self, doc_id: str) -> DocumentRecord:
        if doc_id not in self._docs:
            raise DocumentNotFound(f"unknown document_id: {doc_id}")
        return self._docs[doc_id]

    def delete_doc(self, doc_id: str) -> None:
        if doc_id not in self._docs:
            raise DocumentNotFound(f"unknown document_id: {doc_id}")
        self.store.delete_doc(doc_id)
        del self._docs[doc_id]

    def doc_name_map(self) -> dict[str, str]:
        return {d.document_id: d.name for d in self._docs.values()}

    def list_docs(self) -> list[DocumentRecord]:
        return list(self._docs.values())
