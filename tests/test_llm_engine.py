import pytest


class TestLLMEngine:
    @pytest.mark.P0
    def test_prompt_builder(self):
        from agent_medic.llm.prompts import build_diagnosis_prompt
        alert = {"alert_name": "test", "severity": "critical"}
        prompt = build_diagnosis_prompt(alert, [], [], [])
        assert "ALERT: test" in prompt
        assert "TRACES" in prompt
        assert "METRICS" in prompt
        assert "LOGS" in prompt

    @pytest.mark.P0
    def test_system_prompt_exists(self):
        from agent_medic.llm.prompts import SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 100
        assert "SRE engineer" in SYSTEM_PROMPT
        assert "JSON" in SYSTEM_PROMPT

    @pytest.mark.P1
    def test_context_builder(self):
        from agent_medic.llm.context_builder import context_builder
        context = context_builder.build_context({"alert_name": "test"}, [], [], [])
        assert "test" in context

    @pytest.mark.P0
    def test_response_parser_valid(self):
        from agent_medic.llm.response_parser import response_parser
        result = response_parser.parse('{"root_cause": "test", "confidence": 0.9}')
        assert result["root_cause"] == "test"
        assert result["confidence"] == 0.9

    @pytest.mark.P1
    def test_response_parser_invalid(self):
        from agent_medic.llm.response_parser import response_parser
        result = response_parser.parse("not json")
        assert result["root_cause"] == "Failed to parse LLM response"

    @pytest.mark.P1
    def test_tool_use_loop_with_mcp_client(self):
        from agent_medic.llm.engine import OllamaClient, _parse_llm
        from agent_medic.simulated import SimulatedMCPClient
        mcp = SimulatedMCPClient(scenario="redis_crash")
        client = OllamaClient()
        alert = {"alert_name": "Redis Down", "severity": "critical", "labels": {"service_name": "redis"}}
        result = client._execute_tool({"type": "metrics", "target": "avg(redis_memory_usage)"}, mcp)
        assert result is not None
        assert result["type"] == "metrics"
        assert "result" in result
        result2 = client._execute_tool({"type": "logs", "target": "redis"}, mcp)
        assert result2 is not None
        assert result2["type"] == "logs"
        result3 = client._execute_tool({"type": "traces", "target": "redis"}, mcp)
        assert result3 is not None
        assert result3["type"] == "traces"
        result4 = client._execute_tool({"type": "unknown", "target": "x"}, mcp)
        assert result4 is None
