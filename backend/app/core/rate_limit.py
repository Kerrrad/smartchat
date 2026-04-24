from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Callable

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self.storage: dict[str, deque[datetime]] = defaultdict(deque)

    async def enforce(self, request: Request, key_suffix: str, limit: int, window_seconds: int) -> None:
        ip = request.client.host if request.client else "anonymous"
        key = f"{ip}:{key_suffix}"
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window_seconds)
        bucket = self.storage[key]

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Przekroczono limit żądań. Spróbuj ponownie za chwilę.",
            )

        bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def rate_limit(limit: int, window_seconds: int, key_suffix: str) -> Callable:
    async def dependency(request: Request) -> None:
        await rate_limiter.enforce(
            request=request,
            key_suffix=key_suffix,
            limit=limit,
            window_seconds=window_seconds,
        )

    return dependency

