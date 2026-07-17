from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry import context as otel_context
from opentelemetry.trace import SpanKind, Status, StatusCode
from contextlib import contextmanager
from config import config
import time


_SERVICE_NAME = "agent-medic"
_tracer = None
_meter = None

_agent_incidents_total = None
_agent_fix_attempts = None
_agent_fix_successes = None
_agent_pipeline_duration = None
_agent_llm_calls = None
_agent_queue_depth = None


def init_otel():
    global _tracer, _meter
    global _agent_incidents_total, _agent_fix_attempts, _agent_fix_successes
    global _agent_pipeline_duration, _agent_llm_calls, _agent_queue_depth

    if config.is_demo:
        return

    resource = Resource.create({
        "service.name": _SERVICE_NAME,
        "service.version": "3.0.0",
        "deployment.environment": "demo" if config.is_demo else "production"
    })

    trace_exporter = OTLPSpanExporter(
        endpoint=f"{config.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces"
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)
    _tracer = trace.get_tracer(_SERVICE_NAME)

    metric_exporter = OTLPMetricExporter(
        endpoint=f"{config.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/metrics"
    )
    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    _meter = metrics.get_meter(_SERVICE_NAME)

    _agent_incidents_total = _meter.create_counter(
        "agent.incidents.total",
        description="Total incidents processed"
    )
    _agent_fix_attempts = _meter.create_counter(
        "agent.fix.attempts",
        description="Total fix attempts"
    )
    _agent_fix_successes = _meter.create_counter(
        "agent.fix.successes",
        description="Total successful fixes"
    )
    _agent_pipeline_duration = _meter.create_histogram(
        "agent.pipeline.duration_ms",
        description="Pipeline stage duration in ms",
        unit="ms"
    )
    _agent_llm_calls = _meter.create_counter(
        "agent.llm.calls",
        description="Total LLM diagnosis calls"
    )
    _agent_queue_depth = _meter.create_histogram(
        "agent.queue.depth",
        description="Current incident queue depth"
    )


def get_tracer():
    return _tracer


def get_meter():
    return _meter


@contextmanager
def trace_pipeline_stage(stage_name: str, attributes: dict = None):
    if _tracer is None:
        yield None
        return
    start = time.time()
    with _tracer.start_as_current_span(
        f"pipeline.{stage_name}",
        kind=SpanKind.INTERNAL,
        attributes=attributes or {}
    ) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            duration = (time.time() - start) * 1000
            span.set_attribute("duration_ms", duration)
            if _agent_pipeline_duration:
                _agent_pipeline_duration.record(
                    duration,
                    {"stage": stage_name}
                )


def record_incident(incident_id: str, action: str, status: str):
    if _agent_incidents_total:
        _agent_incidents_total.add(1, {
            "incident_id": incident_id[:8],
            "action": action,
            "status": status
        })


def record_fix_attempt(incident_id: str, fix_type: str):
    if _agent_fix_attempts:
        _agent_fix_attempts.add(1, {
            "incident_id": incident_id[:8],
            "fix_type": fix_type
        })


def record_fix_success(incident_id: str, fix_type: str):
    if _agent_fix_successes:
        _agent_fix_successes.add(1, {
            "incident_id": incident_id[:8],
            "fix_type": fix_type
        })


def record_llm_call(incident_id: str, model: str, success: bool):
    if _agent_llm_calls:
        _agent_llm_calls.add(1, {
            "incident_id": incident_id[:8],
            "model": model,
            "success": str(success)
        })


def record_queue_depth(depth: int):
    if _agent_queue_depth:
        _agent_queue_depth.record(depth)
