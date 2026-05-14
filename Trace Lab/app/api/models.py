from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- Run Schemas ---


class RunResponse(BaseModel):
    """Schema for a single workflow run."""

    id: str
    workflow_name: str
    status: str
    trace_id: str | None = None
    start_time: str
    end_time: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class RunListResponse(BaseModel):
    """Paginated list of workflow runs."""

    runs: list[RunResponse]
    total: int
    limit: int
    offset: int


# --- Workflow Schemas ---


class WorkflowRequest(BaseModel):
    """Request to trigger a workflow execution."""

    workflow_name: str = Field(
        ...,
        description="Name of the workflow to run: 'querypilot' or 'failing'",
        examples=["querypilot"],
    )
    question: str = Field(
        default="Show the top 5 customers by revenue",
        description="Natural language question for LLM workflows",
    )
    should_fail: bool = Field(
        default=False,
        description="Force workflow failure for testing",
    )


class WorkflowResponse(BaseModel):
    """Response after triggering a workflow."""

    run_id: str
    trace_id: str | None = None
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    jaeger_url: str | None = Field(
        default=None,
        description="Direct link to view this trace in Jaeger UI",
    )
