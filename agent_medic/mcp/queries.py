QUERY_TEMPLATES = {
    "error_traces": {
        "tool": "query_traces",
        "args_template": {
            "filters": {"service.name": "{service}", "status.code": "ERROR"},
            "timeRange": {"from": "{time_range}", "to": "now"},
            "limit": 10
        }
    },
    "cpu_metrics": {
        "tool": "query_metrics",
        "args_template": {
            "query": "avg(system_cpu_utilization{service='{service}'})",
            "timeRange": {"from": "{time_range}", "to": "now"}
        }
    },
    "error_rate": {
        "tool": "query_metrics",
        "args_template": {
            "query": "sum(rate(signoz_latency_count{status_code=~'5..'}[5m]))",
            "timeRange": {"from": "{time_range}", "to": "now"}
        }
    },
    "error_logs": {
        "tool": "query_logs",
        "args_template": {
            "filters": {"service": "{service}", "severity": "error"},
            "timeRange": {"from": "{time_range}", "to": "now"},
            "limit": 20
        }
    },
    "redis_metrics": {
        "tool": "query_metrics",
        "args_template": {
            "query": "rate(redis_errors_total{service='{service}'}[5m])",
            "timeRange": {"from": "{time_range}", "to": "now"}
        }
    }
}
