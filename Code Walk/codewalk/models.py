"""Data models for CodeWalk parsing, analysis, and reporting."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ImportInfo(BaseModel):
    """Represents a single import statement."""

    name: str
    alias: Optional[str] = None
    from_module: Optional[str] = None
    line: int


class ArgumentInfo(BaseModel):
    """Represents a function argument."""

    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None


class FunctionInfo(BaseModel):
    """Represents a parsed function or method."""

    name: str
    args: list[ArgumentInfo]
    decorators: list[str]
    docstring: Optional[str] = None
    return_annotation: Optional[str] = None
    line: int
    end_line: int
    body_length: int
    is_async: bool = False


class ClassInfo(BaseModel):
    """Represents a parsed class."""

    name: str
    bases: list[str]
    methods: list[FunctionInfo]
    decorators: list[str]
    docstring: Optional[str] = None
    line: int
    end_line: int


class ParseResult(BaseModel):
    """Complete result from parsing a Python file."""

    module_name: str
    imports: list[ImportInfo]
    functions: list[FunctionInfo]
    classes: list[ClassInfo]


class Warning(BaseModel):
    """A code quality warning detected by the analyzer."""

    type: str
    message: str
    line: int
    severity: str = "warning"  # "warning" | "info" | "error"


class AnalysisResult(BaseModel):
    """Result from analyzing parsed code."""

    warnings: list[Warning]


class Report(BaseModel):
    """Complete report combining parse, analysis, and optional LLM explanation."""

    parse_result: ParseResult
    analysis_result: AnalysisResult
    llm_explanation: Optional[str] = None
