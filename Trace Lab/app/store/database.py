import aiosqlite
from app.core.config import settings

# Global database connection reference
_db: aiosqlite.Connection | None = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    trace_id TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    error TEXT,
    metadata_json TEXT
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_workflow_runs_start_time
ON workflow_runs (start_time DESC);
"""


async def init_db(db_path: str | None = None) -> aiosqlite.Connection:
    """Initialize the SQLite database and create tables if needed."""
    global _db
    path = db_path or settings.sqlite_db_path
    _db = await aiosqlite.connect(path)
    _db.row_factory = aiosqlite.Row
    await _db.execute(CREATE_TABLE_SQL)
    await _db.execute(CREATE_INDEX_SQL)
    await _db.commit()
    return _db


async def get_db() -> aiosqlite.Connection:
    """Return the current database connection, initializing if needed."""
    global _db
    if _db is None:
        _db = await init_db()
    return _db


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
