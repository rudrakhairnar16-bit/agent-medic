from config import config
from llm.context_builder import context_builder
from llm.response_parser import response_parser as llm_parser
from typing import Optional


class RuleBasedFallback:
    @staticmethod
    def diagnose(alert: dict, metrics: list) -> dict:
        cpu_high = any(
            m.get("value", 0) > 80
            for m in metrics
            if "cpu" in str(m.get("query", "")).lower()
        )
        redis_error = any(
            m.get("value", 0) > 0
            for m in metrics
            if "redis" in str(m.get("query", "")).lower()
        )

        if cpu_high:
            return {
                "root_cause": "CPU overload detected (rule-based)",
                "severity": alert.get("severity", "warning"),
                "confidence": 0.7,
                "suggested_fix": "scale_service",
                "fix_params": {"service_name": "sample-app", "replicas": 3}
            }
        if redis_error:
            return {
                "root_cause": "Redis errors detected (rule-based)",
                "severity": "critical",
                "confidence": 0.8,
                "suggested_fix": "restart_container",
                "fix_params": {"service_name": "redis"}
            }

        return {
            "root_cause": "Unknown (LLM unavailable, rule-based fallback)",
            "severity": "warning",
            "confidence": 0.3,
            "suggested_fix": "escalate",
            "fix_params": {}
        }


class OllamaClient:
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.fallback = RuleBasedFallback()

    def diagnose(self, alert: dict, traces: list, metrics: list, logs: list) -> dict:
        import httpx
        context = context_builder.build_context(alert, traces, metrics, logs)
        payload = context_builder.to_ollama_payload(context)

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                return llm_parser.parse(resp.json().get("response", ""))
            return self.fallback.diagnose(alert, metrics)
        except Exception:
            return self.fallback.diagnose(alert, metrics)


ollama_client = OllamaClient()
