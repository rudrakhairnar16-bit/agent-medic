class MetricsCollector:
    def __init__(self):
        self.metrics = dict.fromkeys(["incidents_total", "incidents_resolved", "incidents_failed", "llm_calls", "mcp_queries", "fix_attempts", "fix_successes"], 0)
    def increment(self, m):
        if m in self.metrics: self.metrics[m] += 1
    def snapshot(self): return dict(self.metrics)
    def reset(self):
        for k in self.metrics: self.metrics[k] = 0

metrics_collector = MetricsCollector()
