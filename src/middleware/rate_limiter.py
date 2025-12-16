"""
Rate Limiter Middleware - Redis-backed rate limiting
Implements sliding window algorithm for accurate rate limiting
"""

import redis
import time
from functools import wraps
from typing import Tuple, Dict, Optional
from flask import request, jsonify, g
import logging

# Import from config
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import REDIS_URL, RATE_LIMIT_ENABLED, RATE_LIMITS

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm
    """

    def __init__(self, redis_url: str, enabled: bool = True):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
            enabled: Whether rate limiting is enabled
        """
        self.enabled = enabled
        self.redis_url = redis_url
        self._redis = None

        if self.enabled:
            try:
                self._redis = redis.from_url(redis_url)
                # Test connection
                self._redis.ping()
                logger.info(f"Rate limiter initialized successfully (Redis: {redis_url})")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, rate limiting disabled: {e}")
                self.enabled = False

    @property
    def redis(self):
        """Get Redis client"""
        if not self.enabled or self._redis is None:
            return None
        return self._redis

    def check_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is within rate limit using sliding window

        Args:
            key: Rate limit key (e.g., "ratelimit:query:user123")
            limit: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: limit, remaining, reset
        """
        if not self.enabled or self.redis is None:
            return True, {}

        try:
            now = int(time.time())
            window_start = now - window

            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request timestamp
            pipe.zadd(key, {now: now})

            # Set expiry on the key
            pipe.expire(key, window + 1)

            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]  # Result from zcard

            allowed = current_count < limit
            remaining = max(0, limit - current_count - 1) if allowed else 0

            info = {
                "limit": limit,
                "remaining": remaining,
                "reset": now + window,
                "window": window,
            }

            if not allowed:
                logger.warning(f"Rate limit exceeded for key: {key} ({current_count}/{limit})")

            return allowed, info

        except Exception as e:
            logger.error(f"Rate limit check error for key '{key}': {e}")
            # On error, allow the request (fail open)
            return True, {}

    def reset_limit(self, key: str):
        """
        Reset rate limit for a specific key

        Args:
            key: Rate limit key to reset
        """
        if not self.enabled or self.redis is None:
            return

        try:
            self.redis.delete(key)
            logger.info(f"Rate limit reset for key: {key}")
        except Exception as e:
            logger.error(f"Rate limit reset error for key '{key}': {e}")

    def get_remaining(self, key: str, limit: int, window: int) -> int:
        """
        Get remaining requests for a key

        Args:
            key: Rate limit key
            limit: Maximum requests
            window: Time window in seconds

        Returns:
            Number of remaining requests
        """
        if not self.enabled or self.redis is None:
            return limit

        try:
            now = int(time.time())
            window_start = now - window

            # Clean old entries and count
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()

            current_count = results[1]
            return max(0, limit - current_count)

        except Exception as e:
            logger.error(f"Failed to get remaining for key '{key}': {e}")
            return limit


# Global rate limiter instance
rate_limiter = RateLimiter(REDIS_URL, enabled=RATE_LIMIT_ENABLED)


def rate_limit(limit_key: str = "default"):
    """
    Decorator for rate limiting Flask endpoints

    Args:
        limit_key: Key to lookup rate limit config (e.g., "query", "upload")

    Example:
        @app.route("/api/query")
        @rate_limit("query")
        def query():
            return {"result": "..."}

    The rate limit is applied per user (from userId in request) or per IP address.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # If rate limiting is disabled, skip
            if not rate_limiter.enabled:
                return func(*args, **kwargs)

            # Get rate limit configuration
            limit_str = RATE_LIMITS.get(limit_key, "100/hour")
            try:
                limit_count, period = limit_str.split("/")
                limit_count = int(limit_count)
            except ValueError:
                logger.error(f"Invalid rate limit config: {limit_str}")
                return func(*args, **kwargs)

            # Parse time window
            window_seconds = {
                "second": 1,
                "minute": 60,
                "hour": 3600,
                "day": 86400,
            }.get(period, 3600)

            # Determine identifier (user_id or IP address)
            identifier = None
            if request.is_json:
                identifier = request.json.get("userId")
            elif request.args:
                identifier = request.args.get("userId")

            # Fallback to IP address
            if not identifier:
                identifier = request.remote_addr or "unknown"

            # Build rate limit key
            rate_key = f"ratelimit:{limit_key}:{identifier}"

            # Check rate limit
            allowed, info = rate_limiter.check_limit(rate_key, limit_count, window_seconds)

            # Store info in Flask g for access in route
            g.rate_limit_info = info

            if not allowed:
                # Rate limit exceeded
                response_data = {
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {info['limit']} per {period}",
                    "limit": info['limit'],
                    "reset": info['reset'],
                    "retry_after": info['reset'] - int(time.time()),
                }
                return jsonify(response_data), 429

            # Execute the route handler
            result = func(*args, **kwargs)

            # Add rate limit headers to response
            if isinstance(result, tuple):
                response, status_code = result
            else:
                response, status_code = result, 200

            # Add headers if response is JSON (has headers attribute)
            if hasattr(response, 'headers') and info:
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
                response.headers['X-RateLimit-Window'] = str(info['window'])

            return response, status_code

        return wrapper
    return decorator


def get_rate_limit_info() -> Optional[Dict[str, int]]:
    """
    Get rate limit info for current request

    Returns:
        Dict with limit, remaining, reset, window or None
    """
    return g.get('rate_limit_info')


# Export for convenience
__all__ = [
    'RateLimiter',
    'rate_limiter',
    'rate_limit',
    'get_rate_limit_info',
]
