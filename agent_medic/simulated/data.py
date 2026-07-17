import random
import time
from typing import Optional


class SimulatedDataProvider:
    def __init__(self):
        self.scenarios = {
            "redis_crash": {
                "traces": [
                    {"trace_id": f"trace_{i}", "status": "ERROR",
                     "duration_ms": random.randint(2000, 8000),
                     "error": "redis.exceptions.ConnectionError: Redis connection refused"}
                    for i in range(3)
                ],
                "metrics": [
                    {"query": "redis_errors_total", "value": 15},
                    {"query": "cpu_utilization", "value": 45},
                    {"query": "memory_usage", "value": 62},
                    {"query": "error_rate", "value": 23}
                ],
                "logs": [
                    {"timestamp": time.time(), "severity": "error",
                     "body": "Redis connection pool exhausted at 5000 connections"},
                    {"timestamp": time.time(), "severity": "error",
                     "body": "Cannot acquire connection from pool error"},
                ],
                "expected_diagnosis": {
                    "root_cause": "Redis connection pool exhausted (simulated)",
                    "severity": "critical",
                    "confidence": 0.92,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "redis"}
                }
            },
            "cpu_spike": {
                "traces": [
                    {"trace_id": f"trace_{i}", "status": "OK",
                     "duration_ms": random.randint(800, 3000)} for i in range(5)
                ],
                "metrics": [
                    {"query": "cpu_utilization", "value": 92},
                    {"query": "memory_usage", "value": 55},
                    {"query": "error_rate", "value": 2},
                    {"query": "redis_errors_total", "value": 0}
                ],
                "logs": [
                    {"timestamp": time.time(), "severity": "warning",
                     "body": "High CPU usage detected: 92%"}
                ],
                "expected_diagnosis": {
                    "root_cause": "CPU overload at 92% utilization (simulated)",
                    "severity": "warning",
                    "confidence": 0.85,
                    "suggested_fix": "scale_service",
                    "fix_params": {"service_name": "sample-app", "replicas": 3}
                }
            },
            "db_timeout": {
                "traces": [
                    {"trace_id": f"trace_{i}", "status": "ERROR",
                     "duration_ms": random.randint(5000, 10000),
                     "error": "psycopg2.OperationalError: connection to server timed out"}
                    for i in range(4)
                ],
                "metrics": [
                    {"query": "cpu_utilization", "value": 35},
                    {"query": "error_rate", "value": 18},
                    {"query": "db_connections", "value": 0},
                    {"query": "redis_errors_total", "value": 0}
                ],
                "logs": [
                    {"timestamp": time.time(), "severity": "error",
                     "body": "PostgreSQL connection timeout after 30 seconds"},
                    {"timestamp": time.time(), "severity": "error",
                     "body": "FATAL: could not connect to server: Connection refused"}
                ],
                "expected_diagnosis": {
                    "root_cause": "PostgreSQL server not responding (simulated)",
                    "severity": "critical",
                    "confidence": 0.88,
                    "suggested_fix": "restart_container",
                    "fix_params": {"service_name": "postgres"}
                }
            },
            "random_500s": {
                "traces": [
                    {"trace_id": f"trace_{i}", "status": "ERROR",
                     "duration_ms": random.randint(100, 500),
                     "error": "HTTP 500 Internal Server Error"}
                    for i in range(8)
                ],
                "metrics": [
                    {"query": "cpu_utilization", "value": 40},
                    {"query": "error_rate", "value": 35},
                    {"query": "redis_errors_total", "value": 0}
                ],
                "logs": [
                    {"timestamp": time.time(), "severity": "error",
                     "body": "Internal server error: KeyError 'missing_key' in data_processor.py:142"}
                ],
                "expected_diagnosis": {
                    "root_cause": "Application error in data_processor.py — 35% error rate (simulated)",
                    "severity": "warning",
                    "confidence": 0.65,
                    "suggested_fix": "escalate",
                    "fix_params": {}
                }
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
