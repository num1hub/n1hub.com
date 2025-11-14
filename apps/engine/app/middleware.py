"""Rate limiting middleware for FastAPI."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis or in-memory fallback."""

    def __init__(self, app, redis_client: Optional[redis.Redis] = None) -> None:
        super().__init__(app)
        self._redis_client = redis_client
        self._in_memory_store: dict[str, list[float]] = {}
        self._in_memory_cleanup_interval = 60.0  # Clean up every 60 seconds
        self._last_cleanup = time.time()
    
    def _get_redis_client(self):
        """Get Redis client from global scope if available."""
        # Try to import from main module
        try:
            from .main import redis_client
            return redis_client if redis_client else self._redis_client
        except ImportError:
            return self._redis_client

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check rate limits before processing request."""
        # Identify user (for now, use IP address; in production, use auth token)
        user_id = self._get_user_id(request)
        
        # Determine rate limit based on endpoint
        endpoint = request.url.path
        limit, window = self._get_rate_limit(endpoint)
        
        if limit is None:
            # No rate limit for this endpoint
            return await call_next(request)
        
        # Check rate limit
        key = f"ratelimit:{endpoint}:{user_id}"
        current_time = time.time()
        
        redis_client = self._get_redis_client()
        if redis_client:
            # Use Redis for distributed rate limiting
            allowed = await self._check_redis_limit(redis_client, key, limit, window, current_time)
        else:
            # Use in-memory rate limiting (fallback)
            allowed = await self._check_memory_limit(key, limit, window, current_time)
        
        if not allowed:
            retry_after = int(window - (current_time % window))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        
        response = await call_next(request)
        return response

    def _get_user_id(self, request: Request) -> str:
        """Extract user ID from request (IP address for now)."""
        # In production, extract from auth token
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_rate_limit(self, endpoint: str) -> tuple[Optional[int], int]:
        """Get rate limit for endpoint."""
        window = 60  # 1 minute window
        
        if endpoint == "/ingest":
            return settings.rate_limit_upload, window
        elif endpoint == "/chat":
            return settings.rate_limit_chat, window
        elif endpoint.startswith("/capsules") and "scope=public" in str(endpoint):
            return settings.rate_limit_public, window
        
        return None, window

    async def _check_redis_limit(
        self, redis_client: redis.Redis, key: str, limit: int, window: int, current_time: float
    ) -> bool:
        """Check rate limit using Redis."""
        try:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            results = await pipe.execute()
            
            count = results[1] if len(results) > 1 else 0
            return count < limit
        except Exception:
            # Fallback to memory if Redis fails
            return await self._check_memory_limit(key, limit, window, current_time)

    async def _check_memory_limit(
        self, key: str, limit: int, window: int, current_time: float
    ) -> bool:
        """Check rate limit using in-memory store."""
        # Cleanup old entries periodically
        if current_time - self._last_cleanup > self._in_memory_cleanup_interval:
            self._cleanup_memory_store(current_time - window)
            self._last_cleanup = current_time
        
        if key not in self._in_memory_store:
            self._in_memory_store[key] = []
        
        # Remove old entries
        self._in_memory_store[key] = [
            ts for ts in self._in_memory_store[key] if ts > current_time - window
        ]
        
        # Check limit
        if len(self._in_memory_store[key]) >= limit:
            return False
        
        # Add current request
        self._in_memory_store[key].append(current_time)
        return True

    def _cleanup_memory_store(self, cutoff_time: float) -> None:
        """Remove old entries from in-memory store."""
        for key in list(self._in_memory_store.keys()):
            self._in_memory_store[key] = [
                ts for ts in self._in_memory_store[key] if ts > cutoff_time
            ]
            if not self._in_memory_store[key]:
                del self._in_memory_store[key]


async def create_redis_client() -> Optional[redis.Redis]:
    """Create Redis client if available."""
    if not REDIS_AVAILABLE:
        return None
    
    try:
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
        await client.ping()
        return client
    except Exception:
        return None
