from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider, export as trace_export
from opentelemetry.sdk.metrics import MeterProvider, export as metric_export
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import SpanKind, Status, StatusCode
from contextlib import contextmanager
from config import config
import time

_tracer = None
_instruments = {}

def init_otel():
    global _tracer, _instruments
    if config.DEMO_MODE: return
    resource = Resource.create({"service.name": config.OTEL_SERVICE_NAME, "service.version": "3.1.0"})
    tp = TracerProvider(resource=resource)
    tp.add_span_processor(trace_export.BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{config.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces")))
    trace.set_tracer_provider(tp)
    _tracer = trace.get_tracer(config.OTEL_SERVICE_NAME)
    reader = metric_export.PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{config.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/metrics"), export_interval_millis=5000)
    mp = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(mp)
    meter = metrics.get_meter(config.OTEL_SERVICE_NAME)
    for name, kind, desc in [
        ("agent.incidents.total", "counter", "Total incidents"),
        ("agent.fix.attempts", "counter", "Fix attempts"),
        ("agent.fix.successes", "counter", "Successful fixes"),
        ("agent.llm.calls", "counter", "LLM calls"),
        ("agent.pipeline.duration_ms", "histogram", "Pipeline stage duration ms"),
        ("agent.queue.depth", "histogram", "Queue depth"),
    ]:
        _instruments[name] = (meter.create_counter(name, description=desc) if kind == "counter"
                              else meter.create_histogram(name, description=desc, unit="ms"))

def _rec(name, **attrs):
    inst = _instruments.get(name)
    if inst: inst.add(1, attrs)

def _rec_hist(name, val, **attrs):
    inst = _instruments.get(name)
    if inst: inst.record(val, attrs)

@contextmanager
def trace_pipeline_stage(stage: str, attrs: dict = None):
    if not _tracer:
        yield None; return
    start = time.time()
    max_duration = 300.0
    with _tracer.start_as_current_span(f"pipeline.{stage}", kind=SpanKind.INTERNAL, attributes=attrs or {}) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            ms = (time.time() - start) * 1000
            span.set_attribute("duration_ms", ms)
            span.set_attribute("timeout", ms > max_duration * 1000)
            _rec_hist("agent.pipeline.duration_ms", ms, stage=stage)

def record_incident(iid, action, status):
    _rec("agent.incidents.total", incident_id=iid[:8], action=action, status=status)
    try:
        from incidents.metrics_collector import metrics_collector
        if status == "resolved":
            metrics_collector.increment("incidents_resolved")
        elif status == "failed":
            metrics_collector.increment("incidents_failed")
    except Exception:
        pass
def record_fix_attempt(iid, fix_type): _rec("agent.fix.attempts", incident_id=iid[:8], fix_type=fix_type)
def record_fix_success(iid, fix_type): _rec("agent.fix.successes", incident_id=iid[:8], fix_type=fix_type)
def record_llm_call(iid, model, ok): _rec("agent.llm.calls", incident_id=iid[:8], model=model, success=str(ok))
def record_queue_depth(d): _rec_hist("agent.queue.depth", d)
