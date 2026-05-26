# FileWise

FileWise is a citation-first RAG chatbot for uploaded files. It answers questions from documents and links every answer to source snippets.

## Why This Project Exists

Generic RAG chatbots are everywhere. FileWise is only worth building if it is evidence-first: no citation, no confident answer.

## Hiring Signal

FileWise proves:

- document parsing
- chunking
- embeddings
- vector retrieval
- answer grounding
- failure handling
- retrieval tests

## Core User Story

As a user, I can upload a PDF handbook, ask "What is the leave policy?", and receive an answer with source citations.

## MVP Features

- upload PDF, TXT, or Markdown
- extract text
- chunk text with metadata
- embed chunks
- retrieve relevant chunks
- answer with citations
- return "not enough evidence" when retrieval is weak
- test retrieval against fixtures

## Stretch Features

- multiple collections
- chunking strategy comparison
- retrieval evaluation report
- OpenTelemetry spans
- simple Streamlit UI

## Architecture

```text
Upload
  -> DocumentLoader
  -> Chunker
  -> EmbeddingService
  -> VectorStore
  -> Retriever
  -> Answerer
  -> CitationValidator
```

## Citation Rule

Every answer must include:

- document name
- page or section
- snippet
- relevance score

If no chunk passes the threshold, the system must say it does not have enough evidence.

## Testing Strategy

- chunker tests
- metadata preservation tests
- retrieval tests with fixture documents
- citation validator tests
- API tests for weak retrieval

## Interview Story

I learned that RAG quality depends more on chunking, retrieval, metadata, and citation discipline than the final answer prompt.

## Resume Bullet

Built a citation-first RAG chatbot in Python with document parsing, chunking, vector retrieval, grounded answers, and retrieval regression tests.

---

## Quickstart

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Run the API (offline defaults: fake embeddings + fake LLM)
make run

# In another terminal:
¸
curl -s http://localhost:8000/ask \
  -H "content-type: application/json" \
  -d '{"query":"What is the leave policy?"}' | python -m json.tool
```

A confident answer looks like:

```json
{
  "status": "answered",
  "answer": "Based on [1]: Employees receive 21 days paid leave annually.",
  "citations": [
    {"doc": "handbook.md", "section": "Acme Employee Handbook > Leave Policy", "score": 0.74, "snippet": "..."}
  ],
  "retrieval": {"k": 5, "threshold": 0.35, "max_score": 0.74}
}
```

A refusal looks like:

```json
{
  "status": "not_enough_evidence",
  "answer": null,
  "citations": [],
  "retrieval": {"k": 5, "threshold": 0.35, "max_score": 0.12},
  "hint": "No chunk crossed the score threshold. Try rephrasing or upload more docs."
}
```

## Configuration

All knobs are env vars. Defaults run offline with zero paid API keys.

| Variable | Default | Purpose |
|---|---|---|
| `FILEWISE_EMBED_MODEL` | `fake` | `fake` (tests) or an SBERT model id (requires `pip install .[sbert]`) |
| `FILEWISE_LLM` | `fake:echo` | `fake:echo` only in v0.1.0 (real LLMs land in a later slice) |
| `FILEWISE_CHUNK_SIZE` | `800` | Char-window per chunk |
| `FILEWISE_CHUNK_OVERLAP` | `120` | Char overlap between chunks |
| `FILEWISE_RETRIEVAL_K` | `5` | Top-k chunks per query |
| `FILEWISE_SCORE_THRESHOLD` | `0.35` | Below this → `not_enough_evidence` |
| `FILEWISE_VECTORS_PATH` | `./vectors.npy` | Persisted vector store pickle |
| `FILEWISE_MAX_UPLOAD_BYTES` | `26214400` | 25 MB upload cap |

## How It Stays Honest

- `CitationValidator` (`src/filewise/answer/validator.py`) downgrades any
  "answered" result with empty citations to `not_enough_evidence`.
- Retrieval below threshold short-circuits *before* the LLM is invoked.
- `tests/fixtures/handbook_questions.yaml` is the regression net: known
  questions must return expected substrings, and a deliberately-unanswerable
  question must produce a refusal. CI runs offline (no network).

## Testing

```bash
make test          # full suite
make lint          # ruff
make type          # mypy --strict
```

CI matrix: Python 3.11 + 3.12, `FILEWISE_EMBED_MODEL=fake`, `FILEWISE_LLM=fake:echo`.


