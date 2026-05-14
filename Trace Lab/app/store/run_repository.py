import json
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from app.store.database import get_db


async def create_run(
    run_id: str,
    workflow_name: str,
    trace_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    db: aiosqlite.Connection | None = None,
) -> dict[str, Any]:
    """Insert a new workflow run with status 'running'."""
    conn = db or await get_db()
    now = datetime.now(timezone.utc).isoformat()
    metadata_json = json.dumps(metadata) if metadata else None

    await conn.execute(
        """
        INSERT INTO workflow_runs (id, workflow_name, status, trace_id, start_time, metadata_json)
        VALUES (?, ?, 'running', ?, ?, ?)
        """,
        (run_id, workflow_name, trace_id, now, metadata_json),
    )
    await conn.commit()

    return {
        "id": run_id,
        "workflow_name": workflow_name,
        "status": "running",
        "trace_id": trace_id,
        "start_time": now,
        "end_time": None,
        "error": None,
        "metadata": metadata,
    }


async def complete_run(
    run_id: str,
    status: str,
    error: str | None = None,
    db: aiosqlite.Connection | None = None,
) -> None:
    """Mark a run as completed (success or failed) with end_time."""
    conn = db or await get_db()
    now = datetime.now(timezone.utc).isoformat()

    await conn.execute(
        """
        UPDATE workflow_runs
        SET status = ?, end_time = ?, error = ?
        WHERE id = ?
        """,
        (status, now, error, run_id),
    )
    await conn.commit()


async def get_run(
    run_id: str,
    db: aiosqlite.Connection | None = None,
) -> dict[str, Any] | None:
    """Fetch a single run by ID. Returns None if not found."""
    conn = db or await get_db()
    cursor = await conn.execute(
        "SELECT * FROM workflow_runs WHERE id = ?", (run_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


async def list_runs(
    limit: int = 20,
    offset: int = 0,
    db: aiosqlite.Connection | None = None,
) -> list[dict[str, Any]]:
    """List recent workflow runs ordered by start_time descending."""
    conn = db or await get_db()
    cursor = await conn.execute(
        "SELECT * FROM workflow_runs ORDER BY start_time DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [_row_to_dict(row) for row in rows]


async def count_runs(
    db: aiosqlite.Connection | None = None,
) -> int:
    """Count total workflow runs."""
    conn = db or await get_db()
    cursor = await conn.execute("SELECT COUNT(*) FROM workflow_runs")
    row = await cursor.fetchone()
    return row[0]


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    """Convert an aiosqlite Row to a dict with parsed metadata."""
    d = dict(row)
    # Parse metadata_json back to dict
    raw_meta = d.pop("metadata_json", None)
    d["metadata"] = json.loads(raw_meta) if raw_meta else None
    return d
