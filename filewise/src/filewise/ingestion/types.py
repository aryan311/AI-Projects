"""Shared dataclasses for ingestion + downstream stages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageBlock:
    """A piece of source text with provenance.

    For PDFs, `page` is set. For Markdown, `section` is the heading path
    (e.g. ``"Benefits > Leave"``). At least one of the two is non-None.
    """

    text: str
    page: int | None = None
    section: str | None = None


@dataclass(frozen=True)
class RawDocument:
    name: str
    blocks: tuple[PageBlock, ...]

    @property
    def full_text(self) -> str:
        return "".join(b.text for b in self.blocks)

    @property
    def char_count(self) -> int:
        return len(self.full_text)

    @property
    def page_count(self) -> int:
        pages = {b.page for b in self.blocks if b.page is not None}
        return len(pages)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    page: int | None
    section: str | None
    char_start: int
    char_end: int
