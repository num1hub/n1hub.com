from __future__ import annotations

import asyncio
from typing import Dict, Optional

from .models import JobModel


class EventPublisher:
    """Simple in-process event publisher for SSE (later swappable to Redis Pub/Sub)."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, subscriber_id: str) -> asyncio.Queue:
        """Subscribe to events and return a queue."""
        async with self._lock:
            queue: asyncio.Queue = asyncio.Queue()
            self._subscribers[subscriber_id] = queue
            return queue

    async def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe from events."""
        async with self._lock:
            self._subscribers.pop(subscriber_id, None)

    async def publish(self, event: dict) -> None:
        """Publish an event to all subscribers."""
        async with self._lock:
            for queue in self._subscribers.values():
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop event if queue is full
                    pass

    async def publish_job_update(self, job: JobModel) -> None:
        """Publish a job update event."""
        await self.publish({
            "job_id": job.id,
            "code": job.code,
            "stage": job.stage,
            "state": job.state,
            "progress": job.progress,
            "capsule_id": job.capsule_id,
        })


# Global event publisher instance
event_publisher = EventPublisher()
