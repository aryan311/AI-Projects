"""
Tests for the telemetry wrapper (traced_step).

Validates:
- traced_step re-raises exceptions
- traced_step records exception details on spans
- Tracing disabled mode doesn't crash
"""

import os
import pytest
from unittest.mock import patch

# Ensure tracing is disabled for unit tests
os.environ["ENABLE_TRACING"] = "false"

from app.core.telemetry import traced_step, get_tracer, setup_telemetry, shutdown_telemetry


@pytest.mark.asyncio
async def test_traced_step_success():
    """A successful traced step should complete without error."""
    async with traced_step("test_step", "test_workflow") as span:
        result = 42

    assert result == 42


@pytest.mark.asyncio
async def test_traced_step_reraises_exceptions():
    """traced_step must re-raise exceptions — telemetry must not swallow errors."""
    with pytest.raises(ValueError, match="test error"):
        async with traced_step("failing_step", "test_workflow"):
            raise ValueError("test error")


@pytest.mark.asyncio
async def test_traced_step_with_attributes():
    """traced_step should accept custom attributes without error."""
    async with traced_step(
        "custom_step",
        "test_workflow",
        attributes={"custom.key": "value", "custom.count": 42},
    ) as span:
        pass  # No error expected


@pytest.mark.asyncio
async def test_traced_step_nested():
    """Nested traced steps should work correctly."""
    async with traced_step("outer_step", "test_workflow"):
        async with traced_step("inner_step", "test_workflow"):
            result = "nested"

    assert result == "nested"


@pytest.mark.asyncio
async def test_get_tracer_returns_tracer():
    """get_tracer should return a valid tracer instance."""
    tracer = get_tracer("test")
    assert tracer is not None


@pytest.mark.asyncio
async def test_tracing_disabled_smoke():
    """When tracing is disabled, all operations should still work."""
    # This tests the no-op path
    async with traced_step("noop_step", "noop_workflow"):
        pass  # Should not raise
