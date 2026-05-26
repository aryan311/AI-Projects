"""Optional sentence-transformers backed embedder. Not imported unless requested."""

from __future__ import annotations

from typing import Any


class SbertEmbedding:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers not installed. Install with 'pip install filewise[sbert]'."
            ) from exc
        self._model: Any = SentenceTransformer(model_name)
        self.name: str = model_name
        sample_dim = self._model.get_sentence_embedding_dimension()
        if sample_dim is None:  # pragma: no cover
            raise RuntimeError("Could not determine embedding dimension from model.")
        self.dim: int = int(sample_dim)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]
