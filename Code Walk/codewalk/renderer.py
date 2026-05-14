"""Markdown report renderer for CodeWalk.

Converts a Report into a well-structured Markdown document with
module overview, imports, functions, classes, warnings, and
suggested tests.
"""

from __future__ import annotations

from codewalk.models import ClassInfo, FunctionInfo, Report


def _render_module_overview(report: Report) -> str:
    """Render the module overview section."""
    pr = report.parse_result
    lines = [
        f"# Module: `{pr.module_name}`",
        "",
        "## Overview",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Imports | {len(pr.imports)} |",
        f"| Functions | {len(pr.functions)} |",
        f"| Classes | {len(pr.classes)} |",
        f"| Warnings | {len(report.analysis_result.warnings)} |",
        "",
    ]
    return "\n".join(lines)


def _render_imports(report: Report) -> str:
    """Render the imports section."""
    pr = report.parse_result
    if not pr.imports:
        return ""

    lines = [
        "##  Imports",
        "",
        "| Module | Name | Alias | Line |",
        "|--------|------|-------|------|",
    ]

    for imp in pr.imports:
        from_mod = imp.from_module or "—"
        alias = imp.alias or "—"
        lines.append(f"| `{from_mod}` | `{imp.name}` | `{alias}` | {imp.line} |")

    lines.append("")
    return "\n".join(lines)


def _render_function(func: FunctionInfo, prefix: str = "") -> str:
    """Render a single function/method block."""
    name_display = f"{prefix}{func.name}" if prefix else func.name
    async_marker = "async " if func.is_async else ""

    lines = [
        f"### `{async_marker}def {name_display}()`",
        "",
        f"- **Line**: {func.line}–{func.end_line}",
        f"- **Body length**: {func.body_length} lines",
    ]

    if func.decorators:
        decs = ", ".join(f"`@{d}`" for d in func.decorators)
        lines.append(f"- **Decorators**: {decs}")

    if func.return_annotation:
        lines.append(f"- **Returns**: `{func.return_annotation}`")

    if func.docstring:
        lines.append(f"- **Docstring**: {func.docstring}")

    if func.args:
        lines.append("")
        lines.append("**Arguments:**")
        lines.append("")
        lines.append("| Name | Type | Default |")
        lines.append("|------|------|---------|")
        for arg in func.args:
            ann = f"`{arg.annotation}`" if arg.annotation else "—"
            default = f"`{arg.default}`" if arg.default else "—"
            lines.append(f"| `{arg.name}` | {ann} | {default} |")

    lines.append("")
    return "\n".join(lines)


def _render_functions(report: Report) -> str:
    """Render all top-level functions."""
    pr = report.parse_result
    if not pr.functions:
        return ""

    lines = ["## ⚡ Functions", ""]
    for func in pr.functions:
        lines.append(_render_function(func))

    return "\n".join(lines)


def _render_classes(report: Report) -> str:
    """Render all classes with their methods."""
    pr = report.parse_result
    if not pr.classes:
        return ""

    lines = ["##  Classes", ""]

    for cls in pr.classes:
        lines.append(f"### `class {cls.name}`")
        lines.append("")
        lines.append(f"- **Line**: {cls.line}–{cls.end_line}")

        if cls.bases:
            bases = ", ".join(f"`{b}`" for b in cls.bases)
            lines.append(f"- **Inherits from**: {bases}")

        if cls.decorators:
            decs = ", ".join(f"`@{d}`" for d in cls.decorators)
            lines.append(f"- **Decorators**: {decs}")

        if cls.docstring:
            lines.append(f"- **Docstring**: {cls.docstring}")

        lines.append("")

        if cls.methods:
            lines.append("**Methods:**")
            lines.append("")
            for method in cls.methods:
                lines.append(_render_function(method, prefix=f"{cls.name}."))

    return "\n".join(lines)


def _render_warnings(report: Report) -> str:
    """Render the warnings section."""
    warnings = report.analysis_result.warnings
    if not warnings:
        return "## ✅ No Warnings\n\nNo maintainability issues detected.\n"

    severity_icons = {
        "warning": "⚠️",
        "info": "ℹ️",
        "error": "🚨",
    }

    lines = [
        f"## ⚠️ Warnings ({len(warnings)})",
        "",
        "| Severity | Type | Line | Message |",
        "|----------|------|------|---------|",
    ]

    for w in warnings:
        icon = severity_icons.get(w.severity, "⚠️")
        lines.append(f"| {icon} {w.severity} | `{w.type}` | {w.line} | {w.message} |")

    lines.append("")
    return "\n".join(lines)


def _suggest_tests(report: Report) -> str:
    """Generate test suggestions based on parsed structure."""
    pr = report.parse_result
    lines = ["## 🧪 Suggested Tests", ""]

    suggestions = []

    for func in pr.functions:
        suggestions.append(
            f"- [ ] `test_{func.name}` — verify `{func.name}()` returns expected output"
        )
        if func.args:
            suggestions.append(
                f"- [ ] `test_{func.name}_with_defaults` — test default argument behavior"
            )

    for cls in pr.classes:
        suggestions.append(
            f"- [ ] `test_{cls.name.lower()}_creation` — verify `{cls.name}` can be instantiated"
        )
        for method in cls.methods:
            if method.name.startswith("_") and method.name != "__init__":
                continue
            if method.name == "__init__":
                suggestions.append(
                    f"- [ ] `test_{cls.name.lower()}_init` — verify constructor sets attributes"
                )
            else:
                suggestions.append(
                    f"- [ ] `test_{cls.name.lower()}_{method.name}` — verify `{cls.name}.{method.name}()` behavior"
                )

    if not suggestions:
        lines.append("No functions or classes found to suggest tests for.")
    else:
        lines.extend(suggestions)

    lines.append("")
    return "\n".join(lines)


def _render_llm_explanation(report: Report) -> str:
    """Render the optional LLM explanation section."""
    if not report.llm_explanation:
        return ""

    lines = [
        "## 🤖 AI Explanation",
        "",
        "> **Note**: The following explanation was generated by an LLM using",
        "> the AST-extracted facts above. It is provided for readability only.",
        "",
        report.llm_explanation,
        "",
    ]
    return "\n".join(lines)


def render(report: Report) -> str:
    """Render a complete Markdown report.

    Args:
        report: The Report containing parse results, analysis, and optional LLM output.

    Returns:
        A complete Markdown string ready to be written to a file.
    """
    sections = [
        _render_module_overview(report),
        _render_imports(report),
        _render_functions(report),
        _render_classes(report),
        _render_warnings(report),
        _suggest_tests(report),
        _render_llm_explanation(report),
    ]

    # Filter out empty sections and join
    return "\n---\n\n".join(section for section in sections if section)
