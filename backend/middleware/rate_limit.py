"""
Rate limiting middleware & dependency for FastAPI.
Enforces request rate limits per client IP address to prevent API abuse or Denial of Service (DoS).
"""
import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status
from backend.config import get_settings


class RateLimiter:
    """Sliding-window IP-based rate limiter."""

    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> bool:
        settings = get_settings()
        limit = self.max_requests if self.max_requests is not None else settings.rate_limit_per_minute

        now = time.time()
        cutoff = now - self.window_seconds

        # Prune old request timestamps
        timestamps = [t for t in self._requests[client_ip] if t > cutoff]
        self._requests[client_ip] = timestamps

        if len(timestamps) >= limit:
            return True

        self._requests[client_ip].append(now)
        return False


# Global rate limiter instance (10 requests per minute by default)
job_submission_limiter = RateLimiter(max_requests=10, window_seconds=60)


async def check_rate_limit(request: Request):
    """FastAPI dependency to enforce rate limits on endpoints."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Support X-Forwarded-For header if behind a reverse proxy (Nginx/Caddy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    if job_submission_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: maximum 10 job submissions per minute per IP address. Please wait before retrying.",
            headers={"Retry-After": "60"},
        )
