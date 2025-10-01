"""
Utilities for detecting Cloudflare protection and access issues.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def is_cloudflare_challenge(response: httpx.Response) -> bool:
    """
    Detect if HTTP response is a Cloudflare challenge/block.

    Args:
        response: httpx Response object

    Returns:
        True if response appears to be Cloudflare protection
    """
    # Check status codes commonly used by Cloudflare
    if response.status_code in [403, 503, 429]:
        # Check headers for Cloudflare signatures
        headers_lower = {k.lower(): v for k, v in response.headers.items()}

        # Cloudflare-specific headers
        if any(
            header in headers_lower
            for header in ["cf-ray", "cf-cache-status", "cf-request-id"]
        ):
            logger.debug("Detected Cloudflare headers in response")
            return True

        # Check response body for Cloudflare challenge patterns
        try:
            body = response.text.lower()
            cloudflare_patterns = [
                "checking your browser",
                "cloudflare",
                "cf-browser-verification",
                "ray id",
                "just a moment",
                "enable javascript and cookies",
            ]

            if any(pattern in body for pattern in cloudflare_patterns):
                logger.debug("Detected Cloudflare challenge in response body")
                return True
        except Exception:
            pass  # Body might not be text

    return False


def get_cloudflare_info(response: httpx.Response) -> dict[str, Any]:
    """
    Extract Cloudflare information from response.

    Args:
        response: httpx Response object

    Returns:
        Dictionary with Cloudflare info:
        {
            "is_cloudflare": bool,
            "cf_ray": str | None,
            "status_code": int,
            "likely_reason": str
        }
    """
    headers_lower = {k.lower(): v for k, v in response.headers.items()}

    is_cf = is_cloudflare_challenge(response)
    cf_ray = headers_lower.get("cf-ray")

    # Determine likely reason for block
    reason = "Unknown"
    if response.status_code == 403:
        reason = "Access forbidden (bot detection or geographic restriction)"
    elif response.status_code == 503:
        reason = "Service temporarily unavailable (challenge required)"
    elif response.status_code == 429:
        reason = "Rate limit exceeded"

    return {
        "is_cloudflare": is_cf,
        "cf_ray": cf_ray,
        "status_code": response.status_code,
        "likely_reason": reason,
    }


def suggest_alternatives(
    url: str, doi: str | None = None, unpaywall_urls: list[str] | None = None
) -> list[str]:
    """
    Suggest alternative methods to access a Cloudflare-protected resource.

    Args:
        url: Original URL that failed
        doi: DOI of the paper (if available)
        unpaywall_urls: List of Unpaywall open access URLs that were tried (if available)

    Returns:
        List of suggestion strings for user
    """
    suggestions = []

    # If Unpaywall URLs are available, prioritize them for manual browser download
    if unpaywall_urls:
        suggestions.append(
            "📄 Try these open access versions manually in your browser:"
        )
        for idx, oa_url in enumerate(unpaywall_urls[:3], start=1):  # Top 3
            suggestions.append(f"   {idx}. {oa_url}")
        suggestions.append("")  # Blank line for readability

    if doi:
        suggestions.append(
            f"1. Search Google Scholar for more sources: https://scholar.google.com/scholar?q={doi}"
        )

    suggestions.append(f"2. Try downloading manually from original URL: {url}")
    suggestions.append(
        "3. Check if your institution provides access through a proxy/VPN"
    )
    suggestions.append(
        "5. Enable browser automation in config (if available) to bypass bot detection"
    )

    return suggestions
