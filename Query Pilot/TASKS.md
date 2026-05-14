# QueryPilot Task Decomposition

## Milestone 1: Project Skeleton

- Create Python package with FastAPI
- Add `pyproject.toml`
- Add `/health`
- Add Dockerfile
- Add Docker Compose with Postgres
- Add README run instructions

Done when:

- app starts locally
- database starts locally
- `/health` returns OK

## Milestone 2: Sample Database

- Design ecommerce schema
- Add seed SQL
- Add migration or init script
- Add database connection module
- Add schema discovery query

Done when:

- `/schema` returns tables and columns
- tests verify schema discovery

## Milestone 3: Request and Response Contracts

- Add Pydantic request model
- Add Pydantic response model
- Add error response model
- Add `/ask` placeholder

Done when:

- API contract is stable
- invalid request returns 422

## Milestone 4: SQL Generator

- Add LLM client interface
- Add fake LLM implementation for tests
- Add prompt builder with schema context
- Add generated SQL response parsing

Done when:

- fake LLM can drive `/ask` tests
- real LLM is behind one interface

## Milestone 5: SQL Validator

- Parse or inspect SQL safely
- Allow only single `SELECT`
- Block dangerous keywords
- Enforce `LIMIT`
- Add row limit normalization

Done when:

- 10+ unsafe SQL cases are blocked
- safe SELECT queries pass

## Milestone 6: Query Execution

- Execute validated SQL
- Add timeout
- Convert rows to dictionaries
- Normalize database errors
- Hide stack traces

Done when:

- `/ask` returns rows for valid questions
- DB failures return safe errors

## Milestone 7: Summary and Warnings

- Add summarizer interface
- Add deterministic summary fallback
- Add empty-result warning
- Add limit warning

Done when:

- response is useful without reading raw rows only

## Milestone 8: MCP-Ready Tools

- Add tool functions independent of API layer
- Add `list_tables`
- Add `describe_table`
- Add `run_readonly_query`
- Reuse same validator

Done when:

- API and tool path share safety logic

## Milestone 9: Observability

- Add trace spans for each workflow step
- Add trace ID to response
- Add Docker Compose tracing service

Done when:

- one request can be followed in trace UI

## High-Level Build Estimate

- MVP: 5-7 focused days
- MCP wrapper: 1-2 days
- observability: 1-2 days

## Diligent Notes

- Root risk: unsafe model output.
- Automation: tests must run without real LLM.
- Scope guard: do not add multi-database support in v1.
