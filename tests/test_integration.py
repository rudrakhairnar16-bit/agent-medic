import pytest


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
        assert pipeline_worker.num_workers == 3

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
