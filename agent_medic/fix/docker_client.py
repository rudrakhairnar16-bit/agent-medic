import docker
from docker.errors import DockerException, NotFound, APIError


class DockerClient:
    def __init__(self, base_url: str = "unix:///var/run/docker.sock"):
        self.base_url = base_url
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = docker.from_env()
            except Exception:
                try:
                    self._client = docker.DockerClient(base_url=self.base_url)
                except Exception:
                    self._client = None
        return self._client

    def _ensure_available(self):
        if self.client is None:
            return {"status": "error", "message": "Docker daemon not available"}
        return None

    def restart_container(self, service_name: str, timeout: int = 30) -> dict:
        err = self._ensure_available()
        if err:
            return err
        try:
            container = self.client.containers.get(service_name)
            container.restart(timeout=timeout)
            return {"status": "success", "message": f"Restarted {service_name}"}
        except NotFound:
            containers = self.client.containers.list(filters={"name": service_name})
            if containers:
                containers[0].restart(timeout=timeout)
                return {"status": "success", "message": f"Restarted {service_name}"}
            return {"status": "error", "message": f"Container {service_name} not found"}
        except APIError as e:
            return {"status": "error", "message": str(e)}

    def scale_service(self, service_name: str, replicas: int = 3) -> dict:
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d", "--scale", f"{service_name}={replicas}", "--no-recreate"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return {"status": "success", "message": f"Scaled {service_name} to {replicas}"}
            return {"status": "error", "message": result.stderr}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Scale operation timed out"}

    def clear_cache(self, cache_type: str, host: str = "localhost") -> dict:
        if cache_type == "redis":
            import redis
            try:
                r = redis.Redis(host=host, socket_timeout=5)
                r.flushall()
                return {"status": "success", "message": "Redis cache cleared"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error", "message": f"Unknown cache type: {cache_type}"}


docker_client = DockerClient()
