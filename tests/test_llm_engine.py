import pytest


class TestLLMEngine:
    def test_prompt_builder(self):
        from agent_medic.llm.prompts import build_diagnosis_prompt
        alert = {"alert_name": "test", "severity": "critical"}
        prompt = build_diagnosis_prompt(alert, [], [], [])
        assert "ALERT: test" in prompt
        assert "TRACES" in prompt
        assert "METRICS" in prompt
        assert "LOGS" in prompt

    def test_system_prompt_exists(self):
        from agent_medic.llm.prompts import SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 100
        assert "SRE engineer" in SYSTEM_PROMPT
        assert "JSON" in SYSTEM_PROMPT

    def test_context_builder(self):
        from agent_medic.llm.context_builder import context_builder
        context = context_builder.build_context({"alert_name": "test"}, [], [], [])
        assert "test" in context

    def test_response_parser_valid(self):
        from agent_medic.llm.response_parser import response_parser
        result = response_parser.parse('{"root_cause": "test", "confidence": 0.9}')
        assert result["root_cause"] == "test"
        assert result["confidence"] == 0.9

    def test_response_parser_invalid(self):
        from agent_medic.llm.response_parser import response_parser
        result = response_parser.parse("not json")
        assert result["root_cause"] == "Failed to parse LLM response"
