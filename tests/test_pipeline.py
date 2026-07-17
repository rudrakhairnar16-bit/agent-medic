import pytest


class TestPipeline:
    def test_queue_enqueue_dequeue(self):
        import asyncio
        from agent_medic.pipeline.queue import IncidentQueue

        q = IncidentQueue()
        asyncio.run(q.enqueue({"test": "data"}))
        result = asyncio.run(q.dequeue())
        assert result["test"] == "data"

    def test_dedup_new_alert(self):
        from agent_medic.pipeline.dedup import Deduplicator
        d = Deduplicator(window_minutes=5)
        assert d.is_duplicate("alert_1") is False

    def test_dedup_duplicate_alert(self):
        from agent_medic.pipeline.dedup import Deduplicator
        d = Deduplicator(window_minutes=5)
        d.is_duplicate("alert_1")
        assert d.is_duplicate("alert_1") is True

    def test_rate_limiter_allows(self):
        from agent_medic.pipeline.rate_limiter import RateLimiter
        r = RateLimiter(max_per_minute=10)
        for _ in range(10):
            assert r.allow() is True

    def test_rate_limiter_blocks(self):
        from agent_medic.pipeline.rate_limiter import RateLimiter
        r = RateLimiter(max_per_minute=3)
        for _ in range(3):
            r.allow()
        assert r.allow() is False
