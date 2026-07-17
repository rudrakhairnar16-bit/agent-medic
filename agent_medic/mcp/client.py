import json
import subprocess
import uuid
from typing import Optional


class MCPClient:
    def __init__(self, transport: str = "stdio", base_url: Optional[str] = None):
        self.transport = transport
        self.base_url = base_url or "http://localhost:3301"
        self.process: Optional[subprocess.Popen] = None

    def connect(self):
        if self.transport == "stdio":
            self.process = subprocess.Popen(
                ["signoz-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

    def call_tool(self, tool_name: str, args: dict) -> dict:
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args},
            "id": str(uuid.uuid4())
        }
        return self._send(request)

    def _send(self, request: dict) -> dict:
        if self.transport == "stdio" and self.process:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            response = self.process.stdout.readline()
            return json.loads(response)
        else:
            import httpx
            resp = httpx.post(
                f"{self.base_url}/mcp",
                json=request,
                timeout=30
            )
            return resp.json()

    def query_traces(self, service: str, time_range: str = "now-5m") -> dict:
        return self.call_tool("query_traces", {
            "filters": {"service.name": service},
            "timeRange": {"from": time_range, "to": "now"}
        })

    def query_metrics(self, query: str, time_range: str = "now-5m") -> dict:
        return self.call_tool("query_metrics", {
            "query": query,
            "timeRange": {"from": time_range, "to": "now"}
        })

    def query_logs(self, service: str, time_range: str = "now-5m") -> dict:
        return self.call_tool("query_logs", {
            "filters": {"service": service},
            "timeRange": {"from": time_range, "to": "now"}
        })

    def close(self):
        if self.process:
            self.process.terminate()


mcp_client = MCPClient()

# Direct SigNoz API fallback
class SigNozAPI:
    def __init__(self, base_url: str = "http://localhost:3301"):
        self.base_url = base_url

    def query(self, query: str) -> dict:
        import httpx
        resp = httpx.post(
            f"{self.base_url}/api/v1/query",
            json={"query": query},
            timeout=30
        )
        return resp.json()

    def get_services(self) -> dict:
        import httpx
        resp = httpx.get(f"{self.base_url}/api/v1/services", timeout=30)
        return resp.json()


signoz_api = SigNozAPI()
