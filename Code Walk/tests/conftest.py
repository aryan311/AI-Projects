"""Shared test fixtures for CodeWalk tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_function_path() -> Path:
    """Path to the simple function fixture."""
    return FIXTURES_DIR / "simple_function.py"


@pytest.fixture
def class_example_path() -> Path:
    """Path to the class example fixture."""
    return FIXTURES_DIR / "class_example.py"


@pytest.fixture
def warnings_example_path() -> Path:
    """Path to the warnings example fixture."""
    return FIXTURES_DIR / "warnings_example.py"


@pytest.fixture
def invalid_syntax_path() -> Path:
    """Path to the invalid syntax fixture."""
    return FIXTURES_DIR / "invalid_syntax.txt"


@pytest.fixture
def simple_function_source(simple_function_path: Path) -> str:
    """Source code of the simple function fixture."""
    return simple_function_path.read_text(encoding="utf-8")


@pytest.fixture
def class_example_source(class_example_path: Path) -> str:
    """Source code of the class example fixture."""
    return class_example_path.read_text(encoding="utf-8")


@pytest.fixture
def warnings_example_source(warnings_example_path: Path) -> str:
    """Source code of the warnings example fixture."""
    return warnings_example_path.read_text(encoding="utf-8")
