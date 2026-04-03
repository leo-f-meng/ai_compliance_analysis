from collections import defaultdict
from datetime import date
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

# In-memory counters — replace with Redis for production multi-instance deployment
_concurrent: dict[str, int] = defaultdict(int)
_daily: dict[tuple[str, date], int] = defaultdict(int)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/jobs/") or request.method != "POST":
            return await call_next(request)

        user_id = request.headers.get("x-user-id", "anonymous")
        today = date.today()

        if _concurrent[user_id] >= settings.max_concurrent_jobs_per_user:
            return Response(
                content='{"detail":"Too many concurrent jobs"}',
                status_code=429,
                media_type="application/json",
            )
        if _daily[(user_id, today)] >= settings.max_daily_jobs_per_user:
            return Response(
                content='{"detail":"Daily job limit reached"}',
                status_code=429,
                media_type="application/json",
            )

        _concurrent[user_id] += 1
        _daily[(user_id, today)] += 1
        try:
            response = await call_next(request)
        finally:
            _concurrent[user_id] -= 1

        return response
