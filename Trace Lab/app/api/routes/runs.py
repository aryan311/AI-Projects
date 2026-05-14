from fastapi import APIRouter, HTTPException, Query

from app.api.models import RunResponse, RunListResponse
from app.store import run_repository

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=RunListResponse)
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100, description="Max runs to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """List recent workflow runs with pagination."""
    runs = await run_repository.list_runs(limit=limit, offset=offset)
    total = await run_repository.count_runs()
    return RunListResponse(
        runs=[RunResponse(**r) for r in runs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    """Get a single workflow run by ID."""
    run = await run_repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return RunResponse(**run)
