from fix.actions import validate_action, get_supported_actions
from fix.docker_client import docker_client
from fix.health_verifier import HealthVerifier
import asyncio


class FixExecutor:
    def __init__(self):
        self.health_verifier = HealthVerifier()

    async def execute(self, action_type: str, params: dict) -> dict:
        if not validate_action(action_type, params):
            return {"status": "error", "message": f"Invalid action: {action_type}"}

        if action_type == "restart_container":
            result = docker_client.restart_container(
                params["service_name"]
            )
        elif action_type == "scale_service":
            result = docker_client.scale_service(
                params["service_name"],
                int(params.get("replicas", 3))
            )
        elif action_type == "clear_cache":
            result = docker_client.clear_cache(
                params.get("cache_type", "redis"),
                params.get("host", "localhost")
            )
        else:
            return {"status": "error", "message": f"Unknown action: {action_type}"}

        if result["status"] == "success":
            await asyncio.sleep(3)
            verified = self.health_verifier.verify(action_type, params)
            result["verified"] = verified
        else:
            result["verified"] = False

        return result


executor = FixExecutor()
