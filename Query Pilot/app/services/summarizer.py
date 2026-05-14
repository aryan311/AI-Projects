from typing import Any, Dict, List
from app.core.llm import LLMClient
from app.core.config import settings

class Summarizer:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def summarize(self, question: str, sql: str, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "No data found for your question."
        
        try:
            summary = await self.llm_client.summarize_results(question, sql, rows)
            return summary
        except Exception as e:
            # Deterministic fallback if LLM summarization fails
            return f"The query returned {len(rows)} row(s). (Summarization failed: {e})"

    def generate_warnings(self, rows: List[Dict[str, Any]], max_limit: int = settings.max_row_limit) -> List[str]:
        warnings = []
        if len(rows) == 0:
            warnings.append("The query returned an empty result set.")
        elif len(rows) >= max_limit:
            warnings.append(f"Results may be truncated. A maximum limit of {max_limit} rows was enforced.")
        return warnings
