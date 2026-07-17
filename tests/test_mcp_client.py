import pytest


class TestMCPClient:
    def test_mcp_connect(self):
        from agent_medic.mcp.client import mcp_client
        assert mcp_client is not None

    def test_mcp_has_tools(self):
        from agent_medic.mcp.queries import QUERY_TEMPLATES
        assert len(QUERY_TEMPLATES) >= 3
        assert "error_traces" in QUERY_TEMPLATES
        assert "cpu_metrics" in QUERY_TEMPLATES
        assert "error_logs" in QUERY_TEMPLATES

    def test_signoz_api_fallback_exists(self):
        from agent_medic.mcp.client import signoz_api
        assert signoz_api is not None

    def test_parser_traces(self):
        from agent_medic.mcp.response_parser import parser
        result = parser.parse_traces({"result": [{"trace_id": "abc"}]})
        assert len(result) == 1

    def test_parser_error_detection(self):
        from agent_medic.mcp.response_parser import parser
        assert parser.has_error({"error": "something"}) is True
        assert parser.has_error({"result": "ok"}) is False
