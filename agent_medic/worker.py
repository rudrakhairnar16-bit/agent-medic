import asyncio, logging
from pipeline.queue import incident_queue
from config import config
from otel import trace_pipeline_stage, record_incident, record_fix_attempt, record_fix_success, record_llm_call, record_queue_depth

logger = logging.getLogger(__name__)

def _get_deps():
    if config.DEMO_MODE:
        from simulated import get_simulated_deps
        return get_simulated_deps()
    from mcp.client import signoz_api, parser as mcp_parser, QUERY_TEMPLATES
    from llm.engine import ollama_client
    from fix.executor import executor
    from incidents.incident_logger import incident_logger
    from incidents.metrics_collector import metrics_collector
    return {"mcp": signoz_api, "mcp_parser": mcp_parser,
            "mcp_queries": QUERY_TEMPLATES, "llm": ollama_client, "fix": executor,
            "logger": incident_logger, "metrics": metrics_collector}

class PipelineWorker:
    MAX_RETRIES = config.AGENT_MAX_RETRIES

    def __init__(self, n=3):
        self.n, self.running = n, False
        self._tasks = []
        self.deps = _get_deps()

    async def start(self):
        self.running = True
        logger.info("Starting %s workers (demo=%s)", self.n, config.DEMO_MODE)
        self._tasks = [asyncio.create_task(self._loop(i)) for i in range(self.n)]

    async def stop(self):
        self.running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _loop(self, wid):
        while self.running:
            try:
                data = await asyncio.wait_for(incident_queue.dequeue(), 1.0)
                record_queue_depth(incident_queue.qsize())
                await self._process(wid, data)
            except asyncio.TimeoutError: continue
            except Exception as e: logger.error("Worker %s: %s", wid, e)
            await asyncio.sleep(0.05)

    async def _process(self, wid, data):
        iid, alert, retry = data.get("incident_id"), data.get("body", {}), data.get("retry_count", 0)
        attrs = {"incident_id": iid[:8], "worker_id": str(wid), "retry": str(retry)}
        with trace_pipeline_stage("full_pipeline", attrs):
            from pipeline.queue import correlator
            correlation = correlator.correlate()
            with trace_pipeline_stage("collect_telemetry", attrs):
                traces, mdata, logs = self._collect(alert)
            with trace_pipeline_stage("diagnose", attrs):
                diag = self._diagnose(alert, traces, mdata, logs, retry, correlation)
            if diag.get("suggested_fix") != "escalate" and diag.get("fix_params"):
                await self._fix(iid, diag, retry)
            else:
                self._escalate(iid, diag, retry)

    def _collect(self, alert):
        d = self.deps
        if config.DEMO_MODE:
            scenario = alert.get("scenario", "redis_crash")
            d["mcp"].set_scenario(scenario)
        try:
            svc = alert.get("labels", {}).get("service_name", "sample-app")
            tr = "now-5m"
            mcp = d["mcp"]
            parser = d.get("mcp_parser")
            mt = d.get("metrics")
            r = mcp.query_traces(svc, tr)
            traces = parser.parse_traces(r) if parser and not parser.has_error(r) else r.get("result", []) if isinstance(r, dict) else []
            if mt: mt.increment("mcp_queries")
            mr = mcp.query_metrics(f'avg(system_cpu_utilization{{service="{svc}"}})', tr)
            metrics = parser.parse_metrics(mr) if parser and not parser.has_error(mr) else mr.get("result", []) if isinstance(mr, dict) else []
            if mt: mt.increment("mcp_queries")
            lr = mcp.query_logs(svc, tr)
            logs = parser.parse_logs(lr) if parser and not parser.has_error(lr) else lr.get("result", []) if isinstance(lr, dict) else []
            if mt: mt.increment("mcp_queries")
            return traces, metrics, logs
        except Exception as e:
            logger.warning("Telemetry collection failed: %s", e)
            return [], [], []

    def _diagnose(self, alert, traces, metrics, logs, retry, correlation=None):
        d = self.deps
        try:
            d["metrics"].increment("llm_calls")
            diag = d["llm"].diagnose(alert, traces, metrics, logs, correlation, mcp_client=d.get("mcp"))
            record_llm_call(alert.get("incident_id", "x"), config.OLLAMA_MODEL, True)
            if retry > 0 and diag.get("confidence", 0) < 0.5:
                diag["suggested_fix"] = "escalate"
                diag["root_cause"] += " (low confidence)"
            return diag
        except Exception as e:
            logger.warning("LLM failed: %s", e)
            record_llm_call(alert.get("incident_id", "x"), config.OLLAMA_MODEL, False)
            return {"root_cause": "Diagnosis failed", "confidence": 0.0, "suggested_fix": "escalate", "fix_params": {}}

    async def _fix(self, iid, diag, retry):
        d = self.deps
        fix_type, params = diag.get("suggested_fix", "escalate"), diag.get("fix_params", {})
        try:
            d["metrics"].increment("fix_attempts")
            record_fix_attempt(iid, fix_type)
            result = await d["fix"].execute(fix_type, params)
            if result.get("verified"):
                d["metrics"].increment("fix_successes")
                record_fix_success(iid, fix_type); record_incident(iid, fix_type, "resolved")
                d["logger"].log_resolved(iid, diag, result)
            elif retry < self.MAX_RETRIES:
                await incident_queue.enqueue({"incident_id": iid, "body": diag, "retry_count": retry + 1})
            else:
                record_incident(iid, fix_type, "failed")
                d["logger"].log_failed(iid, result.get("message", "Max retries"))
        except Exception as e:
            if retry < self.MAX_RETRIES:
                await incident_queue.enqueue({"incident_id": iid, "body": diag, "retry_count": retry + 1})
            else:
                record_incident(iid, fix_type, "failed")
                d["logger"].log_failed(iid, str(e))

    def _escalate(self, iid, diag, retry):
        rc = diag.get("root_cause", "unknown")
        label = f" (retried {self.MAX_RETRIES}x)" if retry >= self.MAX_RETRIES else ""
        record_incident(iid, "escalate", "escalated")
        self.deps["logger"].log_failed(iid, f"Escalated: {rc}{label}")

pipeline_worker = PipelineWorker(n=config.AGENT_WORKERS)
