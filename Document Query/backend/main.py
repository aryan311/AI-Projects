from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rag import process_document, answer_question, vector_stores
from models import AskRequest
import uuid

from fastapi.responses import FileResponse
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the path to index.html
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")

@app.get("/")
def read_index():
    return FileResponse(FRONTEND_PATH)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm": "Ollama Llama3.1",
        "embedding": "sentence-transformers/all-MiniLM-L6-v2"
    }

@app.post("/upload")
async def upload(file: UploadFile):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=415, detail="Wrong file type. Only .txt files are allowed.")

    try:
        content = (await file.read()).decode("utf-8").strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read file content")

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    doc_id = str(uuid.uuid4())
    try:
        vector_db, total_chunks = process_document(content)
        vector_stores[doc_id] = vector_db
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "total_chunks": total_chunks
    }

@app.post("/ask")
async def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty")

    if req.document_id not in vector_stores:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        answer, sources = answer_question(req.document_id, req.question)
        return {"answer": answer, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM call failed: {str(e)}")
