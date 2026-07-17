import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent_medic"))

from pipeline.queue import IncidentQueue, Deduplicator, RateLimiter, AlertCorrelator, incident_queue, deduplicator, rate_limiter


class TestPipeline:
    @pytest.mark.P0
    def test_queue_enqueue_dequeue(self):
        import asyncio
        q = IncidentQueue()
        asyncio.run(q.enqueue({"id": 1}))
        asyncio.run(q.enqueue({"id": 2}))
        assert asyncio.run(q.dequeue()) == {"id": 1}
        assert asyncio.run(q.dequeue()) == {"id": 2}

    @pytest.mark.P0
    def test_dedup_new_alert(self):
        d = Deduplicator(window=0.1)
        assert d.is_duplicate("alert_1") is False

    @pytest.mark.P0
    def test_dedup_duplicate_alert(self):
        d = Deduplicator(window=5)
        d.is_duplicate("alert_1")
        assert d.is_duplicate("alert_1") is True

    @pytest.mark.P0
    def test_rate_limiter_allows(self):
        r = RateLimiter(max_per_min=10)
        for _ in range(10):
            assert r.allow() is True

    @pytest.mark.P0
    def test_rate_limiter_blocks(self):
        r = RateLimiter(max_per_min=3)
        for _ in range(3):
            r.allow()
        assert r.allow() is False
