import os
from typing import AsyncGenerator
from psycopg import AsyncConnection

from app.core.database import get_db_connection
from app.core.llm import LLMClient, OllamaLLMClient, FakeLLMClient

async def get_db() -> AsyncGenerator[AsyncConnection, None]:
    async with get_db_connection() as conn:
        yield conn

def get_llm_client() -> LLMClient:
    """
    Returns the appropriate LLM client based on environment.
    Use USE_FAKE_LLM=1 for tests.
    """
    if os.getenv("USE_FAKE_LLM") == "1":
        return FakeLLMClient()
    return OllamaLLMClient()
