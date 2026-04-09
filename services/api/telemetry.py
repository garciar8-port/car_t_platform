"""
OpenTelemetry instrumentation for BioFlow Scheduler API.

Provides request tracing, custom metrics, and Grafana-compatible exports.
"""

import os
import time
from contextlib import contextmanager
from typing import Optional

# OpenTelemetry is optional
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


SERVICE_NAME = "bioflow-scheduler-api"
SERVICE_VERSION = os.getenv("MODEL_VERSION", "v0.4.0-phase4")


def setup_telemetry():
    """Initialize OpenTelemetry tracing and metrics."""
    if not OTEL_AVAILABLE:
        return

    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
    })

    # Tracing
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)

    # Metrics
    reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=30000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)


# Pre-built instruments
_tracer = None
_meter = None
_request_counter = None
_request_duration = None
_inference_duration = None
_recommendation_counter = None


def _ensure_instruments():
    global _tracer, _meter, _request_counter, _request_duration, _inference_duration, _recommendation_counter
    if _tracer is not None:
        return

    if OTEL_AVAILABLE:
        _tracer = trace.get_tracer(SERVICE_NAME, SERVICE_VERSION)
        _meter = metrics.get_meter(SERVICE_NAME, SERVICE_VERSION)
        _request_counter = _meter.create_counter(
            "http.requests.total",
            description="Total HTTP requests",
        )
        _request_duration = _meter.create_histogram(
            "http.request.duration_ms",
            description="HTTP request duration in milliseconds",
        )
        _inference_duration = _meter.create_histogram(
            "model.inference.duration_ms",
            description="Model inference duration in milliseconds",
        )
        _recommendation_counter = _meter.create_counter(
            "recommendations.total",
            description="Total recommendations generated",
        )


class TelemetryRecorder:
    """Lightweight telemetry recorder that works with or without OpenTelemetry."""

    def __init__(self):
        self._metrics_log: list[dict] = []
        _ensure_instruments()

    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        entry = {
            "type": "request",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "timestamp": time.time(),
        }
        self._metrics_log.append(entry)

        if OTEL_AVAILABLE and _request_counter:
            _request_counter.add(1, {"endpoint": endpoint, "method": method, "status_code": str(status_code)})
            _request_duration.record(duration_ms, {"endpoint": endpoint})

    def record_inference(self, patient_id: str, duration_ms: float, action: str, confidence: float):
        entry = {
            "type": "inference",
            "patient_id": patient_id,
            "duration_ms": round(duration_ms, 2),
            "action": action,
            "confidence": confidence,
            "timestamp": time.time(),
        }
        self._metrics_log.append(entry)

        if OTEL_AVAILABLE and _inference_duration:
            _inference_duration.record(duration_ms)
            _recommendation_counter.add(1, {"action": action})

    @contextmanager
    def trace_span(self, name: str, attributes: Optional[dict] = None):
        """Context manager for tracing a code block."""
        if OTEL_AVAILABLE and _tracer:
            with _tracer.start_as_current_span(name, attributes=attributes or {}) as span:
                yield span
        else:
            yield None

    def get_metrics_summary(self) -> dict:
        """Return summary metrics for the /health endpoint."""
        requests = [m for m in self._metrics_log if m["type"] == "request"]
        inferences = [m for m in self._metrics_log if m["type"] == "inference"]

        return {
            "total_requests": len(requests),
            "total_inferences": len(inferences),
            "avg_request_ms": round(sum(r["duration_ms"] for r in requests) / max(len(requests), 1), 2),
            "avg_inference_ms": round(sum(i["duration_ms"] for i in inferences) / max(len(inferences), 1), 2),
            "p95_inference_ms": round(sorted([i["duration_ms"] for i in inferences])[int(len(inferences) * 0.95)] if inferences else 0, 2),
        }


# Singleton
telemetry = TelemetryRecorder()
