"""
Download Reliability Utilities

Provides stateless URL domain extraction for client-side download tracking.

ARCHITECTURE NOTE:
Previously this module tracked download reliability server-side using diskcache.
This created a scalability bottleneck for high-traffic deployments (1M user target).

NEW APPROACH - Client-Side Tracking:
- Clients track their own download success/failure rates (browser localStorage, etc.)
- Server provides stateless utilities (domain extraction, URL parsing)
- No shared server-side state = horizontal scalability

This module is kept for backward compatibility but all functions are now stateless.
"""

import logging
from typing import Literal
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_domain(url: str) -> str:
    """
    Extract domain from URL for client-side tracking.

    Args:
        url: Full URL to extract domain from

    Returns:
        Domain string (e.g., "arxiv.org") or "unknown" if parsing fails
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() or "unknown"
    except Exception:
        return "unknown"


def record_download_attempt(url: str, success: bool) -> None:
    """
    DEPRECATED: No-op function for backward compatibility.

    Previously tracked download attempts server-side. Now clients should
    track their own download reliability using localStorage or similar.

    Args:
        url: The URL that was attempted (ignored)
        success: Whether the download succeeded (ignored)
    """
    pass  # Stateless - no server-side tracking


def get_download_reliability(
    url: str,
) -> tuple[Literal["downloadable", "unreliable", "browser_required"], dict]:
    """
    STATELESS: Always returns optimistic "downloadable" status.

    Previously returned server-side cached reliability statistics.
    Now clients should track their own download reliability.

    Args:
        url: The URL to check (only used for domain extraction)

    Returns:
        Tuple of (status, stats) where:
        - status: Always "downloadable" (optimistic)
        - stats: Empty stats dict (no server-side tracking)

    Example client-side tracking:
        ```javascript
        // In browser JavaScript
        const domain = new URL(pdfUrl).hostname;
        const stats = JSON.parse(localStorage.getItem(`download_stats_${domain}`)) || {
            attempts: 0, successes: 0
        };

        // After download attempt:
        stats.attempts++;
        if (success) stats.successes++;
        localStorage.setItem(`download_stats_${domain}`, JSON.stringify(stats));
        ```
    """
    return "downloadable", {"attempts": 0, "successes": 0, "success_rate": 0.0}
