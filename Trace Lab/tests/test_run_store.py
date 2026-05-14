"""
Tests for the SQLite run store (run_repository).

Validates:
- Creating runs with correct initial state
- Completing runs with success/failure status
- Listing runs with pagination
- Getting individual runs by ID
- Handling missing runs
"""

import pytest
from app.store.run_repository import create_run, complete_run, get_run, list_runs, count_runs


@pytest.mark.asyncio
async def test_create_run_success(test_db):
    """A new run should be created with status 'running'."""
    run = await create_run(
        run_id="test-001",
        workflow_name="querypilot",
        trace_id="abc123",
        metadata={"question": "test question"},
        db=test_db,
    )
    assert run["id"] == "test-001"
    assert run["workflow_name"] == "querypilot"
    assert run["status"] == "running"
    assert run["trace_id"] == "abc123"
    assert run["start_time"] is not None
    assert run["end_time"] is None
    assert run["error"] is None
    assert run["metadata"]["question"] == "test question"


@pytest.mark.asyncio
async def test_complete_run_success(test_db):
    """Completing a run with status 'success' sets end_time and no error."""
    await create_run(run_id="test-002", workflow_name="querypilot", db=test_db)
    await complete_run(run_id="test-002", status="success", db=test_db)

    run = await get_run("test-002", db=test_db)
    assert run["status"] == "success"
    assert run["end_time"] is not None
    assert run["error"] is None


@pytest.mark.asyncio
async def test_complete_run_failure(test_db):
    """Completing a run with status 'failed' records the error message."""
    await create_run(run_id="test-003", workflow_name="failing", db=test_db)
    await complete_run(
        run_id="test-003",
        status="failed",
        error="ValueError: unsafe SQL detected",
        db=test_db,
    )

    run = await get_run("test-003", db=test_db)
    assert run["status"] == "failed"
    assert run["end_time"] is not None
    assert "unsafe SQL" in run["error"]


@pytest.mark.asyncio
async def test_get_run_not_found(test_db):
    """Getting a non-existent run returns None."""
    run = await get_run("nonexistent-id", db=test_db)
    assert run is None


@pytest.mark.asyncio
async def test_list_runs_ordering(test_db):
    """Runs should be listed in reverse chronological order."""
    import asyncio

    await create_run(run_id="run-a", workflow_name="w1", db=test_db)
    await asyncio.sleep(0.01)  # Ensure different timestamps
    await create_run(run_id="run-b", workflow_name="w2", db=test_db)
    await asyncio.sleep(0.01)
    await create_run(run_id="run-c", workflow_name="w3", db=test_db)

    runs = await list_runs(limit=10, offset=0, db=test_db)
    assert len(runs) == 3
    # Most recent first
    assert runs[0]["id"] == "run-c"
    assert runs[2]["id"] == "run-a"


@pytest.mark.asyncio
async def test_list_runs_pagination(test_db):
    """Pagination should limit and offset results correctly."""
    for i in range(5):
        await create_run(run_id=f"page-{i}", workflow_name="test", db=test_db)

    page1 = await list_runs(limit=2, offset=0, db=test_db)
    page2 = await list_runs(limit=2, offset=2, db=test_db)
    page3 = await list_runs(limit=2, offset=4, db=test_db)

    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 1


@pytest.mark.asyncio
async def test_count_runs(test_db):
    """Count should reflect total number of runs."""
    assert await count_runs(db=test_db) == 0
    await create_run(run_id="c-1", workflow_name="test", db=test_db)
    await create_run(run_id="c-2", workflow_name="test", db=test_db)
    assert await count_runs(db=test_db) == 2
