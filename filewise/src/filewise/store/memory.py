"""In-memory numpy-backed vector store with pickle persistence."""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from filewise.errors import EmbeddingDimMismatch
from filewise.ingestion.types import Chunk
from filewise.store.base import ScoredChunk


@dataclass
class _Persisted:
    embedder_name: str
    dim: int
    chunks: list[Chunk]
    vectors: NDArray[np.float32]
    doc_names: dict[str, str] | None = None


class MemoryVectorStore:
    """Cosine-sim store. Vectors are assumed unit-normalized by the embedder."""

    def __init__(self, embedder_name: str, dim: int, path: Path | None = None) -> None:
        self.embedder_name: str = embedder_name
        self.dim: int = dim
        self._chunks: list[Chunk] = []
        self._vectors: NDArray[np.float32] = np.zeros((0, dim), dtype=np.float32)
        self._path: Path | None = path
        self._doc_names: dict[str, str] = {}

    @classmethod
    def load_or_new(cls, path: Path, embedder_name: str, dim: int) -> MemoryVectorStore:
        if path.exists():
            with path.open("rb") as fh:
                data: _Persisted = pickle.load(fh)
            if data.embedder_name != embedder_name or data.dim != dim:
                raise EmbeddingDimMismatch(
                    f"Store at {path} was built with {data.embedder_name}/{data.dim}d, "
                    f"but current config requests {embedder_name}/{dim}d."
                )
            store = cls(embedder_name, dim, path=path)
            store._chunks = list(data.chunks)
            store._vectors = data.vectors.astype(np.float32, copy=False)
            store._doc_names = dict(data.doc_names or {})
            return store
        return cls(embedder_name, dim, path=path)

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors length mismatch")
        if not chunks:
            return
        for v in vectors:
            if len(v) != self.dim:
                raise EmbeddingDimMismatch(
                    f"vector dim {len(v)} != store dim {self.dim}"
                )
        new_vecs = np.asarray(vectors, dtype=np.float32)
        existing_ids = {c.chunk_id: i for i, c in enumerate(self._chunks)}
        keep_mask = np.ones(len(self._chunks), dtype=bool)
        for c in chunks:
            if c.chunk_id in existing_ids:
                keep_mask[existing_ids[c.chunk_id]] = False
        if not keep_mask.all():
            self._chunks = [c for c, keep in zip(self._chunks, keep_mask, strict=True) if keep]
            self._vectors = self._vectors[keep_mask]
        self._chunks.extend(chunks)
        self._vectors = np.vstack([self._vectors, new_vecs]) if self._vectors.size else new_vecs
        self._persist()

    def search(self, vector: list[float], k: int) -> list[ScoredChunk]:
        if len(vector) != self.dim:
            raise EmbeddingDimMismatch(f"query dim {len(vector)} != store dim {self.dim}")
        if not self._chunks:
            return []
        q = np.asarray(vector, dtype=np.float32)
        scores = self._vectors @ q
        top_idx = np.argsort(-scores)[:k]
        return [ScoredChunk(chunk=self._chunks[i], score=float(scores[i])) for i in top_idx]

    def delete_doc(self, doc_id: str) -> None:
        keep_mask = np.array([c.doc_id != doc_id for c in self._chunks], dtype=bool)
        if keep_mask.all() and doc_id not in self._doc_names:
            return
        self._chunks = [c for c, keep in zip(self._chunks, keep_mask, strict=True) if keep]
        self._vectors = self._vectors[keep_mask]
        self._doc_names.pop(doc_id, None)
        self._persist()

    def doc_count(self) -> int:
        return len({c.doc_id for c in self._chunks})

    def register_doc(self, doc_id: str, name: str) -> None:
        self._doc_names[doc_id] = name
        self._persist()

    def doc_names(self) -> dict[str, str]:
        return dict(self._doc_names)

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = _Persisted(
            embedder_name=self.embedder_name,
            dim=self.dim,
            chunks=list(self._chunks),
            vectors=self._vectors.copy(),
            doc_names=dict(self._doc_names),
        )
        with self._path.open("wb") as fh:
            pickle.dump(data, fh)
