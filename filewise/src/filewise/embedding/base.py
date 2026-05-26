"""EmbeddingService Protocol + factory."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingService(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def make_embedder(spec: str) -> EmbeddingService:
    """Construct an embedder from a spec string.

    Spec values:
      - ``"fake"`` → deterministic 64-d hash embedder (always available, tests).
      - any other string → treated as a sentence-transformers model id; requires
        the ``sbert`` extra installed.
    """
    if spec == "fake":
        from filewise.embedding.fake import FakeEmbedding

        return FakeEmbedding()
    from filewise.embedding.sbert import SbertEmbedding

    return SbertEmbedding(model_name=spec)
