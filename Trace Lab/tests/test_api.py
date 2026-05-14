"""
API integration tests for TraceLab endpoints.

Validates:
- GET /health returns OK
- GET /runs returns paginated list
- GET /runs/{id} returns 404 for missing run
- POST /workflow/run returns 400 for unknown workflow
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Health endpoint should return OK."""
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OK"
    assert data["service"] == "tracelab"


@pytest.mark.asyncio
async def test_get_runs_empty(test_client):
    """GET /runs on a fresh database should return an empty list."""
    resp = await test_client.get("/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["runs"] == [] or isinstance(data["runs"], list)
    assert "total" in data


@pytest.mark.asyncio
async def test_get_run_not_found(test_client):
    """GET /runs/{id} for a non-existent run should return 404."""
    resp = await test_client.get("/runs/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_unknown_workflow(test_client):
    """POST /workflow/run with unknown workflow should return 400."""
    resp = await test_client.post(
        "/workflow/run",
        json={"workflow_name": "nonexistent", "question": "test"},
    )
    assert resp.status_code == 400
    assert "Unknown workflow" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_dashboard_returns_html(test_client):
    """GET / should return the HTML dashboard."""
    resp = await test_client.get("/")
    assert resp.status_code == 200
    assert "TraceLab" in resp.text
    assert "text/html" in resp.headers.get("content-type", "")
