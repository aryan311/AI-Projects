# CodeWalk

CodeWalk is a Python code explanation tool that uses **static analysis before asking an LLM** to explain anything. It parses Python files with `ast`, extracts structure, identifies maintainability risks, and generates a Markdown walkthrough — optionally enhanced with a local LLM via Ollama.

## Why This Project Exists

Most code explainers send raw code to an LLM and hope the explanation is correct. CodeWalk uses **deterministic Python analysis first**, then optional language generation. The LLM receives AST-extracted facts (imports, functions, classes, arguments, line numbers) alongside the source, producing grounded explanations rather than hallucinations.

## How It Works

```
Python File
    │
    ▼
┌──────────┐     ┌────────────┐     ┌───────────────────┐     ┌────────────┐
│  Parser  │────▶│  Analyzer  │────▶│ Markdown Renderer │────▶│ .md Report │
│  (AST)   │     │ (warnings) │     │   (7 sections)    │     │            │
└──────────┘     └────────────┘     └───────────────────┘     └────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │ LLM (Ollama)│  ◀── optional
                                    │ llama3.1    │
                                    └─────────────┘
```

1. **Parser** — Uses Python's `ast` module to extract imports, functions, classes, arguments, decorators, docstrings, and line numbers from the target `.py` file.
2. **Analyzer** — Runs 5 code quality detectors on the parsed structure:
   - Long functions (> 50 lines)
   - Missing docstrings on functions/classes/methods
   - Broad `except:` or `except Exception:` handlers
   - Too many arguments (> 5)
   - Deeply nested control flow (> 3 levels)
3. **Markdown Renderer** — Combines parse results and analysis into a structured report with sections for module overview, imports, functions, classes, warnings, and suggested tests.
4. **LLM Layer (optional)** — When `--llm` is passed, sends the AST facts + source to a local Ollama model (`llama3.1:latest`) to generate a beginner-friendly explanation. The explanation is clearly labeled as AI-generated.

## Requirements

- **Python** ≥ 3.10
- **Ollama** (only needed for `--llm` mode) — [Install Ollama](https://ollama.com)
  - Model: `llama3.1:latest` — pull with `ollama pull llama3.1:latest`

### Python Dependencies

| Package | Purpose |
|---------|---------|
| `typer[all]` | CLI framework with rich help |
| `rich` | Terminal formatting and progress |
| `pydantic` | Data models and validation |
| `httpx` | HTTP client for Ollama API |
| `pytest` | Test framework (dev) |
| `pytest-cov` | Coverage reporting (dev) |

## Setup

```bash
# Clone and enter the project
cd Code Walk

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
codewalk --help
```

## Usage

### `inspect` — Parse a file and output JSON

```bash
codewalk inspect <file.py>
```

Outputs the parsed structure (imports, functions, classes, arguments, decorators, docstrings, line numbers) as formatted JSON.

```bash
# Example
codewalk inspect tests/fixtures/class_example.py
```

### `explain` — Generate a Markdown walkthrough

```bash
codewalk explain <file.py> [--output report.md] [--llm] [--model MODEL]
```

| Flag | Description |
|------|-------------|
| `--output`, `-o` | Save report to a file instead of printing to stdout |
| `--llm` | Enable LLM-powered beginner explanation (requires Ollama) |
| `--model`, `-m` | Ollama model name (default: `llama3.1:latest`) |

```bash
# Print report to terminal
codewalk explain codewalk/parser.py

# Save report to file
codewalk explain codewalk/parser.py --output docs/parser-walkthrough.md

# With LLM explanation (Ollama must be running)
codewalk explain codewalk/parser.py --llm --output docs/parser-walkthrough.md
```

### Output Report Sections

The generated Markdown report includes:

1. **📄 Module Overview** — filename and summary statistics table
2. **📦 Imports** — table of all imports with aliases and line numbers
3. **⚡ Functions** — each function with args, types, defaults, decorators, docstrings
4. **🏗️ Classes** — each class with bases, methods, decorators, docstrings
5. **⚠️ Warnings** — maintainability issues with line numbers and severity
6. **🧪 Suggested Tests** — auto-generated test suggestions based on function signatures
7. **🤖 AI Explanation** (optional) — LLM-generated beginner-friendly walkthrough

## Testing

### Run All Tests

```bash
source .venv/bin/activate

# Run tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=codewalk

# Run specific test file
pytest tests/test_parser.py -v
pytest tests/test_analyzer.py -v
pytest tests/test_renderer.py -v
pytest tests/test_cli.py -v
```

### Test Coverage

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_parser.py` | 16 | Import/function/class extraction, line numbers, error handling |
| `test_analyzer.py` | 10 | All 5 warning types with positive and negative cases |
| `test_renderer.py` | 10 | Markdown sections, warnings, suggested tests, LLM output |
| `test_cli.py` | 8 + 3 | CLI smoke tests, output files, error handling |
| **Total** | **47** | |

### Test Fixtures

Located in `tests/fixtures/`:

| Fixture | Purpose |
|---------|---------|
| `simple_function.py` | Clean code with imports, typed functions, docstrings |
| `class_example.py` | Classes with `@dataclass`, inheritance, methods |
| `warnings_example.py` | Triggers all 5 analyzer warnings (bad code on purpose) |
| `invalid_syntax.txt` | Invalid Python for error handling tests |

## Project Structure

```
03-codewalk/
├── README.md                       # This file
├── TASKS.md                        # Task decomposition by milestone
├── pyproject.toml                  # Project config, dependencies, CLI entry point
│
├── codewalk/                       # Main package
│   ├── __init__.py                 # Package init, version
│   ├── cli.py                      # Typer CLI — `inspect` and `explain` commands
│   ├── models.py                   # Pydantic data models (8 models)
│   ├── parser.py                   # AST parser — extracts structure from .py files
│   ├── analyzer.py                 # Code quality detectors (5 warning types)
│   ├── renderer.py                 # Markdown report generator (7 sections)
│   └── llm.py                      # Ollama LLM integration + FakeExplainer
│
├── tests/                          # Test suite (47 tests)
│   ├── __init__.py
│   ├── conftest.py                 # Shared pytest fixtures
│   ├── test_parser.py              # Parser tests (16)
│   ├── test_analyzer.py            # Analyzer tests (10)
│   ├── test_renderer.py            # Renderer tests (10)
│   ├── test_cli.py                 # CLI smoke tests (11)
│   └── fixtures/                   # Sample Python files for testing
│       ├── simple_function.py
│       ├── class_example.py
│       ├── warnings_example.py
│       └── invalid_syntax.txt
│
└── docs/                           # Generated reports output directory
```

### Module Responsibilities

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `cli.py` | Typer app | File validation, command routing, output handling |
| `models.py` | Pydantic | `ImportInfo`, `FunctionInfo`, `ClassInfo`, `Warning`, `ParseResult`, `AnalysisResult`, `Report` |
| `parser.py` | `ast` | Parse imports, functions, classes, args, decorators, docstrings, line numbers |
| `analyzer.py` | `ast` | Detect long functions, missing docstrings, broad except, too many args, deep nesting |
| `renderer.py` | Markdown | Convert `Report` → structured Markdown with 7 sections |
| `llm.py` | `httpx` | `OllamaExplainer` (sends AST facts to LLM), `FakeExplainer` (for tests) |

## Architecture

```
CLI (Typer)
  → Parser (ast.parse)
  → Analyzer (5 detectors)
  → Report (Pydantic model)
  → Markdown Renderer
  → optional: Ollama LLM Explainer
  → output file / stdout
```

## Resume Bullet

Built a Python static-analysis CLI using `ast` to explain code structure, detect maintainability issues, and generate Markdown walkthroughs with pytest-backed parser and analyzer behavior.
