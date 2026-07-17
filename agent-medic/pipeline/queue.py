import asyncio
from typing import Any


class IncidentQueue:
    def __init__(self, maxsize: int = 100):
        self.queue = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, item: dict):
        await self.queue.put(item)

    async def dequeue(self) -> dict:
        return await self.queue.get()

    def qsize(self) -> int:
        return self.queue.qsize()


incident_queue = IncidentQueue()
