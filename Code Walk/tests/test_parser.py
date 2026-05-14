"""Tests for the AST parser module."""

from pathlib import Path

import pytest

from codewalk.parser import parse_file


class TestParseImports:
    """Test import extraction."""

    def test_regular_imports(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        import_names = [i.name for i in result.imports]
        assert "os" in import_names
        assert "sys" in import_names

    def test_from_imports(self, class_example_path: Path):
        result = parse_file(class_example_path)
        from_imports = [i for i in result.imports if i.from_module]
        assert len(from_imports) >= 1
        assert any(i.from_module == "dataclasses" for i in from_imports)
        assert any(i.name == "dataclass" for i in from_imports)

    def test_import_line_numbers(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        for imp in result.imports:
            assert imp.line > 0


class TestParseFunctions:
    """Test function extraction."""

    def test_function_names(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        func_names = [f.name for f in result.functions]
        assert "greet" in func_names
        assert "add" in func_names

    def test_function_arguments(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        greet = next(f for f in result.functions if f.name == "greet")
        assert len(greet.args) == 1
        assert greet.args[0].name == "name"
        assert greet.args[0].annotation == "str"

    def test_function_defaults(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        add = next(f for f in result.functions if f.name == "add")
        b_arg = next(a for a in add.args if a.name == "b")
        assert b_arg.default == "0"

    def test_function_return_annotation(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        greet = next(f for f in result.functions if f.name == "greet")
        assert greet.return_annotation == "str"

    def test_function_docstrings(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        greet = next(f for f in result.functions if f.name == "greet")
        assert greet.docstring == "Greet someone by name."

    def test_function_line_numbers(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        for func in result.functions:
            assert func.line > 0
            assert func.end_line >= func.line
            assert func.body_length >= 0


class TestParseClasses:
    """Test class extraction."""

    def test_class_names(self, class_example_path: Path):
        result = parse_file(class_example_path)
        class_names = [c.name for c in result.classes]
        assert "User" in class_names
        assert "Admin" in class_names

    def test_class_bases(self, class_example_path: Path):
        result = parse_file(class_example_path)
        admin = next(c for c in result.classes if c.name == "Admin")
        assert "User" in admin.bases

    def test_class_decorators(self, class_example_path: Path):
        result = parse_file(class_example_path)
        user = next(c for c in result.classes if c.name == "User")
        assert "dataclass" in user.decorators

    def test_class_docstrings(self, class_example_path: Path):
        result = parse_file(class_example_path)
        user = next(c for c in result.classes if c.name == "User")
        assert user.docstring == "Represents a user."

    def test_class_methods(self, class_example_path: Path):
        result = parse_file(class_example_path)
        user = next(c for c in result.classes if c.name == "User")
        method_names = [m.name for m in user.methods]
        assert "is_adult" in method_names
        assert "greet" in method_names

    def test_class_line_numbers(self, class_example_path: Path):
        result = parse_file(class_example_path)
        for cls in result.classes:
            assert cls.line > 0
            assert cls.end_line >= cls.line


class TestParseModuleName:
    """Test module name extraction."""

    def test_module_name(self, simple_function_path: Path):
        result = parse_file(simple_function_path)
        assert result.module_name == "simple_function"


class TestParseErrors:
    """Test error handling."""

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_file(Path("/nonexistent/file.py"))

    def test_invalid_syntax(self, invalid_syntax_path: Path):
        # Rename to .py for the parser to attempt parsing
        import tempfile
        import shutil

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            shutil.copy(invalid_syntax_path, tmp_path)

        try:
            with pytest.raises(SyntaxError):
                parse_file(tmp_path)
        finally:
            tmp_path.unlink()
