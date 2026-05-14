"""CLI smoke tests for CodeWalk."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from codewalk.cli import app

runner = CliRunner()

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestInspectCommand:
    """Test the `inspect` CLI command."""

    def test_inspect_returns_json(self):
        result = runner.invoke(app, ["inspect", str(FIXTURES_DIR / "simple_function.py")])
        assert result.exit_code == 0
        # Output should contain JSON-like structure
        assert "greet" in result.output
        assert "add" in result.output

    def test_inspect_class_file(self):
        result = runner.invoke(app, ["inspect", str(FIXTURES_DIR / "class_example.py")])
        assert result.exit_code == 0
        assert "User" in result.output
        assert "Admin" in result.output


class TestExplainCommand:
    """Test the `explain` CLI command."""

    def test_explain_prints_markdown(self):
        result = runner.invoke(app, ["explain", str(FIXTURES_DIR / "simple_function.py")])
        assert result.exit_code == 0
        assert "Module" in result.output
        assert "greet" in result.output

    def test_explain_with_output_file(self, tmp_path: Path):
        output_file = tmp_path / "report.md"
        result = runner.invoke(
            app,
            [
                "explain",
                str(FIXTURES_DIR / "simple_function.py"),
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Module" in content
        assert "greet" in content

    def test_explain_warnings_file(self):
        result = runner.invoke(
            app, ["explain", str(FIXTURES_DIR / "warnings_example.py")]
        )
        assert result.exit_code == 0
        assert "warning" in result.output.lower()


class TestErrorHandling:
    """Test CLI error handling."""

    def test_nonexistent_file(self):
        result = runner.invoke(app, ["inspect", "/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_non_python_file(self):
        result = runner.invoke(
            app, ["inspect", str(FIXTURES_DIR / "invalid_syntax.txt")]
        )
        assert result.exit_code != 0

    def test_explain_nonexistent_file(self):
        result = runner.invoke(app, ["explain", "/nonexistent/file.py"])
        assert result.exit_code != 0
