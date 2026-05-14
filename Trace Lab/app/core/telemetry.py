"""
OpenTelemetry setup with auto-instrumentation for FastAPI and httpx.

This module configures the OTel SDK, sets up exporters, and provides
a `traced_step` async context manager for instrumenting workflow steps.
Auto-instrumentation captures FastAPI requests and outbound httpx calls
(e.g. Ollama) without manual span creation.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import StatusCode, format_trace_id
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.core.config import settings

logger = logging.getLogger(__name__)

_provider: TracerProvider | None = None


def setup_telemetry(app=None) -> TracerProvider:
    """
    Configure OpenTelemetry with OTLP exporter and auto-instrumentation.

    Call this once during application startup. If tracing is disabled,
    a no-op provider is used so all tracing calls become safe no-ops.
    """
    global _provider

    if not settings.enable_tracing:
        logger.info("Tracing disabled via ENABLE_TRACING=false")
        _provider = TracerProvider()
        trace.set_tracer_provider(_provider)
        return _provider

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "0.1.0",
        }
    )

    _provider = TracerProvider(resource=resource)

    # Try to configure OTLP exporter; fall back to console if unavailable
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_endpoint,
            insecure=True,
        )
        _provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(
            "OTLP exporter configured → %s", settings.otel_exporter_endpoint
        )
    except Exception as e:
        logger.warning("OTLP exporter unavailable, using console: %s", e)
        _provider.add_span_processor(
            SimpleSpanProcessor(ConsoleSpanExporter())
        )

    trace.set_tracer_provider(_provider)

    # --- Auto-instrumentation ---
    # FastAPI: auto-creates spans for every HTTP request
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI auto-instrumentation enabled")

    # httpx: auto-creates spans for outbound HTTP calls (Ollama LLM calls)
    HTTPXClientInstrumentor().instrument()
    logger.info("httpx auto-instrumentation enabled")

    # sqlite3: auto-creates spans for database operations
    try:
        from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

        SQLite3Instrumentor().instrument()
        logger.info("SQLite3 auto-instrumentation enabled")
    except Exception as e:
        logger.debug("SQLite3 auto-instrumentation skipped: %s", e)

    return _provider


def shutdown_telemetry() -> None:
    """Flush pending spans and shut down the tracer provider."""
    global _provider
    if _provider is not None:
        _provider.shutdown()
        logger.info("Telemetry shut down")


def get_tracer(name: str = "tracelab") -> trace.Tracer:
    """Return a named tracer instance."""
    return trace.get_tracer(name)


def get_current_trace_id() -> str | None:
    """Return the current trace ID as a hex string, or None."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return format_trace_id(ctx.trace_id)
    return None


@asynccontextmanager
async def traced_step(
    step_name: str,
    workflow_name: str = "",
    attributes: dict | None = None,
) -> AsyncGenerator[trace.Span, None]:
    """
    Async context manager that wraps a workflow step in an OTel span.

    - Records step_name and workflow_name as span attributes
    - Records exceptions and sets span status to ERROR
    - Always re-raises exceptions (telemetry must not change business behavior)
    - Safe to use even when tracing is disabled (becomes a no-op)

    Usage:
        async with traced_step("llm_sql_generation", "querypilot") as span:
            result = await call_llm(...)
            span.set_attribute("token_count", result.tokens)
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(step_name) as span:
        span.set_attribute("tracelab.step_name", step_name)
        if workflow_name:
            span.set_attribute("tracelab.workflow_name", workflow_name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)

        try:
            yield span
            span.set_attribute("tracelab.status", "success")
            span.set_status(StatusCode.OK)
        except Exception as exc:
            span.set_attribute("tracelab.status", "error")
            span.set_attribute("tracelab.error_type", type(exc).__name__)
            span.set_attribute("tracelab.error_message", str(exc))
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise  # Always re-raise — telemetry must not swallow errors
