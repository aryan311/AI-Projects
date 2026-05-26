"""CitationValidator: enforce no-citation-no-answer at the boundary."""

from __future__ import annotations

import logging

from filewise.answer.types import AnswerResult

log = logging.getLogger(__name__)


class CitationValidator:
    def validate(self, result: AnswerResult) -> AnswerResult:
        if result.status == "answered" and not result.citations:
            log.warning("answer downgraded: status=answered but citations empty")
            return AnswerResult(
                status="not_enough_evidence",
                answer=None,
                citations=[],
                max_score=result.max_score,
            )
        return result
