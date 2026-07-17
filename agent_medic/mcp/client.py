import httpx, logging
from config import config

logger = logging.getLogger(__name__)


class SigNozAPI:
    """HTTP client for SigNoz Foundry's REST API."""

    def __init__(self, base_url=""):
        self.base_url = base_url or config.SIGNOZ_API_URL
        self._http = httpx.Client(timeout=30)

    def _post(self, path, body):
        try:
            resp = self._http.post(f"{self.base_url}{path}", json=body)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning("SigNozAPI %s failed: %s", path, e)
            return {"error": str(e), "result": []}

    def query(self, q):
        return self._post("/api/v1/query", {"query": q})

    def query_traces(self, svc="", time_range="now-5m"):
        return self._post("/api/v1/traces", {
            "filters": {"service.name": svc} if svc else {},
            "timeRange": {"from": time_range, "to": "now"}, "limit": 20
        })

    def query_metrics(self, q="", time_range="now-5m"):
        return self._post("/api/v1/query", {"query": q, "timeRange": {"from": time_range, "to": "now"}})

    def query_logs(self, svc="", time_range="now-5m"):
        return self._post("/api/v1/logs", {
            "filters": {"service": svc} if svc else {},
            "timeRange": {"from": time_range, "to": "now"}, "limit": 20
        })

    def get_services(self):
        return self._post("/api/v1/services", {})


signoz_api = SigNozAPI(base_url=config.SIGNOZ_API_URL)

# Alias for backward compatibility with worker.py
mcp_client = signoz_api


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

QUERY_TEMPLATES = {
    "error_traces": {"tool": "query_traces", "args_template": {"svc": "{service}", "time_range": "{time_range}"}},
    "cpu_metrics": {"tool": "query_metrics", "args_template": {"q": "avg(system_cpu_utilization{service='{service}'})", "time_range": "{time_range}"}},
    "error_rate": {"tool": "query_metrics", "args_template": {"q": "sum(rate(signoz_latency_count{status_code=~'5..'}[5m]))", "time_range": "{time_range}"}},
    "error_logs": {"tool": "query_logs", "args_template": {"svc": "{service}", "time_range": "{time_range}"}},
    "redis_metrics": {"tool": "query_metrics", "args_template": {"q": "rate(redis_errors_total{service='{service}'}[5m])", "time_range": "{time_range}"}},
}
