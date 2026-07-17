SYSTEM_PROMPT = """You are an expert SRE engineer with 15 years of experience debugging production systems. Given telemetry data from SigNoz (traces, metrics, and logs), identify the root cause of the incident.

Rules:
1. Analyze ALL telemetry data before concluding
2. Correlate traces with metrics with logs
3. Be specific — "Redis connection pool exhausted" not "Redis issue"
4. Confidence > 0.6 required for auto-fix; < 0.6 suggest escalation
5. Response must be valid JSON only, no markdown

Output format:
{
    "root_cause": "brief description",
    "severity": "critical|warning|info",
    "confidence": 0.0-1.0,
    "suggested_fix": "restart_container|scale_service|clear_cache|rollback|escalate",
    "fix_params": {},
    "evidence": ["key trace 1", "key metric 1"]
}"""


def build_diagnosis_prompt(alert: dict, traces: list, metrics: list, logs: list) -> str:
    import json
    return f"""ALERT: {alert.get('alert_name', 'unknown')} ({alert.get('severity', 'info')})
SERVICE: {alert.get('labels', {}).get('service_name', 'unknown')}
TIME: {alert.get('starts_at', 'unknown')}

TRACES (last 5 min):
{json.dumps(traces[:5], indent=2)}

METRICS (last 5 min):
{json.dumps(metrics, indent=2)}

ERROR LOGS (last 5 min):
{json.dumps(logs[:5], indent=2)}

Analyze the above and respond in JSON format.
"""
