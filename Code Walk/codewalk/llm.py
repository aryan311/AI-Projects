"""Optional LLM explainer layer using Ollama.

Provides an interface for generating beginner-friendly code explanations
by sending AST-extracted facts (not just raw code) to a local Ollama model.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from codewalk.models import ParseResult

# Default Ollama settings
DEFAULT_MODEL = "llama3.1:latest"
DEFAULT_BASE_URL = "http://localhost:11434"


class Explainer(Protocol):
    """Protocol for code explainers."""

    def explain(self, parse_result: ParseResult, source: str) -> str:
        """Generate an explanation of the code.

        Args:
            parse_result: The structured parse output.
            source: The raw source code.

        Returns:
            A beginner-friendly explanation string.
        """
        ...


class FakeExplainer:
    """A fake explainer that returns a static explanation for testing."""

    def explain(self, parse_result: ParseResult, source: str) -> str:
        """Return a static explanation for testing purposes."""
        return (
            f"This module '{parse_result.module_name}' contains "
            f"{len(parse_result.functions)} function(s) and "
            f"{len(parse_result.classes)} class(es). "
            "This is a fake explanation for testing."
        )


def _build_prompt(parse_result: ParseResult, source: str) -> str:
    """Build a structured prompt using AST facts and source code.

    The prompt provides deterministic structure information first,
    then asks the LLM to explain based on those facts.
    """
    sections = []

    sections.append("You are a helpful coding tutor. Explain the following Python module to a beginner developer.")
    sections.append("Use the structural facts provided below to guide your explanation. Be concise and accurate.")
    sections.append("")

    # Module info
    sections.append(f"## Module: {parse_result.module_name}")
    sections.append("")

    # Imports
    if parse_result.imports:
        sections.append("### Imports:")
        for imp in parse_result.imports:
            if imp.from_module:
                sections.append(f"- from {imp.from_module} import {imp.name}")
            else:
                sections.append(f"- import {imp.name}")
        sections.append("")

    # Functions
    if parse_result.functions:
        sections.append("### Functions:")
        for func in parse_result.functions:
            args_str = ", ".join(
                f"{a.name}: {a.annotation}" if a.annotation else a.name
                for a in func.args
            )
            ret = f" -> {func.return_annotation}" if func.return_annotation else ""
            sections.append(f"- `{func.name}({args_str}){ret}` (line {func.line})")
            if func.docstring:
                sections.append(f"  Docstring: {func.docstring}")
        sections.append("")

    # Classes
    if parse_result.classes:
        sections.append("### Classes:")
        for cls in parse_result.classes:
            bases = f"({', '.join(cls.bases)})" if cls.bases else ""
            sections.append(f"- `class {cls.name}{bases}` (line {cls.line})")
            if cls.docstring:
                sections.append(f"  Docstring: {cls.docstring}")
            for method in cls.methods:
                sections.append(f"  - Method: `{method.name}()`")
        sections.append("")

    # Source code
    sections.append("### Source Code:")
    sections.append("```python")
    sections.append(source.strip())
    sections.append("```")
    sections.append("")

    sections.append(
        "Based on the structural facts and source code above, provide a clear, "
        "beginner-friendly explanation of what this module does. "
        "Cover the purpose, key components, and how they work together. "
        "Format your response in Markdown."
    )

    return "\n".join(sections)


class OllamaExplainer:
    """Explains code using a local Ollama LLM instance.

    Sends AST-extracted facts alongside the source code to produce
    grounded, accurate explanations rather than pure hallucination.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def explain(self, parse_result: ParseResult, source: str) -> str:
        """Generate an explanation using Ollama.

        Args:
            parse_result: The structured parse output.
            source: The raw source code.

        Returns:
            A beginner-friendly explanation string.

        Raises:
            ConnectionError: If Ollama is not reachable.
            RuntimeError: If the LLM request fails.
        """
        prompt = _build_prompt(parse_result, source)

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1024,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama request failed with status {e.response.status_code}: "
                f"{e.response.text}"
            )

        data = response.json()
        return data.get("response", "No explanation generated.")
