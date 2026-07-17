import asyncio
import logging
from pipeline.queue import incident_queue
from db.models import SessionLocal
from incidents.metrics_collector import metrics_collector
from config import config
import time

logger = logging.getLogger(__name__)


class PipelineWorker:
    MAX_RETRIES = config.AGENT_MAX_RETRIES
    ESCALATION_TIMEOUT = config.AGENT_ESCALATION_TIMEOUT_MINUTES * 60

    def __init__(self, num_workers: int = 3):
        self.num_workers = num_workers
        self.running = False
        self._deps = None
        self._resolve_deps()

    def _resolve_deps(self):
        if config.is_demo:
            from simulated import get_simulated_deps
            self._deps = get_simulated_deps()
            logger.info("DEMO MODE — using simulated clients")
        else:
            from mcp.client import mcp_client, signoz_api
            from mcp.response_parser import parser as mcp_parser
            from mcp.queries import QUERY_TEMPLATES
            from llm.engine import ollama_client
            from fix.executor import executor
            from incidents.incident_logger import incident_logger
            from incidents.metrics_collector import metrics_collector
            from api.websocket import manager as ws_manager
            self._deps = {
                "mcp": mcp_client,
                "mcp_fallback": signoz_api,
                "mcp_parser": mcp_parser,
                "mcp_queries": QUERY_TEMPLATES,
                "llm": ollama_client,
                "fix": executor,
                "logger": incident_logger,
                "metrics": metrics_collector,
                "ws": ws_manager
            }

    @property
    def deps(self):
        if self._deps is None:
            self._resolve_deps()
        return self._deps

    async def start(self):
        self.running = True
        logger.info(f"Starting {self.num_workers} pipeline workers (demo={config.is_demo})")
        tasks = [asyncio.create_task(self._worker_loop(i)) for i in range(self.num_workers)]
        await asyncio.gather(*tasks)

    def stop(self):
        self.running = False

    async def _worker_loop(self, worker_id: int):
        logger.info(f"Worker {worker_id} started")
        while self.running:
            try:
                incident_data = await asyncio.wait_for(
                    incident_queue.dequeue(), timeout=1.0
                )
                await self._process_incident(worker_id, incident_data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

    async def _process_incident(self, worker_id: int, incident_data: dict):
        incident_id = incident_data.get("incident_id")
        alert = incident_data.get("body", {})
        retry_count = incident_data.get("retry_count", 0)

        logger.info(f"Worker {worker_id} processing incident {incident_id} "
                    f"(retry {retry_count}/{self.MAX_RETRIES})")

        traces, metrics, logs = self._collect_telemetry(alert)

        diagnosis = self._run_diagnosis(alert, traces, metrics, logs, retry_count)

        if diagnosis.get("suggested_fix") != "escalate" and diagnosis.get("fix_params"):
            await self._attempt_fix(incident_id, diagnosis, retry_count)
        else:
            self._handle_escalation(incident_id, diagnosis, retry_count)

    def _collect_telemetry(self, alert: dict):
        traces = []
        metrics = []
        logs = []
        d = self.deps

        try:
            if config.is_demo:
                from simulated.data import simulated_data
                scenario = alert.get("scenario", "redis_crash")
                data = simulated_data.get_data(scenario)
                return data["traces"], data["metrics"], data["logs"]

            service = alert.get("labels", {}).get("service_name", "sample-app")
            time_range = "now-5m"

            if not d["mcp"].transport == "stdio" or d["mcp"].process is None:
                try:
                    d["mcp"].connect()
                except Exception:
                    pass

            mcp_result = d["mcp"].query_traces(service, time_range)
            if d["mcp_parser"].has_error(mcp_result) or not mcp_result.get("result"):
                mcp_result = d["mcp_fallback"].query(f'{{service="{service}"}}')
                traces = [mcp_result] if mcp_result else []
            else:
                traces = d["mcp_parser"].parse_traces(mcp_result)
            d["metrics"].increment("mcp_queries")

            mcp_metrics = d["mcp"].query_metrics(
                f'avg(system_cpu_utilization{{service="{service}"}})',
                time_range
            )
            if not d["mcp_parser"].has_error(mcp_metrics):
                metrics = d["mcp_parser"].parse_metrics(mcp_metrics)
            d["metrics"].increment("mcp_queries")

            mcp_logs = d["mcp"].query_logs(service, time_range)
            if not d["mcp_parser"].has_error(mcp_logs):
                logs = d["mcp_parser"].parse_logs(mcp_logs)
            d["metrics"].increment("mcp_queries")

        except Exception as e:
            logger.warning(f"Telemetry collection failed: {e}")

        return traces, metrics, logs

    def _run_diagnosis(self, alert: dict, traces: list, metrics: list,
                       logs: list, retry_count: int) -> dict:
        d = self.deps
        try:
            d["metrics"].increment("llm_calls")
            diagnosis = d["llm"].diagnose(alert, traces, metrics, logs)
        except Exception as e:
            logger.warning(f"LLM diagnosis failed: {e}")
            diagnosis = {"root_cause": "Diagnosis failed", "confidence": 0.0,
                         "suggested_fix": "escalate", "fix_params": {}}

        if retry_count > 0 and diagnosis.get("confidence", 0) < 0.5:
            diagnosis["suggested_fix"] = "escalate"
            diagnosis["root_cause"] += " (low confidence after retry)"

        return diagnosis

    async def _attempt_fix(self, incident_id: str, diagnosis: dict, retry_count: int):
        d = self.deps
        suggested_fix = diagnosis.get("suggested_fix", "escalate")
        fix_params = diagnosis.get("fix_params", {})

        try:
            d["metrics"].increment("fix_attempts")
            fix_result = await d["fix"].execute(suggested_fix, fix_params)

            if fix_result.get("verified"):
                d["metrics"].increment("fix_successes")
                d["logger"].log_resolved(incident_id, diagnosis, fix_result)
                logger.info(f"Fix succeeded: {suggested_fix} on {incident_id}")
            elif retry_count < self.MAX_RETRIES:
                logger.warning(f"Fix not verified for {incident_id}, retrying...")
                await incident_queue.enqueue({
                    "incident_id": incident_id,
                    "body": diagnosis,
                    "retry_count": retry_count + 1
                })
            else:
                d["logger"].log_failed(incident_id,
                    fix_result.get("message", "Fix not verified after max retries"))
                logger.warning(f"Fix failed for {incident_id} after {self.MAX_RETRIES} retries")
        except Exception as e:
            error_msg = str(e)
            if retry_count < self.MAX_RETRIES:
                logger.warning(f"Fix error for {incident_id}, retry {retry_count + 1}: {error_msg}")
                await incident_queue.enqueue({
                    "incident_id": incident_id,
                    "body": diagnosis,
                    "retry_count": retry_count + 1
                })
            else:
                d["logger"].log_failed(incident_id, error_msg)
                logger.error(f"Fix permanently failed for {incident_id}: {error_msg}")

    def _handle_escalation(self, incident_id: str, diagnosis: dict, retry_count: int):
        d = self.deps
        if retry_count >= self.MAX_RETRIES:
            d["logger"].log_failed(incident_id,
                f"Escalated: {diagnosis.get('root_cause', 'unknown')} "
                f"(retried {self.MAX_RETRIES} times)")
            logger.warning(f"Incident {incident_id} escalated to human")
        else:
            root_cause = diagnosis.get("root_cause", "unknown")
            d["logger"].log_failed(incident_id, f"Escalated: {root_cause}")
            logger.info(f"Incident {incident_id} escalated: {root_cause}")


pipeline_worker = PipelineWorker(num_workers=config.AGENT_WORKERS)
