"""Typer CLI application for CodeWalk.

Provides `inspect` and `explain` commands for analyzing Python files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from codewalk.analyzer import analyze
from codewalk.llm import DEFAULT_MODEL, OllamaExplainer
from codewalk.models import Report
from codewalk.parser import parse_file
from codewalk.renderer import render

app = typer.Typer(
    name="codewalk",
    help="🚶 CodeWalk — Python code explanation using AST static analysis.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def _validate_python_file(path: Path) -> Path:
    """Validate that the path exists and is a Python file."""
    if not path.exists():
        err_console.print(f"[red]Error:[/red] File not found: {path}")
        raise typer.Exit(code=1)

    if path.suffix != ".py":
        err_console.print(
            f"[red]Error:[/red] Not a Python file: {path} "
            f"(expected .py extension)"
        )
        raise typer.Exit(code=1)

    # Validate syntax
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
    except SyntaxError as e:
        err_console.print(
            f"[red]Error:[/red] Invalid Python syntax in {path}: {e.msg} "
            f"(line {e.lineno})"
        )
        raise typer.Exit(code=1)

    return path


@app.command()
def inspect(
    file: Path = typer.Argument(
        ...,
        help="Path to the Python file to inspect.",
        exists=True,
        readable=True,
    ),
) -> None:
    """Parse a Python file and output its structure as JSON.

    Extracts imports, functions, classes, arguments, decorators,
    docstrings, and line numbers using Python's AST module.
    """
    path = _validate_python_file(file)

    try:
        result = parse_file(path)
    except SyntaxError as e:
        err_console.print(f"[red]Error:[/red] Failed to parse {path}: {e}")
        raise typer.Exit(code=1)

    output = json.dumps(result.model_dump(), indent=2)
    console.print_json(output)


@app.command()
def explain(
    file: Path = typer.Argument(
        ...,
        help="Path to the Python file to explain.",
        exists=True,
        readable=True,
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for the Markdown report.",
    ),
    llm: bool = typer.Option(
        False,
        "--llm",
        help="Enable LLM-powered explanation (requires Ollama).",
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        "-m",
        help="Ollama model to use for LLM explanation.",
    ),
) -> None:
    """Generate a Markdown walkthrough of a Python file.

    Parses the file using AST, runs code quality analysis, generates
    a structured report, and optionally adds an LLM-powered explanation.
    """
    path = _validate_python_file(file)

    # Parse
    with console.status("[bold green]Parsing file..."):
        try:
            parse_result = parse_file(path)
        except SyntaxError as e:
            err_console.print(f"[red]Error:[/red] Failed to parse {path}: {e}")
            raise typer.Exit(code=1)

    # Analyze
    with console.status("[bold yellow]Analyzing code..."):
        source = path.read_text(encoding="utf-8")
        analysis_result = analyze(parse_result, source)

    # Optional LLM explanation
    llm_explanation = None
    if llm:
        with console.status(f"[bold blue]Generating LLM explanation ({model})..."):
            try:
                explainer = OllamaExplainer(model=model)
                llm_explanation = explainer.explain(parse_result, source)
            except ConnectionError as e:
                err_console.print(f"[yellow]Warning:[/yellow] {e}")
                err_console.print("[yellow]Continuing without LLM explanation...[/yellow]")
            except RuntimeError as e:
                err_console.print(f"[yellow]Warning:[/yellow] {e}")
                err_console.print("[yellow]Continuing without LLM explanation...[/yellow]")

    # Build report
    report = Report(
        parse_result=parse_result,
        analysis_result=analysis_result,
        llm_explanation=llm_explanation,
    )

    # Render
    markdown = render(report)

    # Output
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        console.print(
            Panel(
                f"[green]✅ Report written to:[/green] {output}",
                title="CodeWalk",
                border_style="green",
            )
        )
    else:
        console.print(markdown)

    # Summary
    warn_count = len(analysis_result.warnings)
    if warn_count > 0:
        console.print(
            f"\n[yellow]⚠️  {warn_count} warning(s) detected.[/yellow]"
        )
    else:
        console.print("\n[green]✅ No warnings detected.[/green]")


if __name__ == "__main__":
    app()
