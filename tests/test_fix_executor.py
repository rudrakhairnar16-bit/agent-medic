import pytest


class TestFixExecutor:
    def test_supported_actions(self):
        from agent_medic.fix.actions import get_supported_actions
        actions = get_supported_actions()
        assert "restart_container" in actions
        assert "scale_service" in actions
        assert "clear_cache" in actions

    def test_validate_action_valid(self):
        from agent_medic.fix.actions import validate_action
        assert validate_action("restart_container", {"service_name": "redis"}) is True
        assert validate_action("scale_service", {"service_name": "app", "replicas": 3}) is True

    def test_validate_action_invalid(self):
        from agent_medic.fix.actions import validate_action
        assert validate_action("restart_container", {}) is False
        assert validate_action("unknown_action", {}) is False

    def test_docker_client_init(self):
        from agent_medic.fix.docker_client import docker_client
        assert docker_client is not None

    def test_health_verifier_init(self):
        from agent_medic.fix.health_verifier import HealthVerifier
        hv = HealthVerifier()
        assert hv is not None
