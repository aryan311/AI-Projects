import logging

from fastapi import APIRouter, HTTPException

from app.api.models import WorkflowRequest, WorkflowResponse
from app.workflows.querypilot import QueryPilotWorkflow
from app.workflows.failing import FailingWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflows"])

# Registry of available workflows
WORKFLOW_REGISTRY = {
    "querypilot": QueryPilotWorkflow,
    "failing": FailingWorkflow,
}


@router.post("/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    """
    Trigger a named workflow execution.

    The workflow is instrumented with OpenTelemetry spans and
    recorded in the SQLite run store for later inspection.
    """
    # Determine which workflow to run
    workflow_name = request.workflow_name.lower()

    # Override to failing workflow if should_fail is set
    if request.should_fail:
        workflow_name = "failing"

    workflow_cls = WORKFLOW_REGISTRY.get(workflow_name)
    if workflow_cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow '{workflow_name}'. Available: {list(WORKFLOW_REGISTRY.keys())}",
        )

    workflow = workflow_cls()
    result = await workflow.run(question=request.question)
    return result
