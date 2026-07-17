import random
import time


class SimulatedDataProvider:
    def __init__(self):
        self.scenarios = {
            "redis_crash": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(2000, 8000),
                            "error": "redis.exceptions.ConnectionError: Redis connection refused"}
                           for i in range(3)],
                "metrics": [{"query": "redis_errors_total", "value": 15},
                            {"query": "cpu_utilization", "value": 45},
                            {"query": "memory_usage", "value": 62},
                            {"query": "error_rate", "value": 23}],
                "logs": [{"timestamp": time.time(), "severity": "error",
                          "body": "Redis connection pool exhausted at 5000 connections"},
                         {"timestamp": time.time(), "severity": "error",
                          "body": "Cannot acquire connection from pool error"}],
                "expected_diagnosis": {
                    "root_cause": "Redis connection pool exhausted (simulated)",
                    "severity": "critical", "confidence": 0.92,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "redis"}}
            },
            "cpu_spike": {
                "traces": [{"trace_id": f"trace_{i}", "status": "OK",
                            "duration_ms": random.randint(800, 3000)} for i in range(5)],
                "metrics": [{"query": "cpu_utilization", "value": 92},
                            {"query": "memory_usage", "value": 55},
                            {"query": "error_rate", "value": 2},
                            {"query": "redis_errors_total", "value": 0}],
                "logs": [{"timestamp": time.time(), "severity": "warning",
                          "body": "High CPU usage detected: 92%"}],
                "expected_diagnosis": {
                    "root_cause": "CPU overload at 92% utilization (simulated)",
                    "severity": "warning", "confidence": 0.85,
                    "suggested_fix": "scale_service",
                    "fix_params": {"service_name": "sample-app", "replicas": 3}}
            },
            "db_timeout": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(5000, 10000),
                            "error": "psycopg2.OperationalError: connection to server timed out"}
                           for i in range(4)],
                "metrics": [{"query": "cpu_utilization", "value": 35},
                            {"query": "error_rate", "value": 18},
                            {"query": "db_connections", "value": 0},
                            {"query": "redis_errors_total", "value": 0}],
                "logs": [{"timestamp": time.time(), "severity": "error",
                          "body": "PostgreSQL connection timeout after 30 seconds"},
                         {"timestamp": time.time(), "severity": "error",
                          "body": "FATAL: could not connect to server: Connection refused"}],
                "expected_diagnosis": {
                    "root_cause": "PostgreSQL server not responding (simulated)",
                    "severity": "critical", "confidence": 0.88,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "postgres"}}
            },
            "random_500s": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(100, 500),
                            "error": "HTTP 500 Internal Server Error"}
                           for i in range(8)],
                "metrics": [{"query": "cpu_utilization", "value": 40},
                            {"query": "error_rate", "value": 35},
                            {"query": "redis_errors_total", "value": 0}],
                "logs": [{"timestamp": time.time(), "severity": "error",
                          "body": "Internal server error: KeyError 'missing_key' in data_processor.py:142"}],
                "expected_diagnosis": {
                    "root_cause": "Application error in data_processor.py — 35% error rate (simulated)",
                    "severity": "warning", "confidence": 0.65,
                    "suggested_fix": "escalate", "fix_params": {}}
            },
            "network_partition": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(10000, 30000),
                            "error": "socket.gaierror: [Errno -2] Name or service not known"}
                           for i in range(6)],
                "metrics": [{"query": "cpu_utilization", "value": 30},
                            {"query": "error_rate", "value": 45},
                            {"query": "network_errors", "value": 28},
                            {"query": "redis_errors_total", "value": 0},
                            {"query": "dns_query_failures", "value": 12}],
                "logs": [{"timestamp": time.time(), "severity": "error",
                          "body": "Connection refused: downstream service unreachable after 30s"},
                         {"timestamp": time.time(), "severity": "error",
                          "body": "DNS resolution failed for api.example.com"}],
                "expected_diagnosis": {
                    "root_cause": "Network partition detected — DNS resolution failing, downstream unreachable (simulated)",
                    "severity": "critical", "confidence": 0.82,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "sample-app"}}
            },
            "disk_full": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(3000, 6000),
                            "error": "OSError: [Errno 28] No space left on device"}
                           for i in range(5)],
                "metrics": [{"query": "disk_usage_percent", "value": 98},
                            {"query": "disk_write_latency_ms", "value": 2500},
                            {"query": "error_rate", "value": 30},
                            {"query": "cpu_utilization", "value": 50}],
                "logs": [{"timestamp": time.time(), "severity": "critical",
                          "body": "Disk at 98% capacity — log rotation may help"},
                         {"timestamp": time.time(), "severity": "error",
                          "body": "Write failed: No space left on device"}],
                "expected_diagnosis": {
                    "root_cause": "Disk full at 98% capacity — log files consuming available space (simulated)",
                    "severity": "critical", "confidence": 0.9,
                    "suggested_fix": "clear_cache",
                    "fix_params": {"cache_type": "redis"}}
            },
            "memory_leak": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(500, 1500),
                            "error": "MemoryError: unable to allocate 2.1 GiB"}
                           for i in range(7)],
                "metrics": [{"query": "memory_usage", "value": 96},
                            {"query": "memory_leak_rate_mb_per_min", "value": 45},
                            {"query": "error_rate", "value": 25},
                            {"query": "cpu_utilization", "value": 65}],
                "logs": [{"timestamp": time.time(), "severity": "critical",
                          "body": "Memory at 96% — leak suspected in cache layer"},
                         {"timestamp": time.time(), "severity": "error",
                          "body": "MemoryError in process_data() at line 234 — allocation failed"}],
                "expected_diagnosis": {
                    "root_cause": "Memory leak in data processing — 45 MB/min growth, 96% usage (simulated)",
                    "severity": "critical", "confidence": 0.88,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "sample-app"}}
            },
            "slow_queries": {
                "traces": [{"trace_id": f"trace_{i}", "status": "OK",
                            "duration_ms": random.randint(5000, 15000)}
                           for i in range(10)],
                "metrics": [{"query": "p99_latency_ms", "value": 12000},
                            {"query": "avg_query_duration_ms", "value": 4500},
                            {"query": "db_connection_pool_usage", "value": 85},
                            {"query": "cpu_utilization", "value": 70}],
                "logs": [{"timestamp": time.time(), "severity": "warning",
                          "body": "Slow query detected: SELECT * FROM orders JOIN line_items — 8.2s"},
                         {"timestamp": time.time(), "severity": "warning",
                          "body": "Connection pool at 85% — consider increasing pool_size"}],
                "expected_diagnosis": {
                    "root_cause": "Slow database queries — p99 at 12s, missing index on orders table (simulated)",
                    "severity": "warning", "confidence": 0.72,
                    "suggested_fix": "scale_service",
                    "fix_params": {"service_name": "postgres", "replicas": 2}}
            },
            "tls_cert_expiry": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(200, 800),
                            "error": "SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired"}
                           for i in range(4)],
                "metrics": [{"query": "tls_handshake_errors", "value": 22},
                            {"query": "error_rate", "value": 40},
                            {"query": "cpu_utilization", "value": 35}],
                "logs": [{"timestamp": time.time(), "severity": "error",
                          "body": "TLS handshake failed: certificate expired 2 days ago for api.example.com"}],
                "expected_diagnosis": {
                    "root_cause": "TLS certificate expired for api.example.com — 22 handshake errors (simulated)",
                    "severity": "critical", "confidence": 0.91,
                    "suggested_fix": "escalate", "fix_params": {}}
            },
            "oom_kill": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(100, 300),
                            "error": "Killed: container exited with code 137 (OOMKilled)"}
                           for i in range(3)],
                "metrics": [{"query": "memory_usage", "value": 99},
                            {"query": "oom_kills", "value": 3},
                            {"query": "container_restarts", "value": 2},
                            {"query": "cpu_utilization", "value": 80}],
                "logs": [{"timestamp": time.time(), "severity": "critical",
                          "body": "Container sample-app killed by OOM killer — exit code 137"},
                         {"timestamp": time.time(), "severity": "error",
                          "body": "cgroup: memory limit of 512MB exceeded"}],
                "expected_diagnosis": {
                    "root_cause": "Out of memory — container killed by OOM killer, 512MB limit exceeded (simulated)",
                    "severity": "critical", "confidence": 0.93,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "sample-app"}}
            },
            "cascading_failure": {
                "traces": [{"trace_id": f"trace_{i}", "status": "ERROR",
                            "duration_ms": random.randint(1000, 5000),
                            "error": "HTTP 503: upstream connect error"}
                           for i in range(12)],
                "metrics": [{"query": "error_rate", "value": 55},
                            {"query": "redis_errors_total", "value": 10},
                            {"query": "db_connections", "value": 0},
                            {"query": "cpu_utilization", "value": 90},
                            {"query": "upstream_errors", "value": 35}],
                "logs": [{"timestamp": time.time(), "severity": "error",
                          "body": "Upstream timeout: Redis not responding, DB pool exhausted, CPU maxed"},
                         {"timestamp": time.time(), "severity": "critical",
                          "body": "Cascading failure: all downstream services degraded"}],
                "expected_diagnosis": {
                    "root_cause": "Cascading failure — Redis failure cascaded to DB pool exhaustion and CPU spike (simulated)",
                    "severity": "critical", "confidence": 0.87,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "redis"}}
            }
        }

    def get_scenario_names(self):
        return list(self.scenarios.keys())

    def get_data(self, scenario_name: str) -> dict:
        scenario = self.scenarios.get(scenario_name)
        if not scenario:
            scenario = self.scenarios["redis_crash"]
        return {
            "traces": scenario["traces"],
            "metrics": scenario["metrics"],
            "logs": scenario["logs"],
            "expected_diagnosis": scenario["expected_diagnosis"]
        }

    def get_random_alert(self) -> dict:
        name = random.choice(list(self.scenarios.keys()))
        return {
            "alert_id": f"sim_alert_{int(time.time())}",
            "alert_name": name.replace("_", " ").title(),
            "severity": "critical" if "crash" in name or "timeout" in name else "warning",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": f"Simulated: {name} triggered for demo"},
            "starts_at": time.time(),
            "scenario": name
        }


simulated_data = SimulatedDataProvider()
