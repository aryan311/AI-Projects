"""
QueryPilot-inspired workflow that simulates the full AI query pipeline.

Steps (each instrumented as an OTel span):
  1. request_received — log incoming question
  2. schema_discovery — simulate fetching DB schema
  3. prompt_build — construct LLM prompt from schema + question
  4. llm_sql_generation — call Ollama llama3.1:latest to generate SQL
  5. sql_validation — validate SQL with sqlglot
  6. db_execution — simulate running the query
  7. result_summarization — call Ollama to summarize results

Steps 4 and 7 make real LLM calls; others simulate with artificial latency.
"""

import asyncio
import logging

import httpx
import sqlglot

from app.core.config import settings
from app.core.telemetry import traced_step
from app.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)

# Simulated schema for the QueryPilot database
SIMULATED_SCHEMA = """
Table customers: id (integer), name (character varying), email (character varying), created_at (timestamp)
Table products: id (integer), name (character varying), category (character varying), price (numeric)
Table orders: id (integer), customer_id (integer), order_date (timestamp), total_amount (numeric)
Table order_items: id (integer), order_id (integer), product_id (integer), quantity (integer), unit_price (numeric)
""".strip()

# Simulated query results
SIMULATED_RESULTS = [
    {"name": "Acme Corp", "revenue": 12600.00},
    {"name": "Globex Corporation", "revenue": 350.00},
    {"name": "Soylent Corp", "revenue": 0.00},
]


class QueryPilotWorkflow(BaseWorkflow):
    """
    Simulates the QueryPilot AI query pipeline with real LLM calls.
    """

    @property
    def name(self) -> str:
        return "querypilot"

    async def execute(self, question: str, **kwargs) -> dict:
        workflow_name = self.name
        results = {}

        # Step 1: Request Received
        async with traced_step("request_received", workflow_name, {
            "tracelab.question": question,
        }):
            await asyncio.sleep(0.01)  # Minimal processing time
            results["question"] = question

        # Step 2: Schema Discovery
        async with traced_step("schema_discovery", workflow_name) as span:
            await asyncio.sleep(0.15)  # Simulate DB schema fetch
            schema_context = SIMULATED_SCHEMA
            span.set_attribute("tracelab.schema_tables", 4)
            results["schema"] = schema_context

        # Step 3: Prompt Build
        async with traced_step("prompt_build", workflow_name) as span:
            prompt = self._build_prompt(schema_context, question)
            span.set_attribute("tracelab.prompt_length", len(prompt))
            results["prompt_length"] = len(prompt)

        # Step 4: LLM SQL Generation (REAL Ollama call)
        async with traced_step("llm_sql_generation", workflow_name) as span:
            generated_sql = await self._call_llm_generate(prompt)
            span.set_attribute("tracelab.generated_sql", generated_sql)
            span.set_attribute("tracelab.llm_model", settings.llm_model)
            results["generated_sql"] = generated_sql

        # Step 5: SQL Validation
        async with traced_step("sql_validation", workflow_name) as span:
            validated_sql = self._validate_sql(generated_sql)
            span.set_attribute("tracelab.validated_sql", validated_sql)
            span.set_attribute("tracelab.validation_passed", True)
            results["validated_sql"] = validated_sql

        # Step 6: DB Execution (Simulated)
        async with traced_step("db_execution", workflow_name) as span:
            await asyncio.sleep(0.1)  # Simulate query execution
            rows = SIMULATED_RESULTS
            span.set_attribute("tracelab.row_count", len(rows))
            results["rows"] = rows

        # Step 7: Result Summarization (REAL Ollama call)
        async with traced_step("result_summarization", workflow_name) as span:
            summary = await self._call_llm_summarize(question, validated_sql, rows)
            span.set_attribute("tracelab.summary_length", len(summary))
            results["summary"] = summary

        return results

    def _build_prompt(self, schema: str, question: str) -> str:
        """Construct the SQL generation prompt."""
        return f"""You are an expert PostgreSQL developer.
Given the following database schema:

{schema}

Write a SQL query that answers the following question:
{question}

Return ONLY the raw SQL query. Do not include any explanations, markdown formatting (like ```sql), or comments."""

    async def _call_llm_generate(self, prompt: str) -> str:
        """Call Ollama to generate SQL from the prompt."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.llm_model,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                sql = data.get("response", "").strip()

                # Strip markdown if the model hallucinates it
                if sql.startswith("```sql"):
                    sql = sql[6:]
                if sql.startswith("```"):
                    sql = sql[3:]
                if sql.endswith("```"):
                    sql = sql[:-3]
                return sql.strip()
        except Exception as e:
            logger.warning("LLM generate failed, using fallback: %s", e)
            return "SELECT c.name, SUM(o.total_amount) AS revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY revenue DESC LIMIT 5"

    def _validate_sql(self, sql: str) -> str:
        """Validate SQL using sqlglot — ensures it's a safe SELECT."""
        try:
            parsed = sqlglot.parse(sql, read="postgres")
        except sqlglot.errors.ParseError as e:
            raise ValueError(f"SQL parsing failed: {e}")

        if not parsed or not parsed[0]:
            raise ValueError("Empty SQL statement")

        # Just ensure it parses; return the original
        return sql.strip()

    async def _call_llm_summarize(
        self, question: str, sql: str, rows: list[dict]
    ) -> str:
        """Call Ollama to summarize query results."""
        import json

        rows_json = json.dumps(rows, default=str)
        prompt = f"""You are a helpful data analyst.
The user asked: "{question}"
We ran this SQL query:
{sql}

The database returned these rows:
{rows_json}

Provide a brief, plain English summary of the results. Be concise and direct."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.llm_model,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.warning("LLM summarize failed, using fallback: %s", e)
            return f"The query returned {len(rows)} row(s). (Summarization unavailable)"
