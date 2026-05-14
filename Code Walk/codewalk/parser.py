"""AST parser for Python source files.

Extracts imports, functions, classes, arguments, decorators,
docstrings, and line numbers from a Python file.
"""

from __future__ import annotations

import ast
from pathlib import Path

from codewalk.models import (
    ArgumentInfo,
    ClassInfo,
    FunctionInfo,
    ImportInfo,
    ParseResult,
)


def _get_docstring(node: ast.AST) -> str | None:
    """Extract docstring from a function or class node."""
    return ast.get_docstring(node)


def _get_decorator_names(node: ast.FunctionDef | ast.ClassDef) -> list[str]:
    """Extract decorator names as strings."""
    decorators = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            # e.g. @module.decorator
            parts = []
            current = dec
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            decorators.append(".".join(reversed(parts)))
        elif isinstance(dec, ast.Call):
            # e.g. @decorator(args)
            if isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
            elif isinstance(dec.func, ast.Attribute):
                parts = []
                current = dec.func
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                decorators.append(".".join(reversed(parts)))
        else:
            decorators.append("<complex_decorator>")
    return decorators


def _get_annotation_str(node: ast.expr | None) -> str | None:
    """Convert an annotation AST node to a string representation."""
    if node is None:
        return None
    return ast.unparse(node)


def _parse_arguments(args: ast.arguments) -> list[ArgumentInfo]:
    """Parse function arguments into ArgumentInfo list."""
    result = []

    # Compute defaults alignment: defaults are right-aligned to args
    num_args = len(args.args)
    num_defaults = len(args.defaults)
    default_offset = num_args - num_defaults

    for i, arg in enumerate(args.args):
        # Skip 'self' and 'cls' for methods
        if arg.arg in ("self", "cls"):
            continue

        annotation = _get_annotation_str(arg.annotation)

        default = None
        default_index = i - default_offset
        if default_index >= 0 and default_index < len(args.defaults):
            default = ast.unparse(args.defaults[default_index])

        result.append(
            ArgumentInfo(name=arg.arg, annotation=annotation, default=default)
        )

    # *args
    if args.vararg:
        result.append(
            ArgumentInfo(
                name=f"*{args.vararg.arg}",
                annotation=_get_annotation_str(args.vararg.annotation),
            )
        )

    # **kwargs
    if args.kwarg:
        result.append(
            ArgumentInfo(
                name=f"**{args.kwarg.arg}",
                annotation=_get_annotation_str(args.kwarg.annotation),
            )
        )

    return result


def _parse_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> FunctionInfo:
    """Parse a function/method definition node."""
    return FunctionInfo(
        name=node.name,
        args=_parse_arguments(node.args),
        decorators=_get_decorator_names(node),
        docstring=_get_docstring(node),
        return_annotation=_get_annotation_str(node.returns),
        line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        body_length=(node.end_lineno or node.lineno) - node.lineno,
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _parse_class(node: ast.ClassDef) -> ClassInfo:
    """Parse a class definition node."""
    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_parse_function(item))

    bases = [ast.unparse(base) for base in node.bases]

    return ClassInfo(
        name=node.name,
        bases=bases,
        methods=methods,
        decorators=_get_decorator_names(node),
        docstring=_get_docstring(node),
        line=node.lineno,
        end_line=node.end_lineno or node.lineno,
    )


def _parse_imports(node: ast.Import | ast.ImportFrom) -> list[ImportInfo]:
    """Parse import statements."""
    results = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            results.append(
                ImportInfo(
                    name=alias.name,
                    alias=alias.asname,
                    from_module=None,
                    line=node.lineno,
                )
            )
    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            results.append(
                ImportInfo(
                    name=alias.name,
                    alias=alias.asname,
                    from_module=module,
                    line=node.lineno,
                )
            )
    return results


def parse_file(path: Path) -> ParseResult:
    """Parse a Python file and extract its structure.

    Args:
        path: Path to the Python file to parse.

    Returns:
        ParseResult with imports, functions, classes, and metadata.

    Raises:
        SyntaxError: If the file contains invalid Python syntax.
        FileNotFoundError: If the file does not exist.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    imports: list[ImportInfo] = []
    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(_parse_imports(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_parse_function(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_parse_class(node))

    return ParseResult(
        module_name=path.stem,
        imports=imports,
        functions=functions,
        classes=classes,
    )
