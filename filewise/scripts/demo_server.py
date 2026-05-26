"""Boot a uvicorn server with SBERT embeddings and pre-loaded fixture docs.

Run with:
    .venv/bin/python scripts/demo_server.py

Then ask questions:
    curl -s http://localhost:8000/ask -H 'content-type: application/json' \
        -d '{"query":"What is the leave policy?"}' | python -m json.tool
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

os.environ.setdefault("FILEWISE_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
os.environ.setdefault("FILEWISE_LLM", "fake:echo")
os.environ.setdefault("FILEWISE_CHUNK_SIZE", "180")
os.environ.setdefault("FILEWISE_CHUNK_OVERLAP", "40")
os.environ.setdefault("FILEWISE_SCORE_THRESHOLD", "0.35")
os.environ.setdefault("FILEWISE_VECTORS_PATH", str(ROOT / ".demo_vectors.pkl"))


def _preload() -> None:
    from fastapi.testclient import TestClient

    from filewise.api.main import create_app

    docs = [
        ("handbook.md", FIXTURES / "handbook.md", "text/markdown"),
        ("handbook.pdf", FIXTURES / "pdf" / "handbook.pdf", "application/pdf"),
        ("security_policy.pdf", FIXTURES / "pdf" / "security_policy.pdf", "application/pdf"),
        ("release_notes.txt", FIXTURES / "release_notes.txt", "text/plain"),
    ]

    print("[demo] embedding model:", os.environ["FILEWISE_EMBED_MODEL"])
    print("[demo] preloading fixtures…")
    t0 = time.time()
    with TestClient(create_app()) as c:
        for name, path, mime in docs:
            r = c.post(
                "/documents",
                files={"file": (name, path.read_bytes(), mime)},
            )
            r.raise_for_status()
            body = r.json()
            print(
                f"  - {name}: pages={body['pages']} chars={body['char_count']} chunks={body['chunks']}"
            )
    print(f"[demo] preload done in {time.time() - t0:.1f}s")


def _serve() -> None:
    import uvicorn

    print("[demo] starting server on http://127.0.0.1:8000")
    print("[demo] try:")
    print(
        "  curl -s http://127.0.0.1:8000/ask -H 'content-type: application/json' "
        "-d '{\"query\":\"What is the leave policy?\"}' | python -m json.tool"
    )
    uvicorn.run(
        "filewise.api.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    if "--no-preload" not in sys.argv:
        _preload()
    _serve()
