"""Public dataclasses for answers + citations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Citation:
    doc: str
    page: int | None
    section: str | None
    snippet: str
    score: float


AnswerStatus = Literal["answered", "not_enough_evidence"]


@dataclass(frozen=True)
class AnswerResult:
    status: AnswerStatus
    answer: str | None
    citations: list[Citation]
    max_score: float
