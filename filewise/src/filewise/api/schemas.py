"""Pydantic request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    document_id: str
    name: str
    pages: int
    char_count: int
    chunks: int
    embedding_model: str


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int | None = Field(default=None, ge=1, le=50)
    threshold: float | None = Field(default=None, ge=-1.0, le=1.0)


class CitationModel(BaseModel):
    doc: str
    page: int | None = None
    section: str | None = None
    snippet: str
    score: float


class RetrievalInfo(BaseModel):
    k: int
    threshold: float
    max_score: float


class AskResponse(BaseModel):
    status: str
    answer: str | None
    citations: list[CitationModel]
    retrieval: RetrievalInfo
    hint: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
