import asyncio
from typing import Any, Dict, List
from psycopg import AsyncConnection
from psycopg.errors import Error as PsycopgError

from app.core.config import settings

class QueryExecutor:
    def __init__(self, conn: AsyncConnection, timeout_seconds: float = settings.max_query_timeout_seconds):
        self.conn = conn
        self.timeout_seconds = timeout_seconds

    async def execute(self, sql: str) -> List[Dict[str, Any]]:
        """
        Executes a validated read-only SQL query against the database.
        Includes a timeout to prevent long-running queries.
        Normalizes database errors to prevent leaking internal DB details.
        """
        try:
            async with self.conn.transaction():
                # Set a local statement timeout for this transaction
                timeout_ms = int(self.timeout_seconds * 1000)
                await self.conn.execute(f"SET LOCAL statement_timeout = {timeout_ms};")
                
                async with self.conn.cursor() as cur:
                    await cur.execute(sql)
                    rows = await cur.fetchall()
                    # Convert any non-serializable objects like dates to strings, though
                    # jsonable_encoder or custom Pydantic models usually handle this.
                    # For safety, let's return raw dicts and let the API layer serialize.
                    return [dict(row) for row in rows]
        except asyncio.TimeoutError:
            raise ValueError(f"Query execution timed out after {self.timeout_seconds} seconds.")
        except PsycopgError as e:
            # Hide raw database stack trace, return a generic or safe error message
            # e.g., syntax errors, column not found, etc.
            # We can log the real error `e` internally if logging is set up
            raise ValueError(f"Database error executing query: {str(e).splitlines()[0]}")
        except Exception as e:
            raise ValueError("An unexpected error occurred during query execution.")
