"""
Cache Middleware - Redis-backed caching layer
Provides function-level caching with configurable TTL
"""

import redis
import json
import hashlib
from functools import wraps
from typing import Optional, Callable, Any
import logging

# Import from config
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config.settings import REDIS_URL, CACHE_ENABLED, CACHE_TTL

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-backed cache manager with automatic serialization
    """

    def __init__(self, redis_url: str, enabled: bool = True):
        """
        Initialize cache manager

        Args:
            redis_url: Redis connection URL
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.redis_url = redis_url
        self._redis = None

        if self.enabled:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self._redis.ping()
                logger.info(f"Cache manager initialized successfully (Redis: {redis_url})")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, caching disabled: {e}")
                self.enabled = False

    @property
    def redis(self):
        """Get Redis client, lazy initialization"""
        if not self.enabled or self._redis is None:
            return None
        return self._redis

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled or self.redis is None:
            return None

        try:
            data = self.redis.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(data)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds
        """
        if not self.enabled or self.redis is None:
            return

        try:
            serialized = json.dumps(value, default=str)  # default=str handles datetime, etc.
            self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")

    def delete(self, key: str):
        """
        Delete a single key from cache

        Args:
            key: Cache key to delete
        """
        if not self.enabled or self.redis is None:
            return

        try:
            self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching a pattern

        Args:
            pattern: Redis key pattern (e.g., "user:123:*")
        """
        if not self.enabled or self.redis is None:
            return

        try:
            deleted_count = 0
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
                deleted_count += 1
            logger.info(f"Cache INVALIDATE: {pattern} ({deleted_count} keys)")
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern '{pattern}': {e}")

    def flush_all(self):
        """Flush all cache (use with caution)"""
        if not self.enabled or self.redis is None:
            return

        try:
            self.redis.flushdb()
            logger.warning("Cache FLUSH: All keys deleted")
        except Exception as e:
            logger.error(f"Cache flush error: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or self.redis is None:
            return {"enabled": False}

        try:
            info = self.redis.info("stats")
            return {
                "enabled": True,
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
cache_manager = CacheManager(REDIS_URL, enabled=CACHE_ENABLED)


def cached(key_prefix: str, ttl: Optional[int] = None):
    """
    Decorator for caching function results

    Args:
        key_prefix: Prefix for cache key (e.g., "dataset:list")
        ttl: Time-to-live in seconds (uses CACHE_TTL config if not specified)

    Example:
        @cached("user:profile", ttl=600)
        def get_user_profile(user_id: str):
            return fetch_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function args
            key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            cache_key = f"{key_prefix}:{key_hash}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Determine TTL
            effective_ttl = ttl
            if effective_ttl is None:
                # Try to match key_prefix with CACHE_TTL config
                for config_key, config_ttl in CACHE_TTL.items():
                    if config_key in key_prefix:
                        effective_ttl = config_ttl
                        break
                if effective_ttl is None:
                    effective_ttl = 300  # Default 5 minutes

            # Cache result
            cache_manager.set(cache_key, result, ttl=effective_ttl)

            return result

        return wrapper
    return decorator


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments

    Args:
        *args, **kwargs: Arguments to hash

    Returns:
        MD5 hash of arguments
    """
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def invalidate_cache(pattern: str):
    """
    Invalidate cache by pattern

    Args:
        pattern: Redis key pattern
    """
    cache_manager.invalidate_pattern(pattern)


# Export for convenience
__all__ = [
    'CacheManager',
    'cache_manager',
    'cached',
    'cache_key',
    'invalidate_cache',
]
