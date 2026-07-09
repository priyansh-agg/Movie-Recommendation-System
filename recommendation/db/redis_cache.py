"""
Redis caching layer for recommendation results.

Wraps any service call with a cache-aside pattern:
    1. Check Redis for cached result.
    2. If miss, compute result and store in Redis with TTL.
    3. If hit, deserialise and return immediately.

Falls back gracefully if Redis is unavailable — the system
works without caching, just slower.
"""

import hashlib
import json
import logging
from typing import Any

import redis

from recommendation.db.config import REDIS_URL

logger = logging.getLogger(__name__)

# TTLs in seconds
TTL_SIMILAR = 3600       # 1 hour
TTL_USER_RECS = 900      # 15 minutes
TTL_HOMEPAGE = 600       # 10 minutes
TTL_SEARCH = 1800        # 30 minutes
TTL_POSTER = 86400       # 24 hours


class RedisCache:
    """
    Thin wrapper around Redis with graceful degradation.

    If Redis is down, all operations silently return None / no-op.
    """

    def __init__(self, url: str = REDIS_URL):
        try:
            self._client = redis.from_url(url, decode_responses=True)
            self._client.ping()
            self._available = True
            logger.info("Redis connected: %s", url)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            self._client = None
            self._available = False
            logger.warning("Redis unavailable (%s), caching disabled", e)

    @property
    def available(self) -> bool:
        return self._available

    # ── Core operations ─────────────────────────────────────────────

    def get(self, key: str) -> Any | None:
        """Get a cached value.  Returns None on miss or error."""
        if not self._available:
            return None
        try:
            data = self._client.get(key)
            if data is not None:
                return json.loads(data)
        except (redis.RedisError, json.JSONDecodeError):
            pass
        return None

    def set(self, key: str, value: Any, ttl: int = 600) -> None:
        """Set a cached value with TTL.  No-op on error."""
        if not self._available:
            return
        try:
            self._client.setex(key, ttl, json.dumps(value, default=str))
        except redis.RedisError:
            pass

    def delete(self, key: str) -> None:
        """Delete a cached key."""
        if not self._available:
            return
        try:
            self._client.delete(key)
        except redis.RedisError:
            pass

    def invalidate_user(self, user_id: int) -> None:
        """Invalidate all cached recommendations for a user."""
        if not self._available:
            return
        try:
            # Delete known user-specific keys
            patterns = [
                f"recs:user:{user_id}:*",
                f"recs:homepage:{user_id}",
            ]
            for pattern in patterns:
                for key in self._client.scan_iter(match=pattern, count=100):
                    self._client.delete(key)
        except redis.RedisError:
            pass

    # ── Key builders ────────────────────────────────────────────────

    @staticmethod
    def key_similar(movie_titles: list[str], top_n: int) -> str:
        h = hashlib.md5(
            json.dumps(sorted(movie_titles)).encode()
        ).hexdigest()[:12]
        return f"recs:similar:{h}:{top_n}"

    @staticmethod
    def key_user_recs(user_id: int, top_n: int) -> str:
        return f"recs:user:{user_id}:{top_n}"

    @staticmethod
    def key_homepage(user_id: int | None) -> str:
        uid = user_id if user_id is not None else "anon"
        return f"recs:homepage:{uid}"

    @staticmethod
    def key_search(query: str, max_results: int) -> str:
        return f"search:{query.lower().strip()}:{max_results}"

    @staticmethod
    def key_poster(tmdb_id: int) -> str:
        return f"poster:{tmdb_id}"
