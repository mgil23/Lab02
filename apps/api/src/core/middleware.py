# SPDX-License-Identifier: AGPL-3.0-or-later
import time
from collections.abc import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as aioredis
from ..config import settings
from .telemetry import HTTP_REQUEST_DURATION


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract tenant slug from path (/api/v1/{tenant}/...) and attach to request state."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path_parts = request.url.path.split("/")
        # Path pattern: /api/v1/{tenant}/resource
        if len(path_parts) >= 4 and path_parts[1] == "api" and path_parts[2] == "v1":
            tenant_slug = path_parts[3]
            if tenant_slug not in ("docs", "openapi.json", "health", "metrics", "auth"):
                request.state.tenant_slug = tenant_slug
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis sliding window rate limiter per tenant."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_slug = getattr(request.state, "tenant_slug", None)
        if tenant_slug is None:
            return await call_next(request)

        redis = await self._get_redis()
        key = f"rate:{tenant_slug}"
        pipe = redis.pipeline()
        now = int(time.time())
        window = 60
        limit = settings.rate_limit_requests_per_minute

        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        count = results[2]

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            path=request.url.path,
            status=str(response.status_code),
        ).observe(duration)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
