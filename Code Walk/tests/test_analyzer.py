"""Tests for the code quality analyzer module."""

from pathlib import Path

import pytest

from codewalk.analyzer import analyze
from codewalk.parser import parse_file


class TestLongFunctions:
    """Test long function detection."""

    def test_no_long_functions(self, simple_function_path: Path, simple_function_source: str):
        result = parse_file(simple_function_path)
        analysis = analyze(result, simple_function_source)
        long_warnings = [w for w in analysis.warnings if w.type == "long_function"]
        assert len(long_warnings) == 0


class TestMissingDocstrings:
    """Test missing docstring detection."""

    def test_all_docstrings_present(self, simple_function_path: Path, simple_function_source: str):
        result = parse_file(simple_function_path)
        analysis = analyze(result, simple_function_source)
        doc_warnings = [w for w in analysis.warnings if w.type == "missing_docstring"]
        assert len(doc_warnings) == 0

    def test_missing_docstrings_detected(
        self, warnings_example_path: Path, warnings_example_source: str
    ):
        result = parse_file(warnings_example_path)
        analysis = analyze(result, warnings_example_source)
        doc_warnings = [w for w in analysis.warnings if w.type == "missing_docstring"]
        # no_docstring_function, NoDocstringClass, method_without_docs
        assert len(doc_warnings) >= 2
        messages = [w.message for w in doc_warnings]
        assert any("no_docstring_function" in m for m in messages)
        assert any("NoDocstringClass" in m for m in messages)


class TestBroadExcept:
    """Test broad except detection."""

    def test_bare_except_detected(
        self, warnings_example_path: Path, warnings_example_source: str
    ):
        result = parse_file(warnings_example_path)
        analysis = analyze(result, warnings_example_source)
        except_warnings = [w for w in analysis.warnings if w.type == "broad_except"]
        assert len(except_warnings) >= 1
        assert any("Bare" in w.message for w in except_warnings)

    def test_no_broad_except(self, simple_function_path: Path, simple_function_source: str):
        result = parse_file(simple_function_path)
        analysis = analyze(result, simple_function_source)
        except_warnings = [w for w in analysis.warnings if w.type == "broad_except"]
        assert len(except_warnings) == 0


class TestTooManyArguments:
    """Test too many arguments detection."""

    def test_too_many_args_detected(
        self, warnings_example_path: Path, warnings_example_source: str
    ):
        result = parse_file(warnings_example_path)
        analysis = analyze(result, warnings_example_source)
        arg_warnings = [w for w in analysis.warnings if w.type == "too_many_arguments"]
        assert len(arg_warnings) >= 1
        assert any("bad_function" in w.message for w in arg_warnings)

    def test_acceptable_args(self, simple_function_path: Path, simple_function_source: str):
        result = parse_file(simple_function_path)
        analysis = analyze(result, simple_function_source)
        arg_warnings = [w for w in analysis.warnings if w.type == "too_many_arguments"]
        assert len(arg_warnings) == 0


class TestDeepNesting:
    """Test deep nesting detection."""

    def test_deep_nesting_detected(
        self, warnings_example_path: Path, warnings_example_source: str
    ):
        result = parse_file(warnings_example_path)
        analysis = analyze(result, warnings_example_source)
        nest_warnings = [w for w in analysis.warnings if w.type == "deep_nesting"]
        assert len(nest_warnings) >= 1
        assert any("bad_function" in w.message for w in nest_warnings)

    def test_no_deep_nesting(self, simple_function_path: Path, simple_function_source: str):
        result = parse_file(simple_function_path)
        analysis = analyze(result, simple_function_source)
        nest_warnings = [w for w in analysis.warnings if w.type == "deep_nesting"]
        assert len(nest_warnings) == 0


class TestAnalyzeWarningLineNumbers:
    """Test that all warnings include valid line numbers."""

    def test_warnings_have_line_numbers(
        self, warnings_example_path: Path, warnings_example_source: str
    ):
        result = parse_file(warnings_example_path)
        analysis = analyze(result, warnings_example_source)
        assert len(analysis.warnings) > 0
        for w in analysis.warnings:
            assert w.line > 0, f"Warning '{w.message}' has no line number"
