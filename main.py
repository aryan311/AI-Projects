from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from agents.research import research_executor
from agents.normalize import normalize_executor
from agents.summary import summary_executor
from agents.editor import editor_executor

# We will import the pipeline endpoint here
from pipeline import router as pipeline_router

app = FastAPI(title="NewsRoom Agents API")

# Agent Execute Endpoints
@app.post("/agents/research/execute")
async def execute_research(request: Request):
    payload = await request.json()
    return research_executor.execute(payload)

@app.post("/agents/normalize/execute")
async def execute_normalize(request: Request):
    payload = await request.json()
    return normalize_executor.execute(payload)

@app.post("/agents/summary/execute")
async def execute_summary(request: Request):
    payload = await request.json()
    return summary_executor.execute(payload)

@app.post("/agents/editor/execute")
async def execute_editor(request: Request):
    payload = await request.json()
    return editor_executor.execute(payload)

# Agent Cards
@app.get("/.well-known/agent-card.json")
def get_agent_cards():
    return {
        "agents": [
            {"name": "ResearchAgent", "description": "Fetches news RSS based on topic", "url": "http://localhost:8000/agents/research"},
            {"name": "NormalizeAgent", "description": "Normalizes and deduplicates articles", "url": "http://localhost:8000/agents/normalize"},
            {"name": "SummaryAgent", "description": "Summarizes articles", "url": "http://localhost:8000/agents/summary"},
            {"name": "EditorAgent", "description": "Compiles final briefing", "url": "http://localhost:8000/agents/editor"}
        ]
    }

# Include pipeline router
app.include_router(pipeline_router)

# Mount UI (Static files)
# We will create the UI in the static/ folder
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
