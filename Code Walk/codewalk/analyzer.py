"""Code quality analyzer for parsed Python structures.

Detects maintainability issues such as long functions, missing docstrings,
broad exception handlers, too many arguments, and deep nesting.
"""

from __future__ import annotations

import ast
from pathlib import Path

from codewalk.models import AnalysisResult, ParseResult, Warning

# Configurable thresholds
MAX_FUNCTION_LENGTH = 50
MAX_ARGUMENTS = 5
MAX_NESTING_DEPTH = 3


def _check_long_functions(result: ParseResult) -> list[Warning]:
    """Detect functions with body length exceeding the threshold."""
    warnings = []
    all_functions = list(result.functions)
    for cls in result.classes:
        all_functions.extend(cls.methods)

    for func in all_functions:
        if func.body_length > MAX_FUNCTION_LENGTH:
            warnings.append(
                Warning(
                    type="long_function",
                    message=(
                        f"Function '{func.name}' is {func.body_length} lines long "
                        f"(threshold: {MAX_FUNCTION_LENGTH})"
                    ),
                    line=func.line,
                    severity="warning",
                )
            )
    return warnings


def _check_missing_docstrings(result: ParseResult) -> list[Warning]:
    """Detect functions and classes without docstrings."""
    warnings = []

    for func in result.functions:
        if not func.docstring:
            warnings.append(
                Warning(
                    type="missing_docstring",
                    message=f"Function '{func.name}' has no docstring",
                    line=func.line,
                    severity="warning",
                )
            )

    for cls in result.classes:
        if not cls.docstring:
            warnings.append(
                Warning(
                    type="missing_docstring",
                    message=f"Class '{cls.name}' has no docstring",
                    line=cls.line,
                    severity="warning",
                )
            )
        for method in cls.methods:
            if not method.docstring:
                warnings.append(
                    Warning(
                        type="missing_docstring",
                        message=(
                            f"Method '{cls.name}.{method.name}' has no docstring"
                        ),
                        line=method.line,
                        severity="warning",
                    )
                )

    return warnings


def _check_broad_except(source: str) -> list[Warning]:
    """Detect bare `except:` or `except Exception:` handlers."""
    warnings = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return warnings

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                # Bare except:
                warnings.append(
                    Warning(
                        type="broad_except",
                        message="Bare 'except:' clause catches all exceptions",
                        line=node.lineno,
                        severity="warning",
                    )
                )
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                warnings.append(
                    Warning(
                        type="broad_except",
                        message="'except Exception' is too broad; catch specific exceptions",
                        line=node.lineno,
                        severity="info",
                    )
                )

    return warnings


def _check_too_many_arguments(result: ParseResult) -> list[Warning]:
    """Detect functions with more arguments than the threshold."""
    warnings = []
    all_functions = list(result.functions)
    for cls in result.classes:
        all_functions.extend(cls.methods)

    for func in all_functions:
        # Count only regular args (exclude *args, **kwargs)
        regular_args = [a for a in func.args if not a.name.startswith(("*", "**"))]
        if len(regular_args) > MAX_ARGUMENTS:
            warnings.append(
                Warning(
                    type="too_many_arguments",
                    message=(
                        f"Function '{func.name}' has {len(regular_args)} arguments "
                        f"(threshold: {MAX_ARGUMENTS})"
                    ),
                    line=func.line,
                    severity="warning",
                )
            )

    return warnings


def _measure_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Recursively measure the maximum nesting depth of control flow."""
    max_depth = current_depth
    control_flow_types = (ast.If, ast.For, ast.While, ast.With, ast.AsyncFor, ast.AsyncWith)

    for child in ast.iter_child_nodes(node):
        if isinstance(child, control_flow_types):
            child_depth = _measure_nesting_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = _measure_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)

    return max_depth


def _check_nested_control_flow(source: str) -> list[Warning]:
    """Detect deeply nested control flow structures."""
    warnings = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return warnings

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            depth = _measure_nesting_depth(node)
            if depth > MAX_NESTING_DEPTH:
                warnings.append(
                    Warning(
                        type="deep_nesting",
                        message=(
                            f"Function '{node.name}' has control flow nested "
                            f"{depth} levels deep (threshold: {MAX_NESTING_DEPTH})"
                        ),
                        line=node.lineno,
                        severity="warning",
                    )
                )

    return warnings


def analyze(parse_result: ParseResult, source: str) -> AnalysisResult:
    """Run all analyzers on parsed code and source text.

    Args:
        parse_result: The structured parse output from the parser.
        source: The raw source code of the file.

    Returns:
        AnalysisResult containing all detected warnings.
    """
    warnings: list[Warning] = []

    warnings.extend(_check_long_functions(parse_result))
    warnings.extend(_check_missing_docstrings(parse_result))
    warnings.extend(_check_broad_except(source))
    warnings.extend(_check_too_many_arguments(parse_result))
    warnings.extend(_check_nested_control_flow(source))

    # Sort warnings by line number for readable output
    warnings.sort(key=lambda w: w.line)

    return AnalysisResult(warnings=warnings)
