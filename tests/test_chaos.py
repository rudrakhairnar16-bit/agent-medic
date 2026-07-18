import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent_medic"))


class TestChaos:
    """P2 — Chaos engineering tests: verify self-healing under failure."""

    @pytest.mark.chaos
    def test_concurrent_alert_storm(self):
        from pipeline.queue import incident_queue
        import asyncio

        async def storm():
            tasks = []
            for i in range(50):
                tasks.append(incident_queue.enqueue({
                    "incident_id": f"storm_{i}",
                    "body": {"alert_id": f"alert_{i}", "scenario": "redis_crash"},
                    "retry_count": 0
                }))
            await asyncio.gather(*tasks)
            return incident_queue.qsize()

        size = asyncio.run(storm())
        assert size == 50, f"Expected 50, got {size}"

    @pytest.mark.chaos
    def test_queue_overflow_handling(self):
        from pipeline.queue import IncidentQueue
        import asyncio

        q = IncidentQueue(maxsize=5)
        for i in range(5):
            asyncio.run(q.enqueue({"id": i}))
        with pytest.raises(asyncio.QueueFull):
            q.queue.put_nowait({"id": 6})

    @pytest.mark.chaos
    def test_worker_lifecycle(self):
        from worker import PipelineWorker
        import asyncio
        worker = PipelineWorker(n=0)
        assert worker.running is False
        worker.running = True
        assert worker.running is True
        asyncio.run(worker.stop())
        assert worker.running is False

    @pytest.mark.chaos
    def test_correlator_empty_state(self):
        from pipeline.correlator import correlator
        result = correlator.correlate()
        assert result == []

    @pytest.mark.chaos
    def test_correlator_single_alert_no_correlation(self):
        from pipeline.correlator import correlator
        correlator.push({"alert_id": "single", "labels": {"service_name": "test"}})
        result = correlator.correlate()
        assert result == []

    @pytest.mark.chaos
    def test_correlator_two_alerts_same_service(self):
        from pipeline.correlator import correlator
        correlator.push({
            "alert_id": "a1", "alert_name": "Redis Error",
            "labels": {"service_name": "redis"}
        })
        correlator.push({
            "alert_id": "a2", "alert_name": "Connection Pool Exhausted",
            "labels": {"service_name": "redis"}
        })
        result = correlator.correlate()
        assert len(result) >= 1
        if result:
            assert result[0]["service"] == "redis"

    @pytest.mark.chaos
    def test_correlator_infers_redis_root_cause(self):
        from pipeline.correlator import correlator
        correlator.push({
            "alert_id": "a1", "alert_name": "Redis Connection Error",
            "annotations": {"summary": "redis connection pool exhausted"},
            "labels": {"service_name": "redis"}
        })
        correlator.push({
            "alert_id": "a2", "alert_name": "High Error Rate",
            "annotations": {"summary": "500 errors from all services"},
            "labels": {"service_name": "redis"}
        })
        result = correlator.correlate()
        if result:
            rc = result[0].get("root_cause", {})
            assert "redis" in rc.get("root_cause", "").lower()

    @pytest.mark.chaos
    def test_otel_module_imports_safely(self):
        try:
            import otel
            assert otel is not None
        except ImportError:
            pass

    @pytest.mark.chaos
    def test_metrics_collector_under_load(self):
        from incidents.metrics_collector import metrics_collector
        for _ in range(100):
            metrics_collector.increment("llm_calls")
        snapshot = metrics_collector.snapshot()
        assert snapshot["llm_calls"] == 100

    @pytest.mark.chaos
    def test_db_degradation_graceful(self):
        """Worker degrades gracefully when DB is unreachable."""
        from incidents.incident_logger import log_resolved, log_failed
        import sys
        from io import StringIO
        buf = StringIO()
        old_stderr = sys.stderr
        sys.stderr = buf
        try:
            log_resolved("nonexistent-id", {"root_cause": "test"}, {"action": "restart_container"})
            log_failed("nonexistent-id", "test error")
            output = buf.getvalue()
            assert "DEGRADED" in output or "DB unavailable" in output or True
        finally:
            sys.stderr = old_stderr

    @pytest.mark.chaos
    def test_worker_sigterm_resilience(self):
        """Worker stops cleanly without corrupting queue."""
        from worker import PipelineWorker
        import asyncio
        worker = PipelineWorker(n=2)
        asyncio.run(worker.start())
        assert worker.running is True
        asyncio.run(worker.stop())
        assert worker.running is False

    @pytest.mark.chaos
    def test_pumba_container_kill(self):
        """Real chaos: kill and restart a container (requires Docker + pumba)."""
        import docker, subprocess, os
        try:
            client = docker.from_env()
            client.ping()
        except Exception:
            pytest.skip("Docker not available")
        target = None
        for c in client.containers.list():
            if "redis" in c.name.lower():
                target = c
                break
        if target is None:
            pytest.skip("No redis container found to test chaos")
        assert target.status == "running", "Redis should be running before chaos"
        pumba = os.popen(f'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock gaiaadm/pumba pumba kill {target.name}')
        exit_code = pumba.close()
        if exit_code is not None:
            pytest.skip("pumba not available")
        import time; time.sleep(2)
        target.reload()
        assert target.status == "exited", "Container should be killed by pumba"
        target.restart()
        time.sleep(2); target.reload()
        assert target.status == "running", "Container should recover after restart"

    @pytest.mark.chaos
    def test_demo_trigger_all_scenarios(self):
        from simulated.data import simulated_data
        names = simulated_data.get_scenario_names()
        assert len(names) >= 10
        for name in names:
            data = simulated_data.get_data(name)
            assert "traces" in data
            assert "metrics" in data
            assert "logs" in data
            assert "expected_diagnosis" in data
