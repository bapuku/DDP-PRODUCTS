"""
Simple in-memory rate limit (per IP). For production use Redis.
"""
import time
from collections import defaultdict
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# 100 req/min per IP
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60.0
_store: dict[str, list[float]] = defaultdict(list)


def _clean_old(now: float, timestamps: list[float]) -> list[float]:
    return [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]


def is_rate_limited(key: str) -> bool:
    now = time.monotonic()
    timestamps = _store[key]
    timestamps = _clean_old(now, timestamps)
    _store[key] = timestamps
    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        return True
    timestamps.append(now)
    return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client
        key = client.host if client else "unknown"
        if is_rate_limited(key):
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        return await call_next(request)
