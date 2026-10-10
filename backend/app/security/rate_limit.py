"""
Small sliding-window rate limiter.

LIMITATION: state lives in this process's memory. With several server processes each has its
own counters, and a restart clears them. Before a multi-instance production deployment, move
this to a shared store (for example Redis) or enforce it at the gateway.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, status


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                retry = max(1, int(window_seconds - (now - hits[0])))
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Wait a few minutes and try again.",
                    headers={"Retry-After": str(retry)},
                )
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()
