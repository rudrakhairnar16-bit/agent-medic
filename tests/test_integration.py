import pytest
import asyncio


class TestIntegration:
    @pytest.mark.P0
    def test_config_loaded(self):
        from agent_medic.config import config
        assert config is not None
        assert config.OLLAMA_MODEL == "llama3.2"

    @pytest.mark.P0
    def test_worker_init(self):
        from agent_medic.worker import pipeline_worker
        assert pipeline_worker is not None
        assert pipeline_worker.n == 3

    @pytest.mark.P0
    def test_ollama_client_init(self):
        from agent_medic.llm.engine import ollama_client
        assert ollama_client is not None

    @pytest.mark.P1
    def test_rule_based_fallback_cpu(self):
        from agent_medic.llm.engine import RuleBasedFallback
        fb = RuleBasedFallback()
        result = fb.diagnose(
            {"severity": "warning"},
            [{"query": "cpu_utilization", "value": 90}]
        )
        assert result["suggested_fix"] == "scale_service"

    @pytest.mark.P0
    def test_rule_based_fallback_redis(self):
        from agent_medic.llm.engine import RuleBasedFallback
        fb = RuleBasedFallback()
        result = fb.diagnose(
            {"severity": "critical"},
            [{"query": "redis_errors_total", "value": 5}]
        )
        assert result["suggested_fix"] == "restart_container"

    @pytest.mark.P1
    def test_metrics_collector(self):
        from agent_medic.incidents.metrics_collector import metrics_collector
        metrics_collector.increment("incidents_total")
        snap = metrics_collector.snapshot()
        assert snap["incidents_total"] >= 1

    @pytest.mark.P2
    def test_notifier_init(self):
        from agent_medic.incidents.notifier import notifier
        assert notifier is not None

    @pytest.mark.P0
    def test_pipeline_end_to_end_demo(self):
        """Full pipeline: enqueue incident -> worker processes without crash."""
        # Use short import path to match simulated/__init__.py to avoid double-import
        from pipeline.queue import incident_queue
        from worker import PipelineWorker
        from incidents.metrics_collector import metrics_collector

        # Clear stale items from module-level queue (left by prior tests)
        incident_queue.queue._queue.clear()

        metrics_collector.reset()
        worker = PipelineWorker(n=1)

        async def run():
            await worker.start()
            await incident_queue.enqueue({
                "incident_id": "e2e-test-001",
                "body": {"scenario": "redis_crash", "alert_id": "alert-001"},
                "retry_count": 0
            })
            await asyncio.sleep(5)
            await worker.stop()

        asyncio.run(run())
        snap = metrics_collector.snapshot()
        assert snap["fix_attempts"] >= 1, "Worker should have attempted a fix"
        assert snap["fix_successes"] >= 1, "Worker should have succeeded in sim mode"

    @pytest.mark.P1
    def test_simulated_mcp_scenario_aware(self):
        """SimulatedMCPClient returns correct data per scenario."""
        from agent_medic.simulated import SimulatedMCPClient
        from agent_medic.simulated.data import simulated_data

        client = SimulatedMCPClient(scenario="cpu_spike")
        data = client.query_metrics()
        metrics = data["result"]
        cpu = next((m for m in metrics if "cpu" in str(m.get("query", "")).lower()), None)
        assert cpu is not None
        assert cpu["value"] > 80

        client.set_scenario("disk_full")
        data = client.query_metrics()
        metrics = data["result"]
        disk = next((m for m in metrics if "disk" in str(m.get("query", "")).lower()), None)
        assert disk is not None
        assert disk["value"] > 90

    @pytest.mark.P1
    def test_fallback_rule_expanded_cover_all_scenarios(self):
        """All 11 rules in fallback return a valid fix."""
        from agent_medic.llm.engine import RuleBasedFallback
        from agent_medic.simulated.data import simulated_data

        fb = RuleBasedFallback()
        for name in simulated_data.get_scenario_names():
            data = simulated_data.get_data(name)
            result = fb.diagnose(
                {"severity": "warning"},
                data["metrics"],
                data["logs"]
            )
            assert result["suggested_fix"] in (
                "restart_container", "scale_service", "clear_cache", "escalate"
            ), f"{name} returned invalid fix: {result['suggested_fix']}"
