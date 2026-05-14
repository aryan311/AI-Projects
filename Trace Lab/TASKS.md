# TraceLab Task Decomposition

## Milestone 1: Run Store

- Create SQLite schema for workflow runs
- Store run ID, workflow name, status, start time, end time, error
- Add repository functions
- Add tests

Done when:

- success and failure runs persist correctly

## Milestone 2: FastAPI Run API

- Add `/runs`
- Add `/runs/{run_id}`
- Add response schemas
- Add pagination limit

Done when:

- recent runs can be inspected through API

## Milestone 3: Telemetry Wrapper

- Configure OpenTelemetry SDK
- Add helper for named spans
- Add attributes for step name, workflow name, status
- Ensure exceptions are recorded and re-raised

Done when:

- instrumentation does not change business behavior

## Milestone 4: Sample Workflow

- Add successful sample workflow
- Add failing sample workflow
- Add artificial latency
- Add structured step names

Done when:

- both success and failure traces are visible

## Milestone 5: Docker Trace Backend

- Add Jaeger or Tempo to Docker Compose
- Document trace UI URL
- Add environment config

Done when:

- one local command starts API and tracing backend

## Milestone 6: QueryPilot Integration

- Add TraceLab hooks to QueryPilot
- Return trace ID in `/ask`
- Link run ID to trace ID

Done when:

- a QueryPilot request is debuggable from API response to trace UI

## High-Level Build Estimate

- standalone MVP: 3-5 focused days
- QueryPilot integration: 1-2 days

## Diligent Notes

- Root risk: observability that records noise instead of debugging signals.
- Automation: add tests that telemetry does not swallow exceptions.
- Scope guard: do not build a full dashboard in v1.
