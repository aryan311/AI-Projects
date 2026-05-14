"""
Base workflow class with integrated tracing and run store recording.

All workflows inherit from BaseWorkflow and implement the `execute` method.
The `run` method handles:
  - Creating a run record in SQLite
  - Wrapping execution in a root OTel span
  - Recording success/failure
  - Returning a WorkflowResponse with trace_id
"""

import abc
import logging
import uuid

from app.api.models import WorkflowResponse
from app.core.telemetry import get_tracer, get_current_trace_id
from app.store import run_repository
from opentelemetry.trace import StatusCode

logger = logging.getLogger(__name__)


class BaseWorkflow(abc.ABC):
    """Abstract base class for all instrumented workflows."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique name identifying this workflow."""
        ...

    @abc.abstractmethod
    async def execute(self, question: str, **kwargs) -> dict:
        """
        Execute the workflow logic.

        Returns a dict of result data on success.
        Raises an exception on failure.
        """
        ...

    async def run(self, question: str = "", **kwargs) -> WorkflowResponse:
        """
        Execute the workflow with full tracing and run store integration.

        1. Creates a run record (status=running)
        2. Starts a root OTel span for the workflow
        3. Calls self.execute()
        4. Records success or failure in the run store
        5. Returns a WorkflowResponse
        """
        run_id = str(uuid.uuid4())
        tracer = get_tracer()
        trace_id = None
        result = None
        error_msg = None
        status = "success"

        with tracer.start_as_current_span(
            f"workflow.{self.name}",
            attributes={
                "tracelab.workflow_name": self.name,
                "tracelab.run_id": run_id,
                "tracelab.question": question,
            },
        ) as root_span:
            trace_id = get_current_trace_id()

            # Record the run start
            try:
                await run_repository.create_run(
                    run_id=run_id,
                    workflow_name=self.name,
                    trace_id=trace_id,
                    metadata={"question": question},
                )
            except Exception as e:
                logger.warning("Failed to create run record: %s", e)

            try:
                result = await self.execute(question=question, **kwargs)
                root_span.set_status(StatusCode.OK)
            except Exception as exc:
                status = "failed"
                error_msg = f"{type(exc).__name__}: {str(exc)}"
                root_span.set_status(StatusCode.ERROR, error_msg)
                root_span.record_exception(exc)
                logger.error(
                    "Workflow '%s' failed: %s", self.name, error_msg
                )

            # Record the run completion
            try:
                await run_repository.complete_run(
                    run_id=run_id, status=status, error=error_msg
                )
            except Exception as e:
                logger.warning("Failed to update run record: %s", e)

        # Build Jaeger deep link
        jaeger_url = None
        if trace_id:
            jaeger_url = f"http://localhost:16686/trace/{trace_id}"

        return WorkflowResponse(
            run_id=run_id,
            trace_id=trace_id,
            status=status,
            result=result,
            error=error_msg,
            jaeger_url=jaeger_url,
        )
