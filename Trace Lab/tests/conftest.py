"""
Shared test fixtures for TraceLab tests.
"""

import os
import pytest
import pytest_asyncio
import aiosqlite
from httpx import ASGITransport, AsyncClient

# Disable tracing during tests
os.environ["ENABLE_TRACING"] = "false"

from app.store.database import init_db, close_db, CREATE_TABLE_SQL, CREATE_INDEX_SQL


@pytest_asyncio.fixture
async def test_db(tmp_path):
    """Provide a fresh in-memory SQLite database for each test."""
    db_path = str(tmp_path / "test_tracelab.db")
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute(CREATE_TABLE_SQL)
    await db.execute(CREATE_INDEX_SQL)
    await db.commit()
    yield db
    await db.close()


@pytest_asyncio.fixture
async def test_client():
    """Provide an async test client for the FastAPI app."""
    # Import inside fixture to ensure env vars are set first
    from app.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
