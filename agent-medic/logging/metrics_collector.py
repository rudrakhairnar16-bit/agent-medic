import json


class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "incidents_total": 0,
            "incidents_resolved": 0,
            "incidents_failed": 0,
            "llm_calls": 0,
            "mcp_queries": 0,
            "fix_attempts": 0,
            "fix_successes": 0
        }

    def increment(self, metric: str):
        if metric in self.metrics:
            self.metrics[metric] += 1

    def snapshot(self) -> dict:
        return dict(self.metrics)

    def reset(self):
        for k in self.metrics:
            self.metrics[k] = 0


metrics_collector = MetricsCollector()
