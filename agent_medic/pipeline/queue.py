import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import time

class IncidentQueue:
    def __init__(self, maxsize=100): self.queue = asyncio.Queue(maxsize=maxsize)
    async def enqueue(self, item): await self.queue.put(item)
    async def dequeue(self): return await self.queue.get()
    def qsize(self): return self.queue.qsize()

incident_queue = IncidentQueue()


class Deduplicator:
    def __init__(self, window=5):
        self.window = window
        self.seen = {}
    def is_duplicate(self, alert_id):
        now = datetime.now(timezone.utc)
        if alert_id in self.seen and (now - self.seen[alert_id]).total_seconds() < self.window * 60:
            return True
        self.seen[alert_id] = now
        return False

deduplicator = Deduplicator()


class RateLimiter:
    def __init__(self, max_per_min=10): self.max, self.window = max_per_min, deque()
    def allow(self):
        now = time.time()
        while self.window and self.window[0] < now - 60: self.window.popleft()
        if len(self.window) >= self.max: return False
        self.window.append(now); return True

rate_limiter = RateLimiter()


class AlertCorrelator:
    WINDOW = 120
    RULES = [
        (["redis", "connection", "pool"], "Redis failure", 0.9, "restart_container", {"service_name": "redis"}),
        (["postgres", "db_timeout", "database"], "Database failure", 0.85, "restart_container", {"service_name": "postgres"}),
        (["cpu", "memory", "resource"], "Resource exhaustion", 0.75, "scale_service", {"service_name": "sample-app", "replicas": 3}),
        (["disk", "storage", "space"], "Disk full", 0.8, "clear_cache", {"cache_type": "redis"}),
        (["network", "dns", "connect", "refused"], "Network failure", 0.7, "restart_container", {"service_name": "sample-app"}),
        (["oom", "memory_leak", "out of memory"], "OOM leak", 0.85, "restart_container", {"service_name": "sample-app"}),
        (["tls", "ssl", "certificate"], "TLS failure", 0.8, "escalate", {}),
    ]

    def __init__(self): self.alerts = []
    def push(self, alert):
        now = datetime.now(timezone.utc)
        self.alerts.append((alert, now))
        cutoff = now - timedelta(seconds=self.WINDOW)
        self.alerts = [(a, t) for a, t in self.alerts if t > cutoff]

    def correlate(self):
        if len(self.alerts) < 2: return []
        groups = defaultdict(list)
        for a, _ in self.alerts:
            groups[a.get("labels", {}).get("service_name", "unknown")].append(a)
        results = []
        for svc, alerts in groups.items():
            if len(alerts) < 2: continue
            combined = " ".join(a.get("alert_name", "") + " " + a.get("annotations", {}).get("summary", "") for a in alerts).lower()
            match = next(((rc, conf, fix, fp) for kw, rc, conf, fix, fp in self.RULES if any(k in combined for k in kw)), (None, 0.3, "escalate", {}))
            results.append({"service": svc, "alert_count": len(alerts), "root_cause": {"root_cause": match[0] or "Unknown", "confidence": match[1], "suggested_fix": match[2], "fix_params": match[3], "method": "correlation"}})
        return results

correlator = AlertCorrelator()
