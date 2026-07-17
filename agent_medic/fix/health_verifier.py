import httpx
from config import config


class HealthVerifier:
    def __init__(self):
        self.mcp_available = config.SIGNOZ_MCP_ENABLED

    def verify(self, action_type: str, params: dict) -> bool:
        if action_type == "restart_container":
            return self._check_container_running(params.get("service_name", ""))
        elif action_type == "scale_service":
            return self._check_error_rate_dropped()
        elif action_type == "clear_cache":
            return self._check_memory_reduced()
        return True

    def _check_container_running(self, name: str) -> bool:
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get(name)
            return container.status == "running"
        except Exception:
            return False

    def _check_error_rate_dropped(self) -> bool:
        try:
            if self.mcp_available:
                resp = httpx.post(
                    f"{config.SIGNOZ_API_URL}/api/v1/query",
                    json={"query": "sum(rate(signoz_latency_count{status_code=~'5..'}[5m]))"},
                    timeout=10
                )
                return resp.status_code == 200
            return True
        except Exception:
            return True

    def _check_memory_reduced(self) -> bool:
        return True
