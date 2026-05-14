"""Tests for the Markdown renderer module."""

from pathlib import Path

import pytest

from codewalk.analyzer import analyze
from codewalk.models import Report
from codewalk.parser import parse_file
from codewalk.renderer import render


@pytest.fixture
def simple_report(simple_function_path: Path, simple_function_source: str) -> Report:
    """Build a report from the simple function fixture."""
    parse_result = parse_file(simple_function_path)
    analysis_result = analyze(parse_result, simple_function_source)
    return Report(parse_result=parse_result, analysis_result=analysis_result)


@pytest.fixture
def warnings_report(warnings_example_path: Path, warnings_example_source: str) -> Report:
    """Build a report from the warnings example fixture."""
    parse_result = parse_file(warnings_example_path)
    analysis_result = analyze(parse_result, warnings_example_source)
    return Report(parse_result=parse_result, analysis_result=analysis_result)


@pytest.fixture
def llm_report(simple_function_path: Path, simple_function_source: str) -> Report:
    """Build a report with a fake LLM explanation."""
    parse_result = parse_file(simple_function_path)
    analysis_result = analyze(parse_result, simple_function_source)
    return Report(
        parse_result=parse_result,
        analysis_result=analysis_result,
        llm_explanation="This module provides utility functions for greeting and arithmetic.",
    )


class TestMarkdownSections:
    """Test that the rendered Markdown contains expected sections."""

    def test_contains_module_overview(self, simple_report: Report):
        md = render(simple_report)
        assert "# 📄 Module:" in md
        assert "simple_function" in md

    def test_contains_imports_section(self, simple_report: Report):
        md = render(simple_report)
        assert "## 📦 Imports" in md
        assert "`os`" in md
        assert "`sys`" in md

    def test_contains_functions_section(self, simple_report: Report):
        md = render(simple_report)
        assert "## ⚡ Functions" in md
        assert "greet" in md
        assert "add" in md

    def test_contains_overview_table(self, simple_report: Report):
        md = render(simple_report)
        assert "| Metric | Count |" in md
        assert "| Imports |" in md


class TestWarningsInOutput:
    """Test that warnings appear in rendered output."""

    def test_warnings_section_present(self, warnings_report: Report):
        md = render(warnings_report)
        assert "## ⚠️ Warnings" in md

    def test_warning_types_shown(self, warnings_report: Report):
        md = render(warnings_report)
        assert "too_many_arguments" in md or "missing_docstring" in md

    def test_no_warnings_message(self, simple_report: Report):
        md = render(simple_report)
        assert "No Warnings" in md or "No maintainability issues" in md


class TestSuggestedTests:
    """Test suggested tests section."""

    def test_suggested_tests_section(self, simple_report: Report):
        md = render(simple_report)
        assert "## 🧪 Suggested Tests" in md

    def test_test_suggestions_for_functions(self, simple_report: Report):
        md = render(simple_report)
        assert "test_greet" in md
        assert "test_add" in md


class TestLLMSection:
    """Test the LLM explanation section."""

    def test_llm_section_present(self, llm_report: Report):
        md = render(llm_report)
        assert "## 🤖 AI Explanation" in md
        assert "utility functions" in md

    def test_llm_section_absent_when_none(self, simple_report: Report):
        md = render(simple_report)
        assert "## 🤖 AI Explanation" not in md
