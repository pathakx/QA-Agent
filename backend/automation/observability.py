"""
Observability Module
====================

Provides structured logging, metrics hooks, and tracing for the
automation abstraction layer.

Design Decisions:
- Uses stdlib `logging` with structured JSON-like formatting for
  easy integration with log aggregators (ELK, Datadog, etc).
- MetricsCollector is a simple in-memory counter for MVP, designed
  to be replaced with Prometheus/StatsD in production.
- All log entries include `engine`, `phase`, and `component` fields
  for filtering by migration phase.
"""

from __future__ import annotations

import logging
import time
import functools
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from contextlib import asynccontextmanager


# ============================================================
# Structured Logger Setup
# ============================================================

class AutomationLogFormatter(logging.Formatter):
    """
    Structured log formatter that includes automation-specific context.
    
    Output format:
        [2026-05-17 16:00:00] [automation.engine] [INFO] [playwright] [phase:1] Message
    """

    def format(self, record: logging.LogRecord) -> str:
        # Inject defaults for automation fields if not present
        engine = getattr(record, "engine", "unknown")
        phase = getattr(record, "phase", "?")
        component = getattr(record, "component", "core")

        prefix = (
            f"[{self.formatTime(record)}] "
            f"[{record.name}] "
            f"[{record.levelname}] "
            f"[{engine}] "
            f"[phase:{phase}] "
            f"[{component}] "
        )
        return prefix + record.getMessage()


def get_automation_logger(
    name: str,
    engine: str = "unknown",
    phase: int = 1,
    component: str = "core",
) -> logging.Logger:
    """
    Create a logger with automation context baked into every record.
    
    Args:
        name: Logger name (e.g., "automation.driver_factory")
        engine: Current engine ("selenium" or "playwright")
        phase: Current migration phase number
        component: Component name for filtering
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(AutomationLogFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    # Create a filter that injects context into every record
    class ContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "engine"):
                record.engine = engine  # type: ignore[attr-defined]
            if not hasattr(record, "phase"):
                record.phase = phase  # type: ignore[attr-defined]
            if not hasattr(record, "component"):
                record.component = component  # type: ignore[attr-defined]
            return True

    # Avoid duplicate filters
    filter_names = [f.name for f in logger.filters if hasattr(f, "name")]
    ctx_filter = ContextFilter(name=f"ctx_{name}")
    if ctx_filter.name not in filter_names:
        logger.addFilter(ctx_filter)

    return logger


# ============================================================
# Metrics Collector (MVP — In-Memory)
# ============================================================

@dataclass
class MetricPoint:
    """A single metric measurement."""
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """
    Simple in-memory metrics collector for migration observability.
    
    Tracks counters and timing histograms. Designed to be replaced
    with Prometheus client or StatsD in production.
    
    Thread-safe: No, but safe for single-event-loop async usage.
    
    Usage:
        metrics = MetricsCollector()
        metrics.increment("browser.launch", tags={"engine": "playwright"})
        
        with metrics.timer("test.execution", tags={"test_id": "TC-001"}):
            await run_test()
        
        print(metrics.summary())
    """

    _instance: Optional["MetricsCollector"] = None

    def __init__(self) -> None:
        self._counters: Dict[str, float] = defaultdict(float)
        self._timings: Dict[str, list[float]] = defaultdict(list)
        self._tags_store: Dict[str, Dict[str, str]] = {}

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        self._counters[key] += value
        if tags:
            self._tags_store[key] = tags

    def record_timing(self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timing measurement."""
        key = self._make_key(name, tags)
        self._timings[key].append(duration_seconds)
        if tags:
            self._tags_store[key] = tags

    @asynccontextmanager
    async def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Async context manager to time an operation."""
        start = time.monotonic()
        try:
            yield
        finally:
            duration = time.monotonic() - start
            self.record_timing(name, duration, tags)

    def summary(self) -> Dict[str, Any]:
        """Return a summary of all collected metrics."""
        result: Dict[str, Any] = {"counters": {}, "timings": {}}

        for key, value in self._counters.items():
            result["counters"][key] = {
                "count": value,
                "tags": self._tags_store.get(key, {}),
            }

        for key, values in self._timings.items():
            if values:
                result["timings"][key] = {
                    "count": len(values),
                    "avg_ms": round(sum(values) / len(values) * 1000, 2),
                    "min_ms": round(min(values) * 1000, 2),
                    "max_ms": round(max(values) * 1000, 2),
                    "tags": self._tags_store.get(key, {}),
                }

        return result

    def reset(self) -> None:
        """Reset all metrics. Useful for testing."""
        self._counters.clear()
        self._timings.clear()
        self._tags_store.clear()

    @staticmethod
    def _make_key(name: str, tags: Optional[Dict[str, str]] = None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


# ============================================================
# Tracing Hooks (Lifecycle Events)
# ============================================================

class ExecutionTracer:
    """
    Lifecycle event tracer for automation operations.
    
    Emits structured log events at each lifecycle boundary:
    - browser.launch / browser.close
    - context.create / context.close
    - test.start / test.step / test.end
    - artifact.capture
    - healing.attempt / healing.result
    
    These events enable:
    - Debugging migration issues
    - Performance analysis
    - Audit trails
    """

    def __init__(self, engine: str = "unknown", phase: int = 1) -> None:
        self._logger = get_automation_logger(
            "automation.tracer",
            engine=engine,
            phase=phase,
            component="tracer",
        )
        self._metrics = MetricsCollector.get_instance()

    def trace(self, event: str, details: Optional[Dict[str, Any]] = None, level: str = "info") -> None:
        """
        Emit a trace event.
        
        Args:
            event: Event name (e.g., "browser.launch")
            details: Optional details dict
            level: Log level ("debug", "info", "warning", "error")
        """
        msg = f"TRACE [{event}]"
        if details:
            detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
            msg = f"{msg} {detail_str}"

        log_method = getattr(self._logger, level, self._logger.info)
        log_method(msg)

        # Auto-increment metrics for trace events
        self._metrics.increment(f"trace.{event}")

    def trace_error(self, event: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """Trace an error event with exception details."""
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(details or {}),
        }
        self.trace(event, error_details, level="error")


# ============================================================
# Decorator for Timed Operations
# ============================================================

def timed_operation(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """
    Decorator to automatically time and count async function calls.
    
    Usage:
        @timed_operation("browser.launch", tags={"engine": "playwright"})
        async def launch_browser(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics = MetricsCollector.get_instance()
            metrics.increment(f"{metric_name}.calls", tags=tags)
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                metrics.increment(f"{metric_name}.success", tags=tags)
                return result
            except Exception as e:
                metrics.increment(f"{metric_name}.failure", tags=tags)
                raise
            finally:
                duration = time.monotonic() - start
                metrics.record_timing(metric_name, duration, tags)
        return wrapper
    return decorator
