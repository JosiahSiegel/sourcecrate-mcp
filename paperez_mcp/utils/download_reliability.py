"""
Download Reliability Tracker

Tracks PDF download success/failure rates per domain to provide smart UX.
Uses disk cache for persistence across server restarts.

Key Features:
- Self-learning: No hardcoded domain lists
- Adaptive: Adjusts based on actual success rates
- Persistent: Uses existing disk cache infrastructure
- Gradual: Starts optimistic, learns from failures
"""

import logging
from typing import Literal
from urllib.parse import urlparse

from diskcache import Cache

logger = logging.getLogger(__name__)

# Cache for domain reliability statistics (24 hour TTL, 10MB max size)
_reliability_cache: Cache | None = None
RELIABILITY_TTL = 86400  # 24 hours
CACHE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB


def get_reliability_cache() -> Cache:
    """Get or create the reliability statistics cache."""
    global _reliability_cache
    if _reliability_cache is None:
        from pathlib import Path

        cache_dir = Path.home() / ".cache" / "paperez-mcp" / "reliability"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _reliability_cache = Cache(str(cache_dir), size_limit=CACHE_SIZE_LIMIT)
        logger.info(
            f"Initialized reliability cache at {cache_dir} (max {CACHE_SIZE_LIMIT / 1024 / 1024:.0f}MB)"
        )
    return _reliability_cache


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() or "unknown"
    except Exception:
        return "unknown"


def record_download_attempt(url: str, success: bool) -> None:
    """
    Record a download attempt and its outcome.

    Args:
        url: The URL that was attempted
        success: Whether the download succeeded
    """
    domain = get_domain(url)
    if domain == "unknown":
        return

    cache = get_reliability_cache()
    key = f"domain:{domain}"

    # Get current stats
    stats = cache.get(key, {"attempts": 0, "successes": 0})

    # Update stats
    stats["attempts"] += 1
    if success:
        stats["successes"] += 1

    # Calculate success rate
    stats["success_rate"] = (
        stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0.0
    )

    # Store updated stats with TTL
    cache.set(key, stats, expire=RELIABILITY_TTL)

    logger.debug(
        f"Recorded {'success' if success else 'failure'} for {domain}: "
        f"{stats['successes']}/{stats['attempts']} "
        f"({stats['success_rate']:.1%} success rate)"
    )


def get_download_reliability(
    url: str,
) -> tuple[Literal["downloadable", "unreliable", "browser_required"], dict]:
    """
    Get reliability assessment for a URL.

    Returns:
        Tuple of (status, stats) where:
        - status: "downloadable", "unreliable", or "browser_required"
        - stats: Dictionary with attempts, successes, success_rate

    Decision Logic:
        - browser_required: <20% success rate AND >5 attempts
        - unreliable: <50% success rate AND >10 attempts
        - downloadable: Everything else (optimistic default)
    """
    domain = get_domain(url)
    if domain == "unknown":
        return "downloadable", {"attempts": 0, "successes": 0, "success_rate": 0.0}

    cache = get_reliability_cache()
    key = f"domain:{domain}"
    stats = cache.get(key, {"attempts": 0, "successes": 0, "success_rate": 0.0})

    # Calculate success rate if not already present
    if "success_rate" not in stats and stats["attempts"] > 0:
        stats["success_rate"] = stats["successes"] / stats["attempts"]
    elif "success_rate" not in stats:
        stats["success_rate"] = 0.0

    attempts = stats["attempts"]
    success_rate = stats["success_rate"]

    # Determine reliability status
    if success_rate < 0.2 and attempts >= 5:
        # Consistently fails - requires browser
        status = "browser_required"
        logger.info(
            f"Domain {domain} marked as browser_required: "
            f"{success_rate:.1%} success rate over {attempts} attempts"
        )
    elif success_rate < 0.5 and attempts >= 10:
        # Sometimes works, sometimes doesn't
        status = "unreliable"
        logger.info(
            f"Domain {domain} marked as unreliable: "
            f"{success_rate:.1%} success rate over {attempts} attempts"
        )
    else:
        # Unknown or usually works - stay optimistic
        status = "downloadable"

    return status, stats  # type: ignore[return-value]


def get_all_domain_stats() -> dict[str, dict]:
    """Get statistics for all tracked domains."""
    cache = get_reliability_cache()
    stats = {}

    for key in cache.iterkeys():
        if isinstance(key, str) and key.startswith("domain:"):
            domain = key.replace("domain:", "")
            stats[domain] = cache.get(key, {})

    return stats
