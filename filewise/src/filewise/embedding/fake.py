"""Deterministic hash-based fake embedder for offline tests."""

from __future__ import annotations

import hashlib
import math
import re

_WORD_RE = re.compile(r"[a-z0-9]+")


class FakeEmbedding:
    name: str = "fake"
    dim: int = 64

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = _WORD_RE.findall(text.lower())
        if not tokens:
            tokens = ["<empty>"]
        for tok in tokens:
            h = hashlib.sha1(tok.encode("utf-8")).digest()
            for i in range(self.dim):
                byte = h[i % len(h)]
                vec[i] += (byte - 127) / 128.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            vec[0] = 1.0
            return vec
        return [x / norm for x in vec]
