import json, subprocess, uuid, httpx

class MCPClient:
    def __init__(self, transport="stdio", base_url=None):
        self.transport = transport
        self.base_url = base_url or "http://localhost:3301"
        self.process = None

    def connect(self):
        if self.transport == "stdio":
            self.process = subprocess.Popen(["signoz-mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def _send(self, req):
        if self.transport == "stdio" and self.process:
            self.process.stdin.write(json.dumps(req) + "\n"); self.process.stdin.flush()
            return json.loads(self.process.stdout.readline())
        return httpx.post(f"{self.base_url}/mcp", json=req, timeout=30).json()

    def call_tool(self, name, args):
        return self._send({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name, "arguments": args}, "id": str(uuid.uuid4())})

    def query_traces(self, svc, tr="now-5m"):
        return self.call_tool("query_traces", {"filters": {"service.name": svc}, "timeRange": {"from": tr, "to": "now"}})

    def query_metrics(self, q, tr="now-5m"):
        return self.call_tool("query_metrics", {"query": q, "timeRange": {"from": tr, "to": "now"}})

    def query_logs(self, svc, tr="now-5m"):
        return self.call_tool("query_logs", {"filters": {"service": svc}, "timeRange": {"from": tr, "to": "now"}})

    def close(self):
        if self.process: self.process.terminate()

mcp_client = MCPClient()

class SigNozAPI:
    def __init__(self, base_url="http://localhost:3301"): self.base_url = base_url
    def query(self, q): return httpx.post(f"{self.base_url}/api/v1/query", json={"query": q}, timeout=30).json()
    def get_services(self): return httpx.get(f"{self.base_url}/api/v1/services", timeout=30).json()

signoz_api = SigNozAPI()

QUERY_TEMPLATES = {
    "error_traces": {"tool": "query_traces", "args_template": {"filters": {"service.name": "{service}", "status.code": "ERROR"}, "timeRange": {"from": "{time_range}", "to": "now"}, "limit": 10}},
    "cpu_metrics": {"tool": "query_metrics", "args_template": {"query": "avg(system_cpu_utilization{service='{service}'})", "timeRange": {"from": "{time_range}", "to": "now"}}},
    "error_rate": {"tool": "query_metrics", "args_template": {"query": "sum(rate(signoz_latency_count{status_code=~'5..'}[5m]))", "timeRange": {"from": "{time_range}", "to": "now"}}},
    "error_logs": {"tool": "query_logs", "args_template": {"filters": {"service": "{service}", "severity": "error"}, "timeRange": {"from": "{time_range}", "to": "now"}, "limit": 20}},
    "redis_metrics": {"tool": "query_metrics", "args_template": {"query": "rate(redis_errors_total{service='{service}'}[5m])", "timeRange": {"from": "{time_range}", "to": "now"}}},
}

class MCPResponseParser:
    @staticmethod
    def parse_traces(r): return r.get("result", []) if isinstance(r.get("result"), list) else []
    @staticmethod
    def parse_metrics(r): return r.get("result", []) if isinstance(r.get("result"), list) else []
    @staticmethod
    def parse_logs(r): return r.get("result", []) if isinstance(r.get("result"), list) else []
    @staticmethod
    def has_error(r): return "error" in r or "Error" in str(r)

parser = MCPResponseParser()
