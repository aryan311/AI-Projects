.PHONY: install test lint type run clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests
	ruff format --check src tests

type:
	mypy src/filewise

run:
	.venv/bin/uvicorn filewise.api.main:app --reload

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
