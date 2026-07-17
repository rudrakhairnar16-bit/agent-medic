import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class AlertCorrelator:
    WINDOW_SECONDS = 120

    def __init__(self):
        self._recent_alerts = []

    def push(self, alert: dict):
        now = datetime.now(timezone.utc)
        self._recent_alerts.append({"alert": alert, "timestamp": now})
        cutoff = now - timedelta(seconds=self.WINDOW_SECONDS)
        self._recent_alerts = [a for a in self._recent_alerts if a["timestamp"] > cutoff]

    def correlate(self) -> list:
        if len(self._recent_alerts) < 2:
            return []

        groups = defaultdict(list)
        for entry in self._recent_alerts:
            alert = entry["alert"]
            labels = alert.get("labels", {})
            service = labels.get("service_name", "unknown")
            groups[service].append(alert)

        correlations = []
        for service, alerts in groups.items():
            alert_names = set(a.get("alert_name", a.get("alert_id", "unknown")) for a in alerts)
            if len(alerts) >= 2:
                root_cause = self._infer_root_cause(alerts)
                correlations.append({
                    "service": service,
                    "alert_count": len(alerts),
                    "alert_names": list(alert_names),
                    "root_cause": root_cause,
                    "correlated_at": datetime.now(timezone.utc).isoformat()
                })

        return correlations

    def _infer_root_cause(self, alerts: list) -> dict:
        names_lower = " ".join(
            a.get("alert_name", a.get("alert_id", "")).lower()
            for a in alerts
        )
        annotations = " ".join(
            a.get("annotations", {}).get("summary", "")
            for a in alerts
        )
        combined = names_lower + " " + annotations

        RULES = [
            {
                "keywords": ["redis", "connection", "pool"],
                "root_cause": "Redis infrastructure failure",
                "confidence": 0.9,
                "suggested_fix": "restart_container",
                "fix_params": {"service_name": "redis"}
            },
            {
                "keywords": ["postgres", "db_timeout", "database", "timeout"],
                "root_cause": "Database connectivity failure",
                "confidence": 0.85,
                "suggested_fix": "restart_container",
                "fix_params": {"service_name": "postgres"}
            },
            {
                "keywords": ["cpu", "memory", "resource", "utilization"],
                "root_cause": "Resource exhaustion (CPU/memory)",
                "confidence": 0.75,
                "suggested_fix": "scale_service",
                "fix_params": {"service_name": "sample-app", "replicas": 3}
            },
            {
                "keywords": ["disk", "storage", "space", "io"],
                "root_cause": "Disk space or I/O failure",
                "confidence": 0.8,
                "suggested_fix": "clear_cache",
                "fix_params": {"cache_type": "redis"}
            },
            {
                "keywords": ["network", "dns", "connect", "refused", "timeout"],
                "root_cause": "Network connectivity failure",
                "confidence": 0.7,
                "suggested_fix": "restart_container",
                "fix_params": {"service_name": "sample-app"}
            },
            {
                "keywords": ["oom", "memory_leak", "out of memory"],
                "root_cause": "Out of memory — application leak",
                "confidence": 0.85,
                "suggested_fix": "restart_container",
                "fix_params": {"service_name": "sample-app"}
            },
            {
                "keywords": ["tls", "ssl", "certificate"],
                "root_cause": "TLS/SSL certificate failure",
                "confidence": 0.8,
                "suggested_fix": "escalate",
                "fix_params": {}
            },
        ]

        for rule in RULES:
            if any(kw in combined for kw in rule["keywords"]):
                return {
                    "root_cause": rule["root_cause"],
                    "confidence": rule["confidence"],
                    "suggested_fix": rule["suggested_fix"],
                    "fix_params": rule["fix_params"],
                    "method": "correlation"
                }

        return {
            "root_cause": "Multiple alerts fired — unable to determine root cause",
            "confidence": 0.3,
            "suggested_fix": "escalate",
            "fix_params": {},
            "method": "correlation"
        }

    def get_recent_alerts(self) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.WINDOW_SECONDS)
        return [a for a in self._recent_alerts if a["timestamp"] > cutoff]


correlator = AlertCorrelator()
