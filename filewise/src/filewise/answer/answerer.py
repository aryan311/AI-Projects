"""Orchestrates retrieve -> LLM -> validator into an AnswerResult."""

from __future__ import annotations

import re

from filewise.answer.llm import LLM
from filewise.answer.types import AnswerResult, Citation
from filewise.answer.validator import CitationValidator
from filewise.retrieval.retriever import Retriever
from filewise.store.base import ScoredChunk

SYSTEM_PROMPT = (
    "You are a document Q&A assistant. Answer ONLY from the provided context. "
    "Cite sources by their bracketed number, e.g. [1], [2]. "
    "If the context does not contain the answer, say you don't have enough evidence."
)

_CITATION_RE = re.compile(r"\[(\d+)\]")
SNIPPET_MAX = 200


class Answerer:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLM,
        validator: CitationValidator,
        *,
        threshold: float,
        k: int,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._validator = validator
        self._threshold = threshold
        self._k = k

    def answer(self, query: str, doc_name_by_id: dict[str, str]) -> AnswerResult:
        retrieval = self._retriever.search(query, k=self._k, threshold=self._threshold)
        hits = retrieval.hits
        max_score = retrieval.raw_top_score
        if not hits:
            return AnswerResult(
                status="not_enough_evidence", answer=None, citations=[], max_score=max_score
            )

        user_prompt = _build_user_prompt(query, hits)
        text = self._llm.generate(SYSTEM_PROMPT, user_prompt).strip()
        cited_indices = _extract_cited_indices(text, n=len(hits))
        citations = [
            _to_citation(hits[i], doc_name_by_id.get(hits[i].chunk.doc_id, hits[i].chunk.doc_id))
            for i in cited_indices
        ]
        answer = AnswerResult(
            status="answered" if text else "not_enough_evidence",
            answer=text if text else None,
            citations=citations,
            max_score=max_score,
        )
        return self._validator.validate(answer)


def _build_user_prompt(query: str, hits: list[ScoredChunk]) -> str:
    lines = ["Context chunks:"]
    for i, h in enumerate(hits, start=1):
        lines.append(f"[{i}] {h.chunk.text.strip()}")
    lines.append("")
    lines.append(f"Question: {query}")
    return "\n".join(lines)


def _extract_cited_indices(text: str, n: int) -> list[int]:
    seen: list[int] = []
    for match in _CITATION_RE.finditer(text):
        idx = int(match.group(1)) - 1
        if 0 <= idx < n and idx not in seen:
            seen.append(idx)
    return seen


def _to_citation(hit: ScoredChunk, doc_name: str) -> Citation:
    snippet = hit.chunk.text.strip()
    if len(snippet) > SNIPPET_MAX:
        snippet = snippet[: SNIPPET_MAX - 1].rstrip() + "…"
    return Citation(
        doc=doc_name,
        page=hit.chunk.page,
        section=hit.chunk.section,
        snippet=snippet,
        score=hit.score,
    )
