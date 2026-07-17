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
    def diagnose(alert, metrics):
        cpu = any(m.get("value",0)>80 for m in metrics if "cpu" in str(m.get("query","")).lower())
        redis = any(m.get("value",0)>0 for m in metrics if "redis" in str(m.get("query","")).lower())
        if cpu: return {"root_cause":"CPU overload (rule)","severity":alert.get("severity","warning"),"confidence":0.7,"suggested_fix":"scale_service","fix_params":{"service_name":"sample-app","replicas":3}}
        if redis: return {"root_cause":"Redis errors (rule)","severity":"critical","confidence":0.8,"suggested_fix":"restart_container","fix_params":{"service_name":"redis"}}
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
            return _parse_llm(resp.json().get("response","")) if resp.status_code == 200 else self.fallback.diagnose(alert, metrics)
        except Exception:
            return self.fallback.diagnose(alert, metrics)

ollama_client = OllamaClient()
