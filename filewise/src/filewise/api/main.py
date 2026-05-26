"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from filewise import __version__
from filewise.answer.types import Citation
from filewise.answer.validator import CitationValidator
from filewise.api.schemas import (
    AskRequest,
    AskResponse,
    CitationModel,
    DocumentResponse,
    ErrorResponse,
    RetrievalInfo,
)
from filewise.api.state import AppState
from filewise.config import Config
from filewise.errors import FileTooLarge, FileWiseError

log = logging.getLogger("filewise")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    cfg = Config.from_env()
    app.state.app_state = AppState(cfg)
    log.info(
        "filewise.startup",
        extra={"embed_model": app.state.app_state.embedder.name, "llm": cfg.llm},
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FileWise", version=__version__, lifespan=_lifespan)

    @app.exception_handler(FileWiseError)
    async def _handle_filewise_error(_: Request, exc: FileWiseError) -> JSONResponse:
        body = ErrorResponse(error=exc.code, detail=str(exc) or None).model_dump(exclude_none=True)
        return JSONResponse(status_code=exc.http_status, content=body)

    @app.get("/healthz")
    def healthz(request: Request) -> dict[str, str]:
        state: AppState | None = getattr(request.app.state, "app_state", None)
        return {
            "status": "ok",
            "version": __version__,
            "embedder": state.embedder.name if state else "",
            "llm": state.config.llm if state else "",
        }

    UI_INDEX = Path(__file__).parent.parent / "ui" / "index.html"

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(UI_INDEX, media_type="text/html")

    @app.get("/documents")
    def list_documents(request: Request) -> dict[str, list[dict[str, int | str]]]:
        state: AppState = request.app.state.app_state
        return {
            "documents": [
                {
                    "document_id": d.document_id,
                    "name": d.name,
                    "pages": d.pages,
                    "char_count": d.char_count,
                    "chunks": d.chunks,
                }
                for d in state.list_docs()
            ]
        }

    @app.post("/documents", response_model=DocumentResponse, status_code=201)
    async def upload(
        request: Request,
        file: UploadFile = File(...),  # noqa: B008
    ) -> DocumentResponse:
        state: AppState = request.app.state.app_state
        data = await file.read()
        if len(data) > state.config.max_upload_bytes:
            raise FileTooLarge(
                f"file is {len(data)} bytes; max is {state.config.max_upload_bytes}"
            )
        record = state.ingest(file.filename or "untitled", data)
        return DocumentResponse(
            document_id=record.document_id,
            name=record.name,
            pages=record.pages,
            char_count=record.char_count,
            chunks=record.chunks,
            embedding_model=state.embedder.name,
        )

    @app.get("/documents/{doc_id}", response_model=DocumentResponse)
    def get_document(doc_id: str, request: Request) -> DocumentResponse:
        state: AppState = request.app.state.app_state
        record = state.get_doc(doc_id)
        return DocumentResponse(
            document_id=record.document_id,
            name=record.name,
            pages=record.pages,
            char_count=record.char_count,
            chunks=record.chunks,
            embedding_model=state.embedder.name,
        )

    @app.delete("/documents/{doc_id}", status_code=204)
    def delete_document(doc_id: str, request: Request) -> None:
        state: AppState = request.app.state.app_state
        state.delete_doc(doc_id)

    @app.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest, request: Request) -> AskResponse:
        state: AppState = request.app.state.app_state
        k = req.k or state.config.retrieval_k
        threshold = req.threshold if req.threshold is not None else state.config.score_threshold
        answerer = state.answerer
        if req.k is not None or req.threshold is not None:
            from filewise.answer.answerer import Answerer

            answerer = Answerer(
                state.retriever, state.llm, CitationValidator(),
                threshold=threshold, k=k,
            )
        result = answerer.answer(req.query, state.doc_name_map())
        log.info(
            "filewise.ask",
            extra={
                "status": result.status,
                "k": k,
                "threshold": threshold,
                "max_score": round(result.max_score, 4),
                "n_citations": len(result.citations),
            },
        )
        return AskResponse(
            status=result.status,
            answer=result.answer,
            citations=[_to_model(c) for c in result.citations],
            retrieval=RetrievalInfo(k=k, threshold=threshold, max_score=result.max_score),
            hint=(
                "No chunk crossed the score threshold. Try rephrasing or upload more docs."
                if result.status == "not_enough_evidence"
                else None
            ),
        )

    @app.exception_handler(HTTPException)
    async def _http_exc_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": "http_error", "detail": exc.detail})

    return app


def _to_model(c: Citation) -> CitationModel:
    return CitationModel(
        doc=c.doc, page=c.page, section=c.section, snippet=c.snippet, score=c.score
    )


app = create_app()
