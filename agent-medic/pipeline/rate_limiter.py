import time
from collections import deque


class RateLimiter:
    def __init__(self, max_per_minute: int = 10):
        self.max_per_minute = max_per_minute
        self.window = deque()

    def allow(self) -> bool:
        now = time.time()
        while self.window and self.window[0] < now - 60:
            self.window.popleft()
        if len(self.window) >= self.max_per_minute:
            return False
        self.window.append(now)
        return True


rate_limiter = RateLimiter()
