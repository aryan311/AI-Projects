from contextlib import asynccontextmanager
import pathlib
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from psycopg import AsyncConnection

from app.core.database import close_pool, get_pool
from app.core.llm import LLMClient
from app.api.models import QueryRequest, QueryResponse, ErrorResponse
from app.api.dependencies import get_db, get_llm_client
from app.services.schema import SchemaService
from app.services.query_pipeline import QueryPipelineService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the connection pool on startup
    await get_pool()
    yield
    # Close the pool on shutdown
    await close_pool()

app = FastAPI(title="QueryPilot", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the interactive web UI."""
    html_path = pathlib.Path(__file__).parent.parent / "static" / "index.html"
    return html_path.read_text()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "OK"}

@app.get("/schema", response_model=dict)
async def get_schema(conn: AsyncConnection = Depends(get_db)):
    """Exposes the database schema discovery for debugging or MCP tool context."""
    try:
        schema_service = SchemaService(conn)
        context = await schema_service.get_schema_context()
        return {"schema": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {str(e)}")

@app.post("/ask", response_model=QueryResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def ask_question(
    request: QueryRequest,
    conn: AsyncConnection = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """
    Takes a natural language question, generates safe read-only SQL against the database,
    executes it with limits, and returns a plain English summary.
    """
    pipeline = QueryPipelineService(conn, llm_client)
    try:
        response = await pipeline.process_question(request)
        return response
    except ValueError as ve:
        # Expected validation or execution limits errors (e.g., unsafe SQL, timeout)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
