import json, httpx, logging
from config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert SRE engineer. Given telemetry data, identify root cause.
Output valid JSON only with no extra text: {"root_cause":"...","severity":"critical|warning|info","confidence":0.0-1.0,"suggested_fix":"restart_container|scale_service|clear_cache|escalate","fix_params":{},"evidence":[]}"""

HYPOTHESIS_PROMPT = """You are an expert SRE engineer. Given telemetry data, list 2-3 possible root cause hypotheses.
Be specific about what you suspect and why. Output as a JSON array of objects with "hypothesis" and "reasoning" fields."""

TOOL_USE_PROMPT = """You are an expert SRE engineer. Given these hypotheses, what additional telemetry queries would confirm or rule out each one?
Available query types: metrics (PromQL), traces (service name), logs (service name).
Output a JSON array of tool calls: [{"type":"metrics|traces|logs","target":"...","reason":"..."}]
Limit to 3 queries. Output ONLY the JSON array."""

EVIDENCE_PROMPT = """You are an expert SRE engineer. Based on the hypotheses and all evidence (initial + tool results), determine the root cause.
Output valid JSON only: {"root_cause":"...","severity":"critical|warning|info","confidence":0.0-1.0,"suggested_fix":"restart_container|scale_service|clear_cache|escalate","fix_params":{},"evidence":[]}"""

def _build_prompt(alert, traces, metrics, logs, correlation=None):
    parts = [
        f"ALERT: {alert.get('alert_name','unknown')} ({alert.get('severity','info')})",
        f"SERVICE: {alert.get('labels',{}).get('service_name','unknown')}",
    ]
    if correlation:
        parts.append(f"CORRELATION: {json.dumps(correlation, indent=2)}")
    parts.append(f"TRACES: {json.dumps(traces[:5], indent=2)}")
    parts.append(f"METRICS: {json.dumps(metrics, indent=2)}")
    parts.append(f"LOGS: {json.dumps(logs[:5], indent=2)}")
    parts.append("Respond with valid JSON only, no markdown, no explanation.")
    return "\n".join(parts)

def _parse_llm(text):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {"root_cause":"Failed to parse LLM response","severity":"info","confidence":0.0,"suggested_fix":"escalate","fix_params":{},"evidence":[]}

def _parse_diagnosis(text):
    raw = _parse_llm(text)
    if isinstance(raw, dict):
        return {"root_cause": raw.get("root_cause","Unknown"), "severity": raw.get("severity","info"),
                "confidence": float(raw.get("confidence",0)), "suggested_fix": raw.get("suggested_fix","escalate"),
                "fix_params": raw.get("fix_params",{}), "evidence": raw.get("evidence",[])}
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
    MAX_RETRIES = 2

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.fallback = RuleBasedFallback()

    def _call_llm(self, prompt):
        resp = httpx.post(f"{self.base_url}/api/generate",
                          json={"model": self.model, "prompt": prompt, "stream": False, "temperature": 0, "max_tokens": 2048},
                          timeout=self.timeout)
        if resp.status_code != 200:
            logger.warning("LLM returned %s: %s", resp.status_code, resp.text[:200])
            return None
        return resp.json().get("response", "")

    def _execute_tool(self, tc, mcp_client, tr="now-5m"):
        try:
            t = tc.get("type")
            target = tc.get("target", "")
            if t == "metrics":
                res = mcp_client.query_metrics(target, tr)
                return {"type": "metrics", "query": target, "result": res.get("result", [])}
            if t == "traces":
                res = mcp_client.query_traces(target, tr)
                return {"type": "traces", "service": target, "result": res.get("result", [])}
            if t == "logs":
                res = mcp_client.query_logs(target, tr)
                return {"type": "logs", "service": target, "result": res.get("result", [])}
        except Exception as e:
            logger.warning("Tool call failed: %s", e)
        return None

    def diagnose(self, alert, traces, metrics, logs, correlation=None, mcp_client=None):
        base = _build_prompt(alert, traces, metrics, logs, correlation)
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Stage 1: Generate hypotheses
                hprompt = f"{HYPOTHESIS_PROMPT}\n{base}"
                hraw = self._call_llm(hprompt)
                if hraw is None:
                    last_error = f"HTTP error on hypothesis (attempt {attempt+1})"
                    continue
                hypotheses = _parse_llm(hraw)
                if not isinstance(hypotheses, list):
                    hypotheses = [{"hypothesis": hypotheses.get("root_cause","unknown"), "reasoning": "LLM direct output"}]

                # Stage 2: Tool-use — LLM requests targeted data
                additional = []
                if mcp_client and isinstance(hypotheses, list) and len(hypotheses) > 0:
                    tprompt = f"{TOOL_USE_PROMPT}\nHYPOTHESES: {json.dumps(hypotheses, indent=2)}"
                    traw = self._call_llm(tprompt)
                    if traw:
                        tool_calls = _parse_llm(traw)
                        if isinstance(tool_calls, list):
                            for tc in tool_calls[:3]:
                                result = self._execute_tool(tc, mcp_client)
                                if result:
                                    additional.append(result)

                # Stage 3: Evaluate with all evidence
                context = f"{base}\n\nHYPOTHESES: {json.dumps(hypotheses, indent=2)}"
                if additional:
                    context += f"\nTOOL_RESULTS: {json.dumps(additional, indent=2)}"
                eprompt = f"{EVIDENCE_PROMPT}\n{context}\nEvaluate and output your final diagnosis."
                eraw = self._call_llm(eprompt)
                if eraw is None:
                    last_error = f"HTTP error on evidence (attempt {attempt+1})"
                    continue
                parsed = _parse_diagnosis(eraw)
                if parsed.get("confidence", 0) > 0:
                    if isinstance(hypotheses, list):
                        parsed["hypotheses_considered"] = [h.get("hypothesis","") for h in hypotheses[:3]]
                    if additional:
                        parsed["tool_calls_executed"] = [a["query"] for a in additional if "query" in a]
                    return parsed
                last_error = f"zero confidence (attempt {attempt+1})"
            except httpx.TimeoutException:
                last_error = f"timeout (attempt {attempt+1})"
                logger.warning("LLM timeout, retry %s/%s", attempt + 1, self.MAX_RETRIES)
                continue
            except Exception as e:
                last_error = f"{e} (attempt {attempt+1})"
                logger.warning("LLM error, retry %s/%s: %s", attempt + 1, self.MAX_RETRIES, e)
                continue
        logger.warning("LLM failed after %s retries: %s", self.MAX_RETRIES, last_error)
        return self.fallback.diagnose(alert, metrics, logs)

ollama_client = OllamaClient()
