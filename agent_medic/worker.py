import asyncio
import logging
from pipeline.queue import incident_queue
from mcp.client import mcp_client, signoz_api
from mcp.response_parser import parser
from mcp.queries import QUERY_TEMPLATES
from llm.engine import ollama_client
from fix.executor import executor
from logging.incident_logger import incident_logger
from logging.metrics_collector import metrics_collector
from db.models import Incident, SessionLocal, IncidentStatus
from config import config

logger = logging.getLogger(__name__)


class PipelineWorker:
    def __init__(self, num_workers: int = 3):
        self.num_workers = num_workers
        self.running = False

    async def start(self):
        self.running = True
        logger.info(f"Starting {self.num_workers} pipeline workers")
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

        logger.info(f"Worker {worker_id} processing incident {incident_id}")

        if not mcp_client.transport == "stdio" or mcp_client.process is None:
            try:
                mcp_client.connect()
            except Exception:
                pass

        traces = []
        metrics = []
        logs = []

        try:
            service = alert.get("labels", {}).get("service_name", "sample-app")
            time_range = "now-5m"

            mcp_result = await asyncio.to_thread(
                mcp_client.query_traces, service, time_range
            )
            if parser.has_error(mcp_result) or not mcp_result.get("result"):
                mcp_result = await asyncio.to_thread(
                    signoz_api.query, f'{{service="{service}"}}'
                )
                traces = [mcp_result] if mcp_result else []
            else:
                traces = parser.parse_traces(mcp_result)
            metrics_collector.increment("mcp_queries")

            mcp_metrics = await asyncio.to_thread(
                mcp_client.query_metrics,
                f'avg(system_cpu_utilization{{service="{service}"}})',
                time_range
            )
            if not parser.has_error(mcp_metrics):
                metrics = parser.parse_metrics(mcp_metrics)
            metrics_collector.increment("mcp_queries")

            mcp_logs = await asyncio.to_thread(
                mcp_client.query_logs, service, time_range
            )
            if not parser.has_error(mcp_logs):
                logs = parser.parse_logs(mcp_logs)
            metrics_collector.increment("mcp_queries")

        except Exception as e:
            logger.warning(f"MCP query failed, using fallback: {e}")

        try:
            metrics_collector.increment("llm_calls")
            diagnosis = await asyncio.to_thread(
                ollama_client.diagnose, alert, traces, metrics, logs
            )
        except Exception as e:
            logger.warning(f"LLM diagnosis failed: {e}")
            diagnosis = ollama_client.fallback.diagnose(alert, metrics)

        logger.info(f"Diagnosis: {diagnosis.get('root_cause', 'unknown')} "
                    f"(confidence: {diagnosis.get('confidence', 0)})")

        suggested_fix = diagnosis.get("suggested_fix", "escalate")
        fix_params = diagnosis.get("fix_params", {})

        if suggested_fix != "escalate" and fix_params:
            try:
                metrics_collector.increment("fix_attempts")
                fix_result = await executor.execute(suggested_fix, fix_params)
                if fix_result.get("verified"):
                    metrics_collector.increment("fix_successes")
                    incident_logger.log_resolved(incident_id, diagnosis, fix_result)
                    logger.info(f"Fix succeeded: {suggested_fix} on {incident_id}")
                else:
                    incident_logger.log_failed(incident_id, fix_result.get("message", "Fix not verified"))
                    logger.warning(f"Fix not verified for {incident_id}")
            except Exception as e:
                incident_logger.log_failed(incident_id, str(e))
                logger.error(f"Fix failed for {incident_id}: {e}")
        else:
            incident_logger.log_failed(incident_id, "No fix suggested or escalated")
            logger.info(f"No fix for {incident_id}, escalated")


pipeline_worker = PipelineWorker(num_workers=config.AGENT_WORKERS)
