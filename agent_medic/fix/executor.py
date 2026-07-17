import docker, subprocess, asyncio, httpx, logging
from docker.errors import NotFound, APIError
from config import config

logger = logging.getLogger(__name__)

ACTIONS = {
    "restart_container": {"required": ["service_name"], "timeout": 30},
    "scale_service": {"required": ["service_name", "replicas"], "timeout": 60},
    "clear_cache": {"required": ["cache_type", "host"], "timeout": 10},
}

def validate_action(t, params):
    a = ACTIONS.get(t)
    return bool(a and all(p in params for p in a["required"]))

class DockerClient:
    def __init__(self): self._client = None
    @property
    def client(self):
        if self._client is None:
            try:
                self._client = docker.from_env()
            except docker.errors.DockerException as e:
                if config.DOCKER_HOST:
                    try:
                        self._client = docker.DockerClient(base_url=config.DOCKER_HOST)
                    except docker.errors.DockerException:
                        self._client = None
                        logger.warning("Docker unavailable: %s", e)
                    else:
                        return self._client
                self._client = None
                logger.warning("Docker unavailable: %s", e)
        return self._client

    def restart(self, name, timeout=30):
        if not self.client: return {"status":"error","message":"Docker unavailable"}
        try:
            (self.client.containers.get(name) or self.client.containers.list(filters={"name":name})[0]).restart(timeout=timeout)
            return {"status":"success","message":f"Restarted {name}"}
        except (NotFound, IndexError): return {"status":"error","message":f"{name} not found"}
        except APIError as e: return {"status":"error","message":str(e)}

    def scale(self, name, replicas=3):
        try:
            r = subprocess.run(["docker","compose","-f",config.COMPOSE_FILE,"up","-d","--scale",f"{name}={replicas}","--no-recreate"], capture_output=True, text=True, timeout=60)
            return {"status":"success" if r.returncode==0 else "error","message":f"Scaled {name} to {replicas}" if r.returncode==0 else r.stderr}
        except subprocess.TimeoutExpired: return {"status":"error","message":"Timeout"}

    def clear_cache(self, cache_type="redis", host="localhost"):
        if cache_type != "redis": return {"status":"error","message":f"Unknown: {cache_type}"}
        try:
            import redis as r
            r.Redis(host=host, socket_timeout=5).flushall()
            return {"status":"success","message":"Cache cleared"}
        except Exception as e: return {"status":"error","message":str(e)}

docker_client = DockerClient()

class HealthVerifier:
    def verify(self, action, params):
        if action == "restart_container":
            c = docker_client.client
            if not c: return False
            try:
                return c.containers.get(params.get("service_name", "")).status == "running"
            except NotFound:
                return False
            except Exception as e:
                logger.warning("Health check failed: %s", e)
                return False
        if action == "scale_service":
            try:
                r = httpx.get(f"http://{params.get('service_name', 'localhost')}:8000/health", timeout=5)
                return r.status_code == 200
            except Exception:
                return False
        return True

class FixExecutor:
    async def execute(self, action, params):
        if not validate_action(action, params): return {"status":"error","message":f"Invalid: {action}"}
        fn = {"restart_container": lambda: docker_client.restart(params["service_name"]),
              "scale_service": lambda: docker_client.scale(params["service_name"], int(params.get("replicas",3))),
              "clear_cache": lambda: docker_client.clear_cache(params.get("cache_type","redis"), params.get("host","localhost"))}.get(action)
        if not fn: return {"status":"error","message":f"Unknown: {action}"}
        result = fn()
        if result["status"] == "success":
            await asyncio.sleep(3)
            result["verified"] = HealthVerifier().verify(action, params)
        else: result["verified"] = False
        return result

executor = FixExecutor()
