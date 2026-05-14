import os
import sys


def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


def add(a: int, b: int = 0) -> int:
    """Add two numbers together."""
    return a + b
