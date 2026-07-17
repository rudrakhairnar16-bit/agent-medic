import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent_medic"))


class TestDemoMode:
    """P1 tests for simulated clients and demo trigger."""

    @pytest.fixture(autouse=True)
    def setup_demo(self):
        with patch("config.config.DEMO_MODE", True):
            yield

    def test_simulated_mcp_client_returns_data(self):
        from simulated import SimulatedMCPClient
        client = SimulatedMCPClient()
        traces = client.query_traces()
        assert "result" in traces
        assert traces["simulated"] is True
        assert len(traces["result"]) > 0

    def test_simulated_mcp_returns_metrics(self):
        from simulated import SimulatedMCPClient
        client = SimulatedMCPClient()
        metrics = client.query_metrics()
        assert "result" in metrics
        assert len(metrics["result"]) > 0

    def test_simulated_mcp_returns_logs(self):
        from simulated import SimulatedMCPClient
        client = SimulatedMCPClient()
        logs = client.query_logs()
        assert "result" in logs
        assert len(logs["result"]) > 0

    def test_simulated_fix_executor_returns_success(self):
        import asyncio
        from simulated import SimulatedFixExecutor
        fixer = SimulatedFixExecutor()
        result = asyncio.run(fixer.execute("restart_container", {"service": "redis"}))
        assert result["status"] == "success"
        assert result["simulated"] is True
        assert result["verified"] is True

    def test_simulated_fix_executor_supports_all_actions(self):
        import asyncio
        from simulated import SimulatedFixExecutor
        fixer = SimulatedFixExecutor()
        for action in ["restart_container", "scale_service", "clear_cache"]:
            result = asyncio.run(fixer.execute(action, {}))
            assert result["status"] == "success"

    def test_simulated_ollama_diagnosis_returns_dict(self):
        from simulated import SimulatedOllamaClient
        from simulated.data import simulated_data
        llm = SimulatedOllamaClient()
        data = simulated_data.get_data("redis_crash")
        diagnosis = llm.diagnose(
            {"scenario": "redis_crash"},
            data["traces"], data["metrics"], data["logs"]
        )
        assert "root_cause" in diagnosis
        assert "confidence" in diagnosis
        assert "suggested_fix" in diagnosis
        assert diagnosis["simulated"] is True

    def test_simulated_ollama_all_scenarios(self):
        from simulated import SimulatedOllamaClient
        from simulated.data import simulated_data
        llm = SimulatedOllamaClient()
        for name in simulated_data.get_scenario_names():
            data = simulated_data.get_data(name)
            diagnosis = llm.diagnose(
                {"scenario": name},
                data["traces"], data["metrics"], data["logs"]
            )
            assert diagnosis["suggested_fix"] in (
                "restart_container", "scale_service", "clear_cache", "escalate"
            )

    def test_simulated_get_deps_returns_all_clients(self):
        from simulated import get_simulated_deps
        deps = get_simulated_deps()
        assert "mcp" in deps
        assert "fix" in deps
        assert "llm" in deps

    def test_simulated_data_has_expected_fields(self):
        from simulated.data import simulated_data
        for name in simulated_data.get_scenario_names():
            data = simulated_data.get_data(name)
            for key in ("traces", "metrics", "logs", "expected_diagnosis"):
                assert key in data, f"{name} missing {key}"

    def test_simulated_data_all_scenarios_loadable(self):
        from simulated.data import simulated_data
        names = simulated_data.get_scenario_names()
        assert len(names) >= 10
        assert "redis_crash" in names
        assert "cpu_spike" in names
        assert "db_timeout" in names
        assert "random_500s" in names
        assert "network_partition" in names
        assert "disk_full" in names
        assert "memory_leak" in names
        assert "slow_queries" in names
        assert "tls_cert_expiry" in names
        assert "oom_kill" in names
        assert "cascading_failure" in names
