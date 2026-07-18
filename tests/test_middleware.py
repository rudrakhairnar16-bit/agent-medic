import pytest, time

class TestMiddleware:
    @pytest.mark.P2
    def test_webhook_rate_imports(self):
        from agent_medic.api.middleware import webhook_calls, WEBHOOK_RATE, WEBHOOK_WINDOW, check_webhook_rate
        assert WEBHOOK_RATE == 20
        assert WEBHOOK_WINDOW == 60
        assert webhook_calls is not None
        assert check_webhook_rate is not None

    @pytest.mark.P2
    def test_webhook_rate_allows(self):
        from agent_medic.api.middleware import webhook_calls, check_webhook_rate
        webhook_calls.clear()
        assert check_webhook_rate("1.2.3.4") is True
        webhook_calls.clear()

    @pytest.mark.P2
    def test_webhook_rate_blocks(self):
        from agent_medic.api.middleware import webhook_calls, check_webhook_rate
        webhook_calls.clear()
        ip = "5.6.7.8"
        for _ in range(20):
            check_webhook_rate(ip)
        assert check_webhook_rate(ip) is False
        webhook_calls.clear()
