import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request, status
from app.core.config import settings

# In-memory sliding window rate limiter
# Key: client_ip -> list of timestamps
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)


def check_auth_rate_limit(request: Request) -> None:
    """
    Check rate limit for sensitive auth endpoints (login, forgot-password, reset-password).
    Allows up to AUTH_RATE_LIMIT_MAX_REQUESTS within AUTH_RATE_LIMIT_WINDOW_SECONDS.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = settings.AUTH_RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.AUTH_RATE_LIMIT_MAX_REQUESTS

    # Clean old requests outside window
    timestamps = _rate_limit_store[client_ip]
    _rate_limit_store[client_ip] = [ts for ts in timestamps if now - ts < window]

    if len(_rate_limit_store[client_ip]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again after a few minutes."
        )

    _rate_limit_store[client_ip].append(now)


def reset_rate_limit_store():
    """Helper for testing purposes."""
    _rate_limit_store.clear()
