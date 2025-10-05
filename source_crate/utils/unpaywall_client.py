"""
Unpaywall API client for finding legal open access versions of papers.

Unpaywall (https://unpaywall.org) is a database of 30+ million free scholarly articles.
It's used by researchers to find legal open access versions when publisher sites are blocked.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class UnpaywallClient:
    """Client for Unpaywall API to find open access versions of papers."""

    def __init__(self, email: str = "research@paperez-mcp.org") -> None:
        """
        Initialize Unpaywall client.

        Args:
            email: Email address required by Unpaywall API (for contact/rate limiting)
        """
        self.base_url = "https://api.unpaywall.org/v2"
        self.email = email
        self.timeout = 10.0

    async def find_open_access_pdf(self, doi: str) -> dict[str, Any] | None:
        """
        Find open access PDF for a given DOI.

        Args:
            doi: Digital Object Identifier (e.g., "10.1257/jep.25.1.209")

        Returns:
            Dictionary with open access info, or None if not found:
            {
                "is_oa": bool,
                "best_oa_location": {
                    "url_for_pdf": str,
                    "url": str,
                    "version": str,  # "publishedVersion", "acceptedVersion", "submittedVersion"
                    "license": str
                },
                "oa_locations": list  # All open access locations
            }
        """
        if not doi:
            return None

        # Clean DOI (remove https://doi.org/ prefix if present)
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

        url = f"{self.base_url}/{doi}"
        params = {"email": self.email}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    # Check if open access is available
                    if data.get("is_oa") and data.get("best_oa_location"):
                        logger.info(
                            f"✅ Unpaywall: Found open access version for DOI {doi}"
                        )
                        return {
                            "is_oa": True,
                            "best_oa_location": data["best_oa_location"],
                            "oa_locations": data.get("oa_locations", []),
                        }
                    else:
                        logger.info(
                            f"❌ Unpaywall: No open access version found for DOI {doi}"
                        )
                        return {"is_oa": False}

                elif response.status_code == 404:
                    logger.info(f"❌ Unpaywall: DOI not found: {doi}")
                    return None

                else:
                    logger.warning(
                        f"⚠️  Unpaywall API returned {response.status_code} for DOI {doi}"
                    )
                    return None

        except httpx.TimeoutException:
            logger.warning(f"⏱️  Unpaywall API timeout for DOI {doi}")
            return None
        except Exception as e:
            logger.warning(f"❌ Unpaywall API error for DOI {doi}: {e}")
            return None


# Global instance for reuse
_unpaywall_client: UnpaywallClient | None = None


def get_unpaywall_client(email: str | None = None) -> UnpaywallClient:
    """Get or create global Unpaywall client instance.

    Args:
        email: Email for Unpaywall API. If None, uses UNPAYWALL_EMAIL env var,
               or falls back to default.
    """
    global _unpaywall_client
    if _unpaywall_client is None:
        # Priority: parameter > environment variable > default
        final_email = email or os.getenv("UNPAYWALL_EMAIL", "research@paperez-mcp.org")
        _unpaywall_client = UnpaywallClient(email=final_email)
        logger.info(f"Initialized Unpaywall client with email: {final_email}")
    return _unpaywall_client
