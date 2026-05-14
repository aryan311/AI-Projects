from contextlib import asynccontextmanager
from typing import AsyncGenerator
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.core.config import settings

# Global pool instance
pool: AsyncConnectionPool | None = None

async def get_pool() -> AsyncConnectionPool:
    global pool
    if pool is None:
        pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row}
        )
    return pool

async def close_pool():
    global pool
    if pool is not None:
        await pool.close()
        pool = None

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Provide a transactional scope around a series of operations."""
    p = await get_pool()
    async with p.connection() as conn:
        yield conn
