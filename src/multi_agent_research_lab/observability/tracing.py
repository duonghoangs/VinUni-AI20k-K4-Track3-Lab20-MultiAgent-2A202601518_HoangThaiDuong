"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.state import ResearchState


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal provider-neutral span with success/error status."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "status": "ok",
    }
    try:
        yield span
    except Exception as exc:
        span["status"] = "error"
        span["error"] = str(exc)
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started


def export_trace(state: ResearchState, path: Path) -> Path:
    """Write sanitized workflow trace and aggregate usage as JSON."""

    payload = {
        "query": state.request.query,
        "route_history": state.route_history,
        "trace": state.trace,
        "usage": {
            "input_tokens": state.input_tokens,
            "output_tokens": state.output_tokens,
            "estimated_cost_usd": state.estimated_cost_usd,
            "retries": state.retries,
        },
        "errors": state.errors,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def configure_langsmith(settings: Settings) -> bool:
    """Enable LangGraph's native LangSmith tracing when explicitly configured."""

    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return False
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True
