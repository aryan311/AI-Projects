"""Document loaders: PDF, TXT, Markdown -> RawDocument."""

from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

from filewise.errors import NoExtractableText, UnsupportedFormat
from filewise.ingestion.types import PageBlock, RawDocument

SUPPORTED_EXTS = {".pdf", ".txt", ".md", ".markdown"}


def load(name: str, data: bytes) -> RawDocument:
    """Dispatch by filename extension."""
    lower = name.lower()
    if lower.endswith(".pdf"):
        return _load_pdf(name, data)
    if lower.endswith((".md", ".markdown")):
        return _load_markdown(name, data.decode("utf-8", errors="replace"))
    if lower.endswith(".txt"):
        return _load_text(name, data.decode("utf-8", errors="replace"))
    raise UnsupportedFormat(f"Unsupported extension for '{name}'. Allowed: pdf, txt, md.")


def _load_pdf(name: str, data: bytes) -> RawDocument:
    try:
        reader = PdfReader(BytesIO(data))
        blocks: list[PageBlock] = []
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.endswith("\n"):
                text += "\n"
            blocks.append(PageBlock(text=text, page=idx))
    except (PdfReadError, PdfStreamError, ValueError) as exc:
        raise UnsupportedFormat(f"Could not parse '{name}' as PDF: {exc}") from exc
    full = "".join(b.text for b in blocks)
    if not full.strip():
        raise NoExtractableText(f"No extractable text in '{name}' (likely scanned PDF).")
    return RawDocument(name=name, blocks=tuple(blocks))


def _load_text(name: str, text: str) -> RawDocument:
    if not text.strip():
        raise NoExtractableText(f"Empty text file '{name}'.")
    return RawDocument(name=name, blocks=(PageBlock(text=text, page=1),))


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _load_markdown(name: str, text: str) -> RawDocument:
    if not text.strip():
        raise NoExtractableText(f"Empty markdown file '{name}'.")
    blocks: list[PageBlock] = []
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return RawDocument(name=name, blocks=(PageBlock(text=text, section=None, page=None),))

    heading_stack: list[tuple[int, str]] = []  # (level, title)
    cursor = 0
    if matches[0].start() > 0:
        blocks.append(PageBlock(text=text[: matches[0].start()], section=None))
        cursor = matches[0].start()

    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip()
        heading_stack = [(lvl, ttl) for (lvl, ttl) in heading_stack if lvl < level]
        heading_stack.append((level, title))
        section = " > ".join(ttl for _, ttl in heading_stack)

        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        blocks.append(PageBlock(text=body, section=section))
        cursor = end

    if cursor < len(text):
        blocks.append(PageBlock(text=text[cursor:], section=blocks[-1].section))

    return RawDocument(name=name, blocks=tuple(blocks))
