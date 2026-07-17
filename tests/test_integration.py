import pytest


class TestIntegration:
    def test_config_loaded(self):
        from agent_medic.config import config
        assert config is not None
        assert config.OLLAMA_MODEL == "llama3.2"

    def test_ollama_client_init(self):
        from agent_medic.llm.engine import ollama_client
        assert ollama_client is not None

    def test_rule_based_fallback_cpu(self):
        from agent_medic.llm.engine import RuleBasedFallback
        fb = RuleBasedFallback()
        result = fb.diagnose(
            {"severity": "warning"},
            [{"query": "cpu_utilization", "value": 90}]
        )
        assert result["suggested_fix"] == "scale_service"

    def test_rule_based_fallback_redis(self):
        from agent_medic.llm.engine import RuleBasedFallback
        fb = RuleBasedFallback()
        result = fb.diagnose(
            {"severity": "critical"},
            [{"query": "redis_errors_total", "value": 5}]
        )
        assert result["suggested_fix"] == "restart_container"

    def test_metrics_collector(self):
        from agent_medic.logging.metrics_collector import metrics_collector
        metrics_collector.increment("incidents_total")
        snap = metrics_collector.snapshot()
        assert snap["incidents_total"] >= 1

    def test_notifier_init(self):
        from agent_medic.logging.notifier import notifier
        assert notifier is not None
