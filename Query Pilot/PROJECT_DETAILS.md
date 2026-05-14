# QueryPilot: Project Overview, Design & Code Walkthrough

QueryPilot is a production-ready FastAPI service designed to safely expose a database to a Large Language Model (LLM) allowing users to ask plain English questions and get reliable results. 

Most AI database demos simply take SQL from an LLM and run it. **QueryPilot treats the LLM output as untrusted user input.** It enforces strict validation, limits execution scope, handles timeouts, and ensures no mutating or malicious queries can execute.

## 1. Architectural Decisions & Design Patterns

The project was built using **Ports and Adapters (Hexagonal Architecture)** combined with a **Pipeline Pattern** for request handling, and the **Strategy Pattern** for the LLM integration.

### Hexagonal Architecture (Clean Architecture)
We isolated the core business logic from external dependencies (FastAPI, PostgreSQL, Ollama). The services do not know they are running in an API context. This ensures that the core rules—such as SQL safety validation and query execution limits—are testable and never tightly coupled to the hosting environment.

### Strategy Pattern for LLM
We required the use of Ollama (`llama3.1:latest`) for execution, but also needed a "Fake LLM" for fast, reliable unit testing. 
By defining a base `LLMClient` interface in `app/core/llm.py`, we created two concrete implementations: `OllamaLLMClient` and `FakeLLMClient`. 
FastAPI's dependency injection provides the appropriate client at runtime, allowing seamless testing without real LLM overhead.

### Pipeline Pattern
The primary `/ask` endpoint operates as a sequential pipeline coordinated by `QueryPipelineService`. 
1. `SchemaService` (fetches context)
2. `SqlGenerator` (prompts LLM for SQL)
3. `SqlValidator` (safety checks)
4. `QueryExecutor` (runs query safely)
5. `Summarizer` (LLM translates results)

## 2. Detailed Code Explanation

Below is an explanation of how the core components function under the hood.

### The Pipeline (`app/services/query_pipeline.py`)
This file orchestrates the entire lifecycle of a user request. 
```python
# Fetches the public schema representation (tables & columns)
schema_context = await schema_service.get_schema_context()

# Asks the LLM to write raw SQL based on the user's question + schema
raw_sql = await generator.generate(schema_context, request.question)

# Passes the raw SQL through the security validator
safe_sql = validator.validate_and_format(raw_sql)

# Executes the strictly validated SQL
rows = await executor.execute(safe_sql)

# Translates the JSON rows back into plain English
summary = await summarizer.summarize(request.question, safe_sql, rows)
```

### The Security Validator (`app/services/validator.py`)
This is the most critical file in the project. It uses the `sqlglot` library to parse the LLM's raw string into an Abstract Syntax Tree (AST) to completely eliminate SQL injection risks.

1. **Syntax Checking & Multi-Statement Blocks**:
   ```python
   parsed = sqlglot.parse(sql, read="postgres")
   if len(parsed) > 1:
       raise ValueError("Multiple SQL statements are not allowed.")
   ```
   If the LLM attempts to run `SELECT * FROM users; DROP TABLE products;`, `sqlglot` parses this as two statements, and the validator immediately rejects it.

2. **Mutation Blocking**:
   ```python
   if not isinstance(ast, exp.Select):
       raise ValueError("Only SELECT statements are allowed.")
   
   for node in ast.walk():
       if isinstance(node[0], (exp.Insert, exp.Update, exp.Delete, exp.Drop)):
           raise ValueError("Mutating operations are not allowed.")
   ```
   The root node *must* be a `SELECT`. We also recursively walk the tree to ensure no nested `DELETE` or `UPDATE` commands were injected.

3. **Execution Limits (Memory Protection)**:
   ```python
   limit_expr = ast.args.get("limit")
   if not limit_expr or int(limit_expr.expression.name) > self.max_row_limit:
       ast.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))
   ```
   If the LLM forgot to add a limit, or added `LIMIT 100000`, the validator dynamically overwrites the AST node to enforce a maximum bound (e.g., `LIMIT 100`) before compiling it back to SQL.

### Safe Execution (`app/services/executor.py`)
Even after validation, complex analytical queries can lock up the database. 
```python
async with self.conn.transaction():
    timeout_ms = int(self.timeout_seconds * 1000)
    await self.conn.execute(f"SET LOCAL statement_timeout = {timeout_ms};")
    async with self.conn.cursor() as cur:
        await cur.execute(sql)
```
Before executing the query, we inject a Postgres configuration `SET LOCAL statement_timeout` bound strictly to that specific transaction. If the query runs longer than 5 seconds, Postgres automatically kills it.

### The LLM Strategy (`app/core/llm.py`)
The `OllamaLLMClient` class handles making async POST requests to the local Dockerized host. 
```python
prompt = f"""You are an expert PostgreSQL developer.
Given the following database schema:
{schema_context}
Write a SQL query that answers the following question: {question}
..."""
```
It wraps the user's natural language into a strict system prompt and ensures we strip away any markdown formatting (` ```sql `) that the model might hallucinate, returning only executable code.

## 3. The Interactive Frontend

To make the application demonstrable, we bypassed building a complex React app and instead served a single-page HTML file (`app/static/index.html`) directly from FastAPI. 

- **Glassmorphism Aesthetic**: Uses modern web design principles like blurred backgrounds, gradients, and custom scrolling.
- **Dynamic Interactions**: Handles API state management (loading spinners, error boxes, dynamic table generation) natively using Vanilla JS.
- **Seamless Integration**: The HTML file interacts seamlessly with the `/ask` endpoint, rendering the `Summary`, the raw `Generated SQL`, and the raw `Data Results` all in one place.

## 4. System Flow Diagram

The following Mermaid diagram visualises the end‑to‑end request lifecycle, from the browser UI to the database and LLM:

```mermaid
flowchart TD
    A[Browser UI (index.html)] -->|POST /ask| B[FastAPI /ask endpoint]
    B --> C[QueryPipelineService]
    C --> D[SchemaService]
    C --> E[SqlGenerator (OllamaLLMClient)]
    C --> F[SqlValidator]
    C --> G[QueryExecutor]
    C --> H[Summarizer (OllamaLLMClient)]
    D --> I[PostgreSQL (schema introspection)]
    G --> J[PostgreSQL (query execution)]
    E --> K[Ollama (llama3.1:latest)]
    H --> K
    K --> L[LLM response (SQL / summary)]
    L --> C
    J --> M[Result rows]
    M --> C
    C --> B
    B --> A
```

* **Blue arrows** represent data flow.
* **Dashed lines** (if any) would indicate optional/auxiliary calls.
* All components are loosely coupled via dependency injection, enabling easy swapping of implementations (e.g., FakeLLMClient for tests).

---
