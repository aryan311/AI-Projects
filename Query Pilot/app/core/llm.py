import abc
import json
import httpx
from typing import Any, Dict, List

from app.core.config import settings

class LLMClient(abc.ABC):
    @abc.abstractmethod
    async def generate_sql(self, schema_context: str, question: str) -> str:
        pass
        
    @abc.abstractmethod
    async def summarize_results(self, question: str, sql: str, rows: List[Dict[str, Any]]) -> str:
        pass

class OllamaLLMClient(LLMClient):
    def __init__(self, base_url: str = settings.ollama_base_url, model: str = settings.llm_model):
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"

    async def _call_ollama(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.generate_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    async def generate_sql(self, schema_context: str, question: str) -> str:
        prompt = f"""You are an expert PostgreSQL developer.
Given the following database schema:

{schema_context}

Write a SQL query that answers the following question:
{question}

Return ONLY the raw SQL query. Do not include any explanations, markdown formatting (like ```sql), or comments.
"""
        sql = await self._call_ollama(prompt)
        # Strip markdown if the model hallucinates it despite instructions
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        return sql.strip()

    async def summarize_results(self, question: str, sql: str, rows: List[Dict[str, Any]]) -> str:
        rows_json = json.dumps(rows, default=str)
        prompt = f"""You are a helpful data analyst. 
The user asked: "{question}"
We ran this SQL query:
{sql}

The database returned these rows:
{rows_json}

Provide a brief, plain English summary of the results. Be concise and direct.
"""
        summary = await self._call_ollama(prompt)
        return summary

class FakeLLMClient(LLMClient):
    """For unit testing without needing Ollama."""
    
    async def generate_sql(self, schema_context: str, question: str) -> str:
        # A simple deterministic mapping for tests
        if "top" in question.lower() and "revenue" in question.lower():
            return "SELECT c.name, SUM(o.total_amount) AS revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY revenue DESC LIMIT 5"
        return "SELECT 1"

    async def summarize_results(self, question: str, sql: str, rows: List[Dict[str, Any]]) -> str:
        return f"Fake summary for {len(rows)} rows."
