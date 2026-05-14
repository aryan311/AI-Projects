# CodeWalk Task Decomposition

## Milestone 1: CLI Skeleton

- Create Typer app
- Add `inspect` command
- Add `explain` command
- Add file path validation
- Add basic tests

Done when:

- CLI accepts a `.py` file and returns a result

## Milestone 2: AST Parser

- Parse imports
- Parse functions
- Parse classes
- Parse arguments
- Parse decorators
- Parse docstrings
- Capture line numbers

Done when:

- parser returns structured JSON for fixture files

## Milestone 3: Analyzer

- Detect long functions
- Detect missing docstrings
- Detect broad exception handlers
- Detect too many arguments
- Detect nested control flow

Done when:

- analyzer warnings include line numbers and reasons

## Milestone 4: Markdown Renderer

- Convert parsed structure into Markdown
- Include warnings
- Include suggested tests
- Support output file path

Done when:

- `codewalk explain file.py` creates a useful report

## Milestone 5: Optional LLM Layer

- Add explainer interface
- Feed AST facts, not raw-only code
- Clearly label generated explanation
- Add fake explainer for tests

Done when:

- LLM mode is optional and testable

## High-Level Build Estimate

- MVP: 4-6 focused days
- LLM layer: 1-2 days
- repo scanning: 2-3 days

## Diligent Notes

- Root risk: hallucinated explanations.
- Automation: use fixtures and snapshot tests.
- Scope guard: Python-only in v1.
