# Document Q&A Web Application

A  single-page web application that allows users to upload `.txt` documents and ask questions based strictly on the document's content using RAG (Retrieval-Augmented Generation).

## Tech Stack

- **Backend**: FastAPI (Python)
- **RAG Framework**: LangChain
- **LLM**: Ollama (Llama 3.1)
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`) - Local
- **Vector Store**: FAISS (In-memory)
- **Frontend**: Vanilla HTML/CSS/JS (Modern Glassmorphism UI)

## Why these models?

- **Ollama (Llama 3.1)**: Runs locally on my machine, providing privacy and no reliance on external API keys.
- **all-MiniLM-L6-v2**: A lightweight, efficient embedding model that runs locally, ensuring low latency and no extra API costs for embeddings.

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- Ollama (running locally with `llama3.1` model)


### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Backend
```bash
cd backend
uvicorn main:app --reload
```
*Note: Ensure the backend is running on `http://localhost:8000`.*

### 4. Run the Frontend
Simply open `frontend/index.html` in your web browser.

## Features
- **Strict Contextual Answering**: The AI will only answer based on the provided document.
- **Source Highlighting**: Displays which chunks of the document were used to generate the answer.

