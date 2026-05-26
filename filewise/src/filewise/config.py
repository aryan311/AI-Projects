"""Runtime configuration. Only this module reads os.environ."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    embed_model: str
    llm: str
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int
    score_threshold: float
    db_path: str
    vectors_path: str
    max_upload_bytes: int

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            embed_model=os.getenv("FILEWISE_EMBED_MODEL", "fake"),
            llm=os.getenv("FILEWISE_LLM", "fake:echo"),
            chunk_size=int(os.getenv("FILEWISE_CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("FILEWISE_CHUNK_OVERLAP", "120")),
            retrieval_k=int(os.getenv("FILEWISE_RETRIEVAL_K", "5")),
            score_threshold=float(os.getenv("FILEWISE_SCORE_THRESHOLD", "0.35")),
            db_path=os.getenv("FILEWISE_DB_PATH", "./filewise.db"),
            vectors_path=os.getenv("FILEWISE_VECTORS_PATH", "./vectors.npy"),
            max_upload_bytes=int(os.getenv("FILEWISE_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        )
