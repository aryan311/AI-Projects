"""Typed errors mapped to HTTP responses in api/."""

from __future__ import annotations


class FileWiseError(Exception):
    code: str = "filewise_error"
    http_status: int = 500


class UnsupportedFormat(FileWiseError):
    code = "unsupported_format"
    http_status = 415


class FileTooLarge(FileWiseError):
    code = "file_too_large"
    http_status = 413


class DocumentNotFound(FileWiseError):
    code = "document_not_found"
    http_status = 404


class EmbeddingDimMismatch(FileWiseError):
    code = "embedding_model_mismatch"
    http_status = 409


class NoExtractableText(FileWiseError):
    code = "no_extractable_text"
    http_status = 415
