from datetime import datetime, timedelta, timezone
from typing import Dict


class Deduplicator:
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.seen: Dict[str, datetime] = {}

    def _now(self):
        return datetime.now(timezone.utc)

    def is_duplicate(self, alert_id: str) -> bool:
        now = self._now()
        if alert_id in self.seen:
            last_seen = self.seen[alert_id]
            if now - last_seen < timedelta(minutes=self.window_minutes):
                return True
        self.seen[alert_id] = now
        return False

    def cleanup(self):
        cutoff = self._now() - timedelta(minutes=self.window_minutes)
        self.seen = {k: v for k, v in self.seen.items() if v > cutoff}


deduplicator = Deduplicator()
