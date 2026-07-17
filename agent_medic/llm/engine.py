import json, httpx
from config import config

SYSTEM_PROMPT = """You are an expert SRE engineer. Given telemetry data, identify root cause.
Output JSON: {"root_cause":"...","severity":"critical|warning|info","confidence":0.0-1.0,"suggested_fix":"restart_container|scale_service|clear_cache|escalate","fix_params":{},"evidence":[]}"""

def _build_prompt(alert, traces, metrics, logs):
    return f"""ALERT: {alert.get('alert_name','unknown')} ({alert.get('severity','info')})
SERVICE: {alert.get('labels',{}).get('service_name','unknown')}
TRACES: {json.dumps(traces[:5], indent=2)}
METRICS: {json.dumps(metrics, indent=2)}
LOGS: {json.dumps(logs[:5], indent=2)}
Analyze and respond in JSON."""

def _parse_llm(text):
    try:
        d = json.loads(text)
        return {"root_cause": d.get("root_cause","Unknown"), "severity": d.get("severity","info"),
                "confidence": float(d.get("confidence",0)), "suggested_fix": d.get("suggested_fix","escalate"),
                "fix_params": d.get("fix_params",{}), "evidence": d.get("evidence",[])}
    except (json.JSONDecodeError, ValueError):
        return {"root_cause":"Failed to parse LLM response","severity":"info","confidence":0.0,"suggested_fix":"escalate","fix_params":{},"evidence":[]}

class RuleBasedFallback:
    @staticmethod
    def diagnose(alert, metrics, logs=None):
        logs = logs or []
        for m in metrics:
            q = str(m.get("query", "")).lower()
            v = m.get("value", 0)
            if "redis" in q and v > 0:
                return {"root_cause":"Redis errors (rule)","severity":"critical","confidence":0.8,"suggested_fix":"restart_container","fix_params":{"service_name":"redis"}}
            if "cpu" in q and v > 80:
                return {"root_cause":"CPU overload (rule)","severity":"warning","confidence":0.7,"suggested_fix":"scale_service","fix_params":{"service_name":"sample-app","replicas":3}}
            if "memory" in q and v > 95:
                return {"root_cause":"Memory exhaustion (rule)","severity":"critical","confidence":0.85,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}
            if "disk" in q and v > 90:
                return {"root_cause":"Disk full (rule)","severity":"critical","confidence":0.9,"suggested_fix":"clear_cache","fix_params":{"cache_type":"redis"}}
            if "oom" in q or "memory_leak" in q and v > 0:
                return {"root_cause":"OOM or memory leak (rule)","severity":"critical","confidence":0.85,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}
            if "error_rate" in q and v > 50:
                return {"root_cause":"High error rate (rule)","severity":"critical","confidence":0.7,"suggested_fix":"escalate","fix_params":{}}
            if "tls" in q or "ssl" in q or "cert" in q and v > 0:
                return {"root_cause":"TLS/certificate failure (rule)","severity":"critical","confidence":0.8,"suggested_fix":"escalate","fix_params":{}}
            if "network" in q and v > 0:
                return {"root_cause":"Network failure (rule)","severity":"critical","confidence":0.75,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}
            if "db_connections" in q and v == 0:
                return {"root_cause":"Database unavailable (rule)","severity":"critical","confidence":0.85,"suggested_fix":"restart_container","fix_params":{"service_name":"postgres"}}
        for l in logs:
            body = str(l.get("body", "")).lower()
            if "tls" in body or "cert" in body or "ssl" in body:
                return {"root_cause":"TLS/certificate failure (rule)","severity":"critical","confidence":0.8,"suggested_fix":"escalate","fix_params":{}}
            if "oom" in body or "memory" in body:
                return {"root_cause":"OOM/memory exhaustion (rule)","severity":"critical","confidence":0.85,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}
        return {"root_cause":"Unknown (fallback)","severity":"warning","confidence":0.3,"suggested_fix":"escalate","fix_params":{}}

class OllamaClient:
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.fallback = RuleBasedFallback()

    def diagnose(self, alert, traces, metrics, logs):
        prompt = _build_prompt(alert, traces, metrics, logs)
        try:
            resp = httpx.post(f"{self.base_url}/api/generate",
                              json={"model": self.model, "prompt": prompt, "stream": False, "temperature": 0, "max_tokens": 2048},
                              timeout=self.timeout)
            return _parse_llm(resp.json().get("response","")) if resp.status_code == 200 else self.fallback.diagnose(alert, metrics, logs)
        except Exception:
            return self.fallback.diagnose(alert, metrics, logs)

ollama_client = OllamaClient()
