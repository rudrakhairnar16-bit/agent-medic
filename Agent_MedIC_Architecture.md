# AGENT MEDIC — Complete Architecture v2.0

**Team:** Enthusiast (Rudra + Het Patel)  
**Track:** 01 — AI & Agent Observability  
**Hackathon:** Agents of SigNoz (Jul 20-26, 2026)

---

## 1. System Architecture (4-Layer Design)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            LAYER 1: USER INTERFACE                                │
│                                                                                   │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────────────┐   │
│   │  GitHub       │   │  Terminal    │   │  Web UI      │   │  Slack/Email   │   │
│   │  (Source)     │   │  (Deploy)    │   │  (Browser)   │   │  (Notify)      │   │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └───────┬────────┘   │
│          │  git push        │  docker-compose  │  ws://localhost   │  webhook    │
└──────────┼──────────────────┼──────────────────┼───────────────────┼─────────────┘
           │                  │                  │                   │
           ▼                  ▼                  ▼                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            LAYER 2: OBSERVABILITY                                 │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────┐│
│   │                         SigNoz (via Foundry)                                 ││
│   │                                                                              ││
│   │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                ││
│   │   │ OTel Collector│    │ Query Service │    │ Alert Manager │                ││
│   │   │ :4318 (HTTP)  │    │ :3301 (API)   │    │ :3301 (hooks) │                ││
│   │   │ :4317 (gRPC)  │    │               │    │               │                ││
│   │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                ││
│   │          │                   │                   │                          ││
│   │          ▼                   ▼                   ▼                          ││
│   │   ┌──────────────────────────────────────────────────────────────────┐     ││
│   │   │                    ClickHouse (Storage)                          │     ││
│   │   │    traces  │  metrics  │  logs  │  span_attributes  │  ...       │     ││
│   │   └──────────────────────────────────────────────────────────────────┘     ││
│   │                                                                              ││
│   │   ┌──────────────────────────────────────────────────────────────────┐     ││
│   │   │                    MCP Server (stdio/HTTP)                       │     ││
│   │   │    Tools: query_traces, query_metrics, query_logs,               │     ││
│   │   │           get_alerts, get_services, create_dashboard             │     ││
│   │   └──────────────────────────────────────────────────────────────────┘     ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────┐│
│   │                      Instrumented Services                                   ││
│   │                                                                              ││
│   │   ┌────────────────────┐    ┌────────────────────┐                          ││
│   │   │  FastAPI App       │    │     Redis           │                          ││
│   │   │  :8001             │    │     :6379           │                          ││
│   │   │  OTel SDK (Python) │    │     OTel SDK        │                          ││
│   │   │  Service: sample-  │    │     (Redis plugin)  │                          ││
│   │   │         app         │    │                    │                          ││
│   │   └─────────┬──────────┘    └────────────────────┘                          ││
│   │             │ OTLP :4318                                                     ││
│   │             ▼                                                                ││
│   │   ┌────────────────────┐    ┌────────────────────┐                          ││
│   │   │  PostgreSQL        │    │  Intentionally      │                          ││
│   │   │  :5432             │    │  Buggy endpoints    │                          ││
│   │   │  (App DB)          │    │  /trigger/*         │                          ││
│   │   └────────────────────┘    └────────────────────┘                          ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
           │                     │                          │
           │ HTTP POST           │ MCP stdio/HTTP           │ Docker SDK (socket)
           │ /webhook            │ query_traces() etc.      │ /var/run/docker.sock
           ▼                     ▼                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            LAYER 3: AGENT CORE                                    │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────┐│
│   │                     FastAPI Application (:8000)                              ││
│   │                                                                              ││
│   │   ┌──────────────────────────────────────────────────────────────────────┐  ││
│   │   │                          API ROUTES                                  │  ││
│   │   │  POST /webhook     → alert_listener.handle_alert()                   │  ││
│   │   │  GET  /health      → return {"status": "healthy"}                    │  ││
│   │   │  GET  /incidents   → return all incidents (paginated)               │  ││
│   │   │  GET  /incidents/{id} → return single incident with diagnosis       │  ││
│   │   │  WS   /ws/events   → real-time incident stream to Web UI            │  ││
│   │   └──────────────────────────────────────────────────────────────────────┘  ││
│   │                                                                              ││
│   │   ┌──────────────────────────────────────────────────────────────────────┐  ││
│   │   │                     INCIDENT PIPELINE (Async Queue)                   │  ││
│   │   │                                                                       │  ││
│   │   │   Alert comes in → dedup check → rate limit → enqueue → process      │  ││
│   │   │                                                                       │  ││
│   │   │   Queue: asyncio.Queue (in-memory) or Redis Queue                     │  ││
│   │   │   Workers: 3 concurrent workers processing incidents                 │  ││
│   │   └──────────────────────────────────────────────────────────────────────┘  ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────┐│
│   │                         ANALYSIS ENGINE                                      ││
│   │                                                                              ││
│   │   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     ││
│   │   │ MCP Client        │    │  LangGraph       │    │  Ollama Client   │     ││
│   │   │                  │    │  State Machine   │    │                  │     ││
│   │   │ connect()        │    │                  │    │ chat()           │     ││
│   │   │ query_traces()   │───▶│ collect → analyze │───▶│ generate()       │     ││
│   │   │ query_metrics()  │    │ diagnose → plan  │    │ stream()         │     ││
│   │   │ query_logs()     │    │ execute → verify │    │                  │     ││
│   │   └──────────────────┘    └──────────────────┘    └──────────────────┘     ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────┐│
│   │                         RESOLUTION ENGINE                                    ││
│   │                                                                              ││
│   │   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     ││
│   │   │ Docker Client     │    │ Fix Executor     │    │ Incident Logger  │     ││
│   │   │                  │    │                  │    │                  │     ││
│   │   │ restart_container│───▶│ restart → verify │───▶│ SigNoz custom log │     ││
│   │   │ scale_service    │    │ scale  → verify  │    │ Update alert     │     ││
│   │   │ get_logs()       │    │ cache  → verify  │    │ DB insert        │     ││
│   │   └──────────────────┘    └──────────────────┘    └──────────────────┘     ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
           │
           │ SQLAlchemy ORM
           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            LAYER 4: DATA STORE                                    │
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────┐│
│   │                          PostgreSQL (:5432)                                  ││
│   │                                                                              ││
│   │   ┌──────────────────────────────────────────────────────────────────────┐  ││
│   │   │                             TABLES                                   │  ││
│   │   │                                                                       │  ││
│   │   │  incidents                                                           │  ││
│   │   │  ├─ id (UUID, PK)                                                    │  ││
│   │   │  ├─ alert_id VARCHAR(255)                                            │  ││
│   │   │  ├─ alert_name VARCHAR(255)                                          │  ││
│   │   │  ├─ status ENUM(open, investigating, diagnosing, fixing, resolved,  │  ││
│   │   │  │          failed, escalated)                                       │  ││
│   │   │  ├─ severity ENUM(critical, warning, info)                           │  ││
│   │   │  ├─ source_service VARCHAR(255)                                      │  ││
│   │   │  ├─ telemetry_data JSONB                                             │  ││
│   │   │  ├─ message TEXT                                                     │  ││
│   │   │  ├─ retry_count INT DEFAULT 0                                        │  ││
│   │   │  ├─ created_at TIMESTAMP DEFAULT NOW()                               │  ││
│   │   │  └─ resolved_at TIMESTAMP                                            │  ││
│   │   │                                                                       │  ││
│   │   │  diagnosis_results — FK → incidents                                  │  ││
│   │   │  ├─ root_cause TEXT                                                  │  ││
│   │   │  ├─ confidence FLOAT                                                 │  ││
│   │   │  ├─ evidence JSONB                                                   │  ││
│   │   │  ├─ suggested_fix VARCHAR(255)                                       │  ││
│   │   │  ├─ fix_params JSONB                                                 │  ││
│   │   │  └─ llm_response_raw TEXT                                            │  ││
│   │   │                                                                       │  ││
│   │   │  fix_actions — FK → incidents                                        │  ││
│   │   │  ├─ action_type VARCHAR(100)                                         │  ││
│   │   │  ├─ status ENUM(pending, running, success, failed)                  │  ││
│   │   │  ├─ params JSONB                                                     │  ││
│   │   │  ├─ duration_ms INT                                                  │  ││
│   │   │  └─ verified BOOLEAN                                                 │  ││
│   │   │                                                                       │  ││
│   │   │  agent_metrics                                                       │  ││
│   │   │  ├─ incidents_total INT                                              │  ││
│   │   │  ├─ incidents_resolved INT                                           │  ││
│   │   │  ├─ avg_resolution_time_ms INT                                       │  ││
│   │   │  └─ auto_fix_success_rate FLOAT                                      │  ││
│   │   └───────────────────────────────────────────────────────────────────────┘  ││
│   └─────────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow — Alert to Resolution

```
                    ┌─────────────────────────────────────────────────────┐
                    │               ALERT WEBHOOK FORMAT                  │
                    │                                                     │
                    │  POST /webhook                                      │
                    │  {                                                  │
                    │    "alert_id": "alert_abc123",                     │
                    │    "alert_name": "High Error Rate",                │
                    │    "severity": "critical",                          │
                    │    "status": "firing",                              │
                    │    "labels": {                                      │
                    │      "service_name": "sample-app",                  │
                    │      "severity": "critical"                         │
                    │    },                                               │
                    │    "annotations": {                                 │
                    │      "summary": "Error rate > 5% for 5 minutes",   │
                    │      "description": "Service sample-app has ..."   │
                    │    },                                               │
                    │    "starts_at": "2026-07-20T10:00:00Z"             │
                    │  }                                                  │
                    └─────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │           STEP 1: INCIDENT CREATION                 │
                    │                                                     │
                    │  alert_listener.py receives webhook                │
                    │  → Check dedup (same alert_id in last 5 min?)      │
                    │  → Check rate limit (max 10 alerts/min)            │
                    │  → Create incident record in PostgreSQL            │
                    │  → Push to async queue                              │
                    │  → Update Web UI via WebSocket                      │
                    └─────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │           STEP 2: DATA COLLECTION (MCP)             │
                    │                                                     │
                    │  mcp_client.py queries SigNoz:                     │
                    │                                                     │
                    │  ┌─────────────────────────────────────────────┐   │
                    │  │ # Query 1: Traces for affected service      │   │
                    │  │ mcp.call("query_traces", {                  │   │
                    │  │   "filters": {"service.name": "sample-app",│   │
                    │  │              "status.code": "ERROR"},       │   │
                    │  │   "timeRange": {"from": "now-5m",          │   │
                    │  │                "to": "now"}                 │   │
                    │  │ })                                          │   │
                    │  │                                              │   │
                    │  │ # Query 2: Metrics                          │   │
                    │  │ mcp.call("query_metrics", {                 │   │
                    │  │   "query": "avg(system_cpu_utilization)",   │   │
                    │  │   "timeRange": {"from": "now-5m", ...}     │   │
                    │  │ })                                          │   │
                    │  │                                              │   │
                    │  │ # Query 3: Error logs                       │   │
                    │  │ mcp.call("query_logs", {                    │   │
                    │  │   "filters": {"service": "sample-app",     │   │
                    │  │              "severity": "error"},          │   │
                    │  │   "timeRange": {...}                        │   │
                    │  │ })                                          │   │
                    │  └─────────────────────────────────────────────┘   │
                    │                                                     │
                    │  All results → JSON → stored in context            │
                    └─────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │         STEP 3: LLM ANALYSIS (LangGraph)            │
                    │                                                     │
                    │  diagnosis_engine.py builds prompt:                │
                    │                                                     │
                    │  SYSTEM: "You are an SRE expert. Given the         │
                    │    following telemetry data, identify the root     │
                    │    cause and suggest a fix. Respond in JSON."       │
                    │                                                     │
                    │  CONTEXT: {traces, metrics, logs data}             │
                    │                                                     │
                    │  LLM RESPONSE:                                      │
                    │  {                                                  │
                    │    "root_cause": "Redis connection pool exhausted  │
                    │       due to 5000 concurrent connections",          │
                    │    "severity": "critical",                          │
                    │    "confidence": 0.92,                              │
                    │    "suggested_fix": "restart_container",            │
                    │    "fix_params": {"container": "redis",            │
                    │                   "action": "restart"},            │
                    │    "evidence": ["trace_abc...", "log_xyz..."]     │
                    │  }                                                  │
                    └─────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │         STEP 4: FIX EXECUTION (Docker SDK)          │
                    │                                                     │
                    │  fix_executor.py receives:                          │
                    │  {"action": "restart_container",                    │
                    │   "params": {"container_name": "agent-medic-redis-1"}}│
                    │                                                     │
                    │  ┌─────────────────────────────────────────────┐   │
                    │  │ import docker                               │   │
                    │  │ client = docker.from_env()                  │   │
                    │  │ container = client.containers.get("redis")  │   │
                    │  │ container.restart(timeout=30)               │   │
                    │  │                                              │   │
                    │  │ # Available fix actions:                    │   │
                    │  │ FIX_ACTIONS = {                             │   │
                    │  │   "restart_container": ...,                  │   │
                    │  │   "scale_service": ...,                      │   │
                    │  │   "clear_cache": ...,                        │   │
                    │  │   "rollback_deployment": ...                 │   │
                    │  │ }                                            │   │
                    │  └─────────────────────────────────────────────┘   │
                    │                                                     │
                    │  After fix → health_verifier.py:                   │
                    │  • Query SigNoz MCP for error rate                 │
                    │  • Check container status                          │
                    │  • Return verified: true/false                     │
                    └─────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │         STEP 5: INCIDENT LOGGING                    │
                    │                                                     │
                    │  incident_logger.py:                               │
                    │                                                     │
                    │  ✅ PostgreSQL: Update incident status → resolved   │
                    │  ✅ SigNoz: Push custom log with incident data      │
                    │  ✅ SigNoz: Resolve the alert                        │
                    │  ✅ Web UI: WebSocket push "Incident #42 Resolved"  │
                    │  ✅ Email/Slack: Optional notification (if config)  │
                    └─────────────────────────────────────────────────────┘
```

---

## 3. LangGraph State Machine — Detailed

```
                    ┌──────────────┐
                    │   ENTRY POINT│
                    │ (Alert Recvd)│
                    └──────┬───────┘
                           │
                           ▼
              ┌──────────────────────┐
              │   collect_data       │
              │                      │
              │  Input: alert        │
              │  Action: MCP queries  │
              │  Output: telemetry    │
              │  Retry: 3 (exp back) │
              └──────────┬───────────┘
                         │ success
                         ▼
              ┌──────────────────────┐
              │   analyze_data       │
              │                      │
              │  Input: telemetry    │
              │  Action: LLM analyze  │
              │  Output: patterns    │
              │  Retry: 2 (fallback) │
              └──────────┬───────────┘
                         │ success
                         ▼
              ┌──────────────────────┐
              │   diagnose_rca       │
              │                      │
              │  Input: patterns     │
              │  Action: LLM root    │
              │          cause       │
              │  Output: diagnosis   │
              └──────────┬───────────┘
                         │ confidence > 0.6
                         ▼
              ┌──────────────────────┐
              │   plan_fix           │
              │                      │
              │  Input: diagnosis    │
              │  Action: LLM fix plan│
              │  Output: fix_action  │
              └──────────┬───────────┘
                         │ plan ready
                         ▼
              ┌──────────────────────┐
              │   execute_fix        │
              │                      │
              │  Input: fix_action   │
              │  Action: Docker API   │
              │  Output: result      │
              │  Retry: 2 (exp back) │
              └──────────┬───────────┘
                         │ executed
                         ▼
              ┌──────────────────────┐
              │   verify_fix         │
              │                      │
              │  Input: result       │
              │  Action: MCP health   │
              │  Output: verified    │
              └──────────┬───────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         verified=true        verified=false
              │                     │
              ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │   log_success    │  │  retry_count < 3  │
    │                  │  │  → back to        │
    │  Status: resolved│  │    execute_fix     │
    │  DB update       │  │                    │
    │  SigNoz log      │  │  retry_count >= 3  │
    │  WebSocket push  │  │  → log_failure     │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │
             ▼                     ▼
       ┌──────────┐        ┌──────────────┐
       │    END   │        │  log_failure  │
       └──────────┘        │              │
                           │  Status:      │
                           │  escalated    │
                           │  Notify human │
                           └──────┬───────┘
                                  │
                                  ▼
                            ┌──────────┐
                            │    END   │
                            └──────────┘
```

---

## 4. MCP Protocol — SigNoz Integration

### 4.1 MCP Tool Definitions

| Tool Name | Parameters | Returns |
|---|---|---|
| `query_traces` | filters (dict), timeRange (dict) | \[trace_id, span_id, duration, status, ...\] |
| `query_metrics` | query (str), timeRange (dict) | \[series: \[{timestamp, value}\]\] |
| `query_logs` | filters (dict), timeRange (dict) | \[timestamp, severity, body, attributes\] |
| `get_alerts` | status (str) | \[alert_id, name, severity, status\] |
| `get_services` | — | \[service_name, p99_latency, error_rate\] |
| `create_dashboard` | config (JSON) | dashboard_id |

### 4.2 MCP Client Implementation Pattern

```python
class SigNozMCPClient:
    def __init__(self, transport="stdio"):
        if transport == "stdio":
            self.process = subprocess.Popen(
                ["signoz-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
        elif transport == "http":
            self.base_url = "http://localhost:3301/mcp"

    def call_tool(self, tool_name: str, args: dict) -> dict:
        # MCP JSON-RPC call
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args},
            "id": str(uuid.uuid4())
        }
        # Send request, parse response
        return self._send_request(request)

    def query_traces(self, service: str, time_range: str = "now-5m"):
        return self.call_tool("query_traces", {
            "filters": {"service.name": service},
            "timeRange": {"from": time_range, "to": "now"}
        })

    # Fallback: direct SigNoz API (when MCP unavailable)
    def query_metrics_direct(self, query: str):
        # Direct HTTP call to SigNoz Query Service
        resp = requests.post(
            "http://localhost:3301/api/v1/query",
            json={"query": query}
        )
        return resp.json()
```

---

## 5. Prompt Engineering — LLM Templates

### 5.1 System Prompt (SRE Expert)

```python
SYSTEM_PROMPT = """You are an expert SRE engineer with 15 years of experience
debugging production systems. Given telemetry data from SigNoz (traces, metrics,
and logs), identify the root cause of the incident.

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
```

### 5.2 Diagnosis Prompt

```python
def build_diagnosis_prompt(alert: dict, traces: list, metrics: list, logs: list) -> str:
    return f"""
ALERT: {alert['alert_name']} ({alert['severity']})
SERVICE: {alert['labels'].get('service_name', 'unknown')}
TIME: {alert['starts_at']}

TRACES (last 5 min):
{json.dumps(traces[:5], indent=2)}

METRICS (last 5 min):
{json.dumps(metrics, indent=2)}

ERROR LOGS (last 5 min):
{json.dumps(logs[:5], indent=2)}

Analyze the above and respond in JSON format.
"""
```

---

## 6. Docker Fix Actions — Full Definitions

```python
FIX_ACTIONS = {
    "restart_container": {
        "description": "Restart a Docker container by service name",
        "required_params": ["service_name"],
        "timeout": 30,
        "verify": "container_uptime"
    },
    "scale_service": {
        "description": "Scale a Docker Compose service to N replicas",
        "required_params": ["service_name", "replicas"],
        "timeout": 60,
        "verify": "cpu_usage_drop"
    },
    "clear_cache": {
        "description": "Flush Redis cache or clear application cache",
        "required_params": ["cache_type", "host"],
        "timeout": 10,
        "verify": "memory_reduction"
    },
    "rollback_deployment": {
        "description": "Revert to previous Docker image tag",
        "required_params": ["service_name"],
        "timeout": 120,
        "verify": "error_rate_drop"
    }
}

def execute_fix(action_type: str, params: dict) -> dict:
    action = FIX_ACTIONS.get(action_type)
    if not action:
        return {"status": "error", "message": f"Unknown action: {action_type}"}

    client = docker.from_env()

    if action_type == "restart_container":
        container = client.containers.get(params["service_name"])
        container.restart(timeout=action["timeout"])
        return {"status": "success", "action": f"restarted {params['service_name']}"}

    elif action_type == "scale_service":
        # For Docker Compose: docker compose up -d --scale service=N
        subprocess.run([
            "docker", "compose", "up", "-d",
            "--scale", f"{params['service_name']}={params['replicas']}",
            "--no-recreate"
        ], check=True)
        return {"status": "success", "action": f"scaled {params['service_name']} to {params['replicas']}"}

    elif action_type == "clear_cache":
        if params["cache_type"] == "redis":
            redis_client = redis.Redis(host=params["host"])
            redis_client.flushall()
        return {"status": "success", "action": f"cleared {params['cache_type']} cache"}
```

---

## 7. Error Handling & Resilience Strategy

```python
RETRY_CONFIG = {
    "mcp_query": {"max_retries": 3, "backoff": [1, 2, 4], "timeout": 30},
    "llm_inference": {"max_retries": 2, "backoff": [5, 10], "timeout": 60},
    "docker_fix": {"max_retries": 2, "backoff": [5, 10], "timeout": 120}
}

CIRCUIT_BREAKERS = {
    "ollama": {
        "failure_threshold": 5,
        "reset_timeout_seconds": 60,
        "fallback": "rule_based_diagnosis"
    },
    "docker_api": {
        "failure_threshold": 3,
        "reset_timeout_seconds": 30,
        "fallback": "log_only"
    },
    "signoz_mcp": {
        "failure_threshold": 3,
        "reset_timeout_seconds": 30,
        "fallback": "direct_sigNoz_api"
    }
}
```

### 7.1 Rule-Based Fallback (When Ollama is Down)

```python
def rule_based_diagnosis(alert: dict, metrics: list) -> dict:
    # Simple heuristic rules when LLM is unavailable
    cpu_metrics = [m for m in metrics if "cpu" in m.get("query", "")]
    error_metrics = [m for m in metrics if "error" in m.get("query", "")]
    redis_metrics = [m for m in metrics if "redis" in m.get("query", "")]

    if any(m["value"] > 80 for m in cpu_metrics):
        return {"root_cause": "CPU overload detected", "suggested_fix": "scale_service"}

    if any(m["value"] > 0 for m in redis_metrics):
        return {"root_cause": "Redis errors detected", "suggested_fix": "restart_container",
                "fix_params": {"service_name": "redis"}}

    return {"root_cause": "Unknown (LLM unavailable)", "suggested_fix": "escalate"}
```

---

## 8. Complete docker-compose.yml

```yaml
version: "3.8"

networks:
  signoz-net:
    driver: bridge

services:
  signoz:
    image: signoz/foundry:latest
    command: signoz start
    networks: [signoz-net]
    ports:
      - "3301:3301"   # SigNoz UI + API
      - "4318:4318"   # OTLP HTTP
      - "4317:4317"   # OTLP gRPC
    volumes:
      - signoz-data:/var/lib/signoz
      - ./casting.yaml:/etc/signoz/casting.yaml

  sample-app:
    build: ./sample-app
    ports: ["8001:8001"]
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: http://signoz:4318
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/app
    networks: [signoz-net]
    depends_on: [signoz, redis, postgres]

  redis:
    image: redis:7-alpine
    networks: [signoz-net]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: agent_medic
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks: [signoz-net]
    ports: ["5432:5432"]

  agent-medic:
    build: ./agent-medic
    ports: ["8000:8000"]
    environment:
      SIGNOZ_MCP_ENABLED: "true"
      OLLAMA_BASE_URL: http://ollama:11434
      OLLAMA_MODEL: llama3.2
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/agent_medic
      DOCKER_HOST: unix:///var/run/docker.sock
      LOG_LEVEL: INFO
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks: [signoz-net]
    depends_on: [signoz, ollama, postgres]

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama_data:/root/.ollama
    networks: [signoz-net]
    deploy:
      resources:
        reservations:
          memory: 8G
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      retries: 3

  web-ui:
    build: ./web-ui
    ports: ["3000:80"]
    networks: [signoz-net]
    depends_on: [agent-medic]

volumes:
  signoz-data:
  pgdata:
  ollama_data:
```

---

## 9. Configuration & Environment

```bash
# .env.example
SIGNOZ_MCP_ENABLED=true
SIGNOZ_MCP_TRANSPORT=stdio        # stdio | http
SIGNOZ_API_URL=http://localhost:3301

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=60

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_medic

DOCKER_HOST=unix:///var/run/docker.sock

LOG_LEVEL=INFO

AGENT_WORKERS=3                    # concurrent incident processors
AGENT_DEDUP_WINDOW_MINUTES=5
AGENT_RATE_LIMIT_PER_MINUTE=10

NOTIFICATION_SLACK_WEBHOOK=        # optional
NOTIFICATION_EMAIL=                # optional
```

---

## 10. API Contract

| Method | Endpoint | Request | Response | Description |
|---|---|---|---|---|
| POST | `/webhook` | SigNoz alert JSON | `{"status": "accepted", "incident_id": "..."}` | Receive alert |
| GET | `/health` | — | `{"status": "healthy", "uptime": 123}` | Health check |
| GET | `/incidents` | `?page=1&limit=20` | `{"incidents": [...], "total": 50}` | List incidents |
| GET | `/incidents/{id}` | — | `{"incident": {...}, "diagnosis": {...}, "fix": {...}}` | Incident detail |
| GET | `/metrics` | — | `{"total": 50, "resolved": 45, "avg_time": 26}` | Agent metrics |
| WS | `/ws/events` | — | `{"type": "incident_update", "data": {...}}` | Real-time stream |

---

## 11. Project Structure (Final)

```
Track_1/
│
├── .env.example              # Environment template
├── .gitignore                # Python, Docker, IDE
├── LICENSE                   # MIT
├── README.md                 # Stellar documentation
├── casting.yaml              # Foundry config (MANDATORY)
├── casting.yaml.lock         # Foundry lock (MANDATORY)
├── docker-compose.yml        # Full stack (7 services)
│
├── sample-app/               # Buggy microservice
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                # FastAPI with /trigger/* endpoints
│   ├── instrument.py         # OTel SDK initialization
│   └── bugs/                 # 4 failure modules
│       ├── __init__.py
│       ├── high_cpu.py
│       ├── memory_leak.py
│       ├── db_timeout.py
│       └── random_errors.py
│
├── agent-medic/              # Core agent
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py               # FastAPI server startup
│   ├── config.py             # Environment config loader
│   │
│   ├── pipeline/             # Alert ingestion
│   │   ├── __init__.py
│   │   ├── queue.py          # Async incident queue
│   │   ├── dedup.py          # Duplicate alert detection
│   │   └── rate_limiter.py   # Rate limiting
│   │
│   ├── listeners/            # External event receivers
│   │   ├── __init__.py
│   │   └── alert_listener.py # SigNoz webhook handler
│   │
│   ├── mcp/                  # SigNoz MCP integration
│   │   ├── __init__.py
│   │   ├── client.py         # MCP protocol client (stdio + HTTP)
│   │   ├── queries.py        # Pre-built query templates
│   │   └── response_parser.py # Parse MCP responses
│   │
│   ├── llm/                  # LLM integration
│   │   ├── __init__.py
│   │   ├── engine.py         # LangGraph workflow
│   │   ├── prompts.py        # System + diagnosis prompts
│   │   ├── context_builder.py# Build LLM context from telemetry
│   │   ├── response_parser.py# Parse LLM JSON output
│   │   └── fallback.py       # Rule-based fallback
│   │
│   ├── fix/                  # Fix execution
│   │   ├── __init__.py
│   │   ├── executor.py       # Fix action dispatcher
│   │   ├── actions.py        # 4 fix action implementations
│   │   ├── docker_client.py  # Docker SDK wrapper
│   │   └── health_verifier.py# Post-fix health check
│   │
│   ├── logging/              # Logging + notification
│   │   ├── __init__.py
│   │   ├── incident_logger.py# Log to SigNoz + DB
│   │   ├── notifier.py       # WebSocket + optional Slack
│   │   └── metrics_collector.py # Self-metrics
│   │
│   ├── db/                   # Database layer
│   │   ├── __init__.py
│   │   ├── models.py         # SQLAlchemy models
│   │   └── repository.py     # CRUD operations
│   │
│   └── api/                  # REST + WebSocket
│       ├── __init__.py
│       ├── routes.py         # All API endpoints
│       ├── schemas.py        # Pydantic request/response models
│       └── websocket.py      # WebSocket event manager
│
├── web-ui/                   # Agent dashboard
│   ├── Dockerfile
│   ├── index.html
│   ├── style.css
│   └── app.js                # WebSocket + UI logic
│
├── scripts/                  # Utilities
│   ├── setup.sh              # One-click env setup
│   ├── seed-data.sh          # Load sample data
│   ├── load-test.sh          # Locust load test
│   └── demo.sh               # Automated demo sequence
│
└── tests/                    # 50 tests
    ├── conftest.py
    ├── test_mcp_client.py    # 5 tests
    ├── test_llm_engine.py    # 5 tests
    ├── test_fix_executor.py  # 5 tests
    ├── test_pipeline.py      # 5 tests
    └── test_integration.py   # 30 tests
```

---

## 12. Demo Timeline — End to End

```
TIME    EVENT                           SYSTEM STATE
─────   ─────────────────────────────── ─────────────────────────
 0:00   Web UI open                     Dashboard: Healthy, 0 incidents
 0:05   Click "Trigger Redis Crash"     Sample App: Redis unavailable
 0:08   500 errors in logs              OTel sends error traces to SigNoz
 0:10   ALERT FIRES                     SigNoz: "Critical — Redis errors"
 0:11   Webhook POST /webhook           Agent: Incident #1 created
 0:12   MCP Query: traces               Fetching error traces from SigNoz
 0:14   MCP Query: metrics              Fetching CPU, memory, error rate
 0:15   MCP Query: logs                 Fetching error logs
 0:16   LLM analysis starts             Ollama: processing telemetry data
 0:18   LLM diagnosis complete          Root cause: Redis pool exhausted
 0:19   Fix plan: restart_container     Suggested action + params ready
 0:20   Docker API: restart redis        Container restart initiated
 0:22   Container restarted             Redis: ready to accept connections
 0:23   Verify: MCP query error rate    SigNoz: error rate dropped to 0%
 0:24   Fix verified ✅                  Health verifier: confirmed
 0:25   Incident logged to SigNoz       Custom log pushed + alert resolved
 0:26   Web UI updates                  "Incident #1 — Resolved in 26s"
 0:30   Demo complete                   Full cycle visible in UI + logs
```

---

*Revised architecture for Agents of SigNoz Hackathon 2026*
*Team Enthusiast — Rudra & Het Patel*
