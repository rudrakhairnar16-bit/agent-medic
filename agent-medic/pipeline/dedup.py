from datetime import datetime, timedelta
from typing import Dict


class Deduplicator:
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.seen: Dict[str, datetime] = {}

    def is_duplicate(self, alert_id: str) -> bool:
        now = datetime.utcnow()
        if alert_id in self.seen:
            last_seen = self.seen[alert_id]
            if now - last_seen < timedelta(minutes=self.window_minutes):
                return True
        self.seen[alert_id] = now
        return False

    def cleanup(self):
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        self.seen = {k: v for k, v in self.seen.items() if v > cutoff}


deduplicator = Deduplicator()
