"""Deterministic char-based chunker with page/section metadata."""

from __future__ import annotations

import hashlib

from filewise.ingestion.types import Chunk, RawDocument


def chunk_document(
    doc: RawDocument,
    doc_id: str,
    size: int,
    overlap: int,
) -> list[Chunk]:
    """Split each block into overlapping windows.

    Chunks never span block boundaries — that keeps page/section metadata
    truthful. ``char_start`` / ``char_end`` reference offsets into the
    document's full text, so a chunk's text equals
    ``doc.full_text[chunk.char_start:chunk.char_end]``.
    """
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be in [0, size)")

    chunks: list[Chunk] = []
    block_offset = 0
    step = size - overlap

    for block in doc.blocks:
        text = block.text
        if not text:
            block_offset += 0
            continue
        i = 0
        while i < len(text):
            j = min(i + size, len(text))
            piece = text[i:j]
            if piece.strip():
                start = block_offset + i
                end = block_offset + j
                chunk_id = _chunk_id(doc_id, start, end)
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        text=piece,
                        page=block.page,
                        section=block.section,
                        char_start=start,
                        char_end=end,
                    )
                )
            if j == len(text):
                break
            i += step
        block_offset += len(text)

    return chunks


def _chunk_id(doc_id: str, start: int, end: int) -> str:
    h = hashlib.sha1(f"{doc_id}:{start}:{end}".encode()).hexdigest()[:16]
    return f"c_{h}"
