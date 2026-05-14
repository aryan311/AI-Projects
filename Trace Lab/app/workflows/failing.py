"""
Deliberately failing workflow for testing error observability.

This workflow simulates a pipeline that fails during SQL validation,
demonstrating how TraceLab captures error spans, error metadata,
and failure points in the trace UI.
"""

import asyncio
import logging

from app.core.telemetry import traced_step
from app.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)


class FailingWorkflow(BaseWorkflow):
    """
    A workflow designed to fail at the SQL validation step.

    Useful for demonstrating:
    - Error spans in Jaeger
    - Failed run records in the run store
    - How TraceLab captures the exact failure point
    """

    @property
    def name(self) -> str:
        return "failing"

    async def execute(self, question: str, **kwargs) -> dict:
        workflow_name = self.name

        # Step 1: Request Received (succeeds)
        async with traced_step("request_received", workflow_name, {
            "tracelab.question": question,
        }):
            await asyncio.sleep(0.02)

        # Step 2: Schema Discovery (succeeds)
        async with traced_step("schema_discovery", workflow_name) as span:
            await asyncio.sleep(0.1)
            span.set_attribute("tracelab.schema_tables", 4)

        # Step 3: Prompt Build (succeeds)
        async with traced_step("prompt_build", workflow_name) as span:
            await asyncio.sleep(0.01)
            span.set_attribute("tracelab.prompt_length", 200)

        # Step 4: LLM SQL Generation (succeeds but returns unsafe SQL)
        async with traced_step("llm_sql_generation", workflow_name) as span:
            await asyncio.sleep(0.3)  # Simulate LLM latency
            unsafe_sql = "DROP TABLE customers; --"
            span.set_attribute("tracelab.generated_sql", unsafe_sql)
            span.set_attribute("tracelab.llm_model", "llama3.1:latest")

        # Step 5: SQL Validation (FAILS — unsafe SQL detected)
        async with traced_step("sql_validation", workflow_name) as span:
            span.set_attribute("tracelab.input_sql", unsafe_sql)
            span.set_attribute("tracelab.validation_passed", False)
            raise ValueError(
                "SQL validation failed: mutating operations (DROP TABLE) are not allowed. "
                "Only SELECT statements are permitted."
            )

        # These steps are never reached
        # Step 6: DB Execution
        # Step 7: Result Summarization
