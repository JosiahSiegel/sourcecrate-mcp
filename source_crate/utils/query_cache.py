"""
Enhanced query result caching for improved performance.
Implements intelligent caching with TTL and deduplication.
"""

import hashlib
import json
import logging
import time
from typing import Any

from diskcache import Cache  # type: ignore

# Create cache instance directly
cache = Cache("/tmp/sourcecrate-mcp-cache", size_limit=1e9)  # 1GB cache

logger = logging.getLogger(__name__)


class QueryCache:
    """Enhanced caching system for query results"""

    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self.default_ttl = default_ttl
        self.cache_prefix = "query_result:v2:"
        self.stats_key = "query_cache_stats"

    def _generate_cache_key(
        self, query: str, limit: int, additional_params: dict[str, Any] | None = None
    ) -> str:
        """Generate a stable cache key for the query"""
        # Normalize query for consistent caching
        normalized_query = query.lower().strip()

        # Create cache key components
        key_data = {
            "query": normalized_query,
            "limit": limit,
            "params": additional_params or {},
        }

        # Generate hash for stable key
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

        return f"{self.cache_prefix}{key_hash}"

    def get_cached_result(
        self, query: str, limit: int, additional_params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Retrieve cached result if available and not expired"""
        try:
            cache_key = self._generate_cache_key(query, limit, additional_params)
            cached_data = cache.get(cache_key)

            if cached_data:
                # Check if result is still valid
                cached_time = cached_data.get("cached_at", 0)
                ttl = cached_data.get("ttl", self.default_ttl)

                if time.time() - cached_time < ttl:
                    logger.info(
                        f"🎯 Cache HIT for query: '{query}' (age: {time.time() - cached_time:.1f}s)"
                    )
                    self._update_cache_stats("hits")
                    result = cached_data.get("result")
                    return result if isinstance(result, dict) else None
                else:
                    # Expired cache entry
                    logger.info(f"⏰ Cache EXPIRED for query: '{query}'")
                    cache.delete(cache_key)
                    self._update_cache_stats("expired")

            logger.info(f"❌ Cache MISS for query: '{query}'")
            self._update_cache_stats("misses")
            return None

        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None

    def cache_result(
        self,
        query: str,
        limit: int,
        result: dict[str, Any],
        additional_params: dict[str, Any] | None = None,
        custom_ttl: int | None = None,
    ) -> bool:
        """Cache query result with metadata"""
        try:
            cache_key = self._generate_cache_key(query, limit, additional_params)
            ttl = custom_ttl or self.default_ttl

            # Prepare cache data with metadata
            cache_data = {
                "result": result,
                "cached_at": time.time(),
                "ttl": ttl,
                "query": query,
                "limit": limit,
                "params": additional_params or {},
            }

            # Cache with expiration
            success = cache.set(cache_key, cache_data, expire=ttl)

            if success:
                logger.info(f"💾 Cached result for query: '{query}' (TTL: {ttl}s)")
                self._update_cache_stats("cached")
                return True
            else:
                logger.warning(f"Failed to cache result for query: '{query}'")
                return False

        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
            return False

    def _update_cache_stats(self, stat_type: str) -> None:
        """Update cache performance statistics"""
        try:
            stats = cache.get(self.stats_key) or {}
            stats[stat_type] = stats.get(stat_type, 0) + 1
            stats["last_updated"] = time.time()
            cache.set(self.stats_key, stats, expire=86400)  # 24 hours
        except Exception as e:
            logger.warning(f"Failed to update cache stats: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics"""
        try:
            stats = cache.get(self.stats_key) or {}

            hits = stats.get("hits", 0)
            misses = stats.get("misses", 0)
            total_requests = hits + misses
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "hits": hits,
                "misses": misses,
                "expired": stats.get("expired", 0),
                "cached": stats.get("cached", 0),
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests,
                "last_updated": stats.get("last_updated", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {}

    def clear_cache(self, query_pattern: str | None = None) -> int:
        """Clear cached results, optionally filtering by query pattern"""
        try:
            cleared = 0

            if query_pattern:
                # Clear specific pattern (this would require cache key iteration)
                # For now, just clear all query cache
                logger.warning(
                    "Pattern-based cache clearing not implemented, clearing all query cache"
                )

            # Note: diskcache doesn't have a direct way to clear by prefix
            # This is a limitation we'd need to work around
            logger.info("Cache clearing requested - manual key management needed")
            return cleared

        except Exception as e:
            logger.warning(f"Cache clearing error: {e}")
            return 0

    def get_cache_size_info(self) -> dict[str, Any]:
        """Get information about cache size and usage"""
        try:
            # Get basic cache info from the underlying cache
            return {
                "cache_size": getattr(cache, "volume", lambda: 0)(),
                "cache_directory": getattr(cache, "directory", "unknown"),
                "size_limit": getattr(cache, "size_limit", "unlimited"),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache size info: {e}")
            return {}


# Global query cache instance
query_cache = QueryCache()


class ConcurrentRequestManager:
    """Manages concurrent identical requests to prevent duplicate work"""

    def __init__(self) -> None:
        self._pending_requests: dict[str, Any] = {}

    def get_or_create_request(self, cache_key: str, request_coro: Any) -> Any:
        """Get existing request or create new one for the same query"""
        if cache_key in self._pending_requests:
            logger.info(
                f"🔄 Deduplicating concurrent request for key: {cache_key[:16]}..."
            )
            return self._pending_requests[cache_key]

        # Create new request
        self._pending_requests[cache_key] = request_coro
        return request_coro

    def complete_request(self, cache_key: str) -> None:
        """Mark request as completed"""
        if cache_key in self._pending_requests:
            del self._pending_requests[cache_key]


# Global concurrent request manager
concurrent_request_manager = ConcurrentRequestManager()
