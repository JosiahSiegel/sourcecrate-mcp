"""
SocArXiv (OSF Preprints) client for social science papers.
https://help.osf.io/hc/en-us/articles/360019738594-OSF-Preprints-API
"""

import logging
from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, api_status
from .http_client import create_http_client

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def search_socarxiv(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search SocArXiv for social science preprints"""
    cache_key = f"socarxiv:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = "https://api.osf.io/v2/preprints/"
        params = {
            "filter[provider]": "socarxiv",
            "filter[title,description]": query,
            "page[size]": limit
        }

        async with create_http_client() as client:
            response = await client.get(url, params=params)

            if response.status_code == 429:
                logger.warning("⚠️ SocArXiv API rate limited")
                raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("data", []):
                    attrs = item.get("attributes", {})
                    relationships = item.get("relationships", {})

                    # Get PDF URL from primary file
                    pdf_url = item.get("links", {}).get("preprint_download")

                    # Only include preprints with downloadable PDFs
                    if pdf_url:
                        result = {
                            "title": attrs.get("title", ""),
                            "authors": [contrib.get("users", {}).get("data", {}).get("attributes", {}).get("full_name", "")
                                       for contrib in attrs.get("contributors", [])],
                            "abstract": attrs.get("description", ""),
                            "year": attrs.get("date_published", "")[:4] if attrs.get("date_published") else None,
                            "doi": attrs.get("doi"),
                            "pdf_url": pdf_url,
                            "source": "SocArXiv",
                            "open_access": True,
                            "tags": attrs.get("tags", []),
                            "date_published": attrs.get("date_published"),
                            "license": attrs.get("license_record", {}).get("name", ""),
                            "url": item.get("links", {}).get("html", "")
                        }
                        results.append(result)

                # Cache for 2 hours
                cache.set(cache_key, results, expire=7200)
                logger.info(f"✅ SocArXiv: Found {len(results)} social science preprints for '{query}'")
                return results
            else:
                logger.warning(f"❌ SocArXiv API HTTP {response.status_code}: {response.text}")
                return []

    except httpx.HTTPStatusError:
        raise  # Let retry handle this
    except Exception as e:
        logger.warning(f"❌ SocArXiv search failed: {e}")
        api_status["socarxiv"] = False
        return []


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def search_osf_preprints_general(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search all OSF preprint providers for broader coverage"""
    cache_key = f"osf_preprints:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = "https://api.osf.io/v2/preprints/"
        params = {
            "filter[title,description]": query,
            "page[size]": limit
        }

        async with create_http_client() as client:
            response = await client.get(url, params=params)

            if response.status_code == 429:
                logger.warning("⚠️ OSF Preprints API rate limited")
                raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("data", []):
                    attrs = item.get("attributes", {})

                    # Get PDF URL from primary file
                    pdf_url = item.get("links", {}).get("preprint_download")

                    # Only include preprints with downloadable PDFs
                    if pdf_url:
                        provider = attrs.get("provider", "OSF")
                        result = {
                            "title": attrs.get("title", ""),
                            "authors": [contrib.get("users", {}).get("data", {}).get("attributes", {}).get("full_name", "")
                                       for contrib in attrs.get("contributors", [])],
                            "abstract": attrs.get("description", ""),
                            "year": attrs.get("date_published", "")[:4] if attrs.get("date_published") else None,
                            "doi": attrs.get("doi"),
                            "pdf_url": pdf_url,
                            "source": f"OSF-{provider}",
                            "open_access": True,
                            "tags": attrs.get("tags", []),
                            "date_published": attrs.get("date_published"),
                            "license": attrs.get("license_record", {}).get("name", ""),
                            "url": item.get("links", {}).get("html", "")
                        }
                        results.append(result)

                # Cache for 2 hours
                cache.set(cache_key, results, expire=7200)
                logger.info(f"✅ OSF Preprints: Found {len(results)} preprints for '{query}'")
                return results
            else:
                logger.warning(f"❌ OSF Preprints API HTTP {response.status_code}: {response.text}")
                return []

    except httpx.HTTPStatusError:
        raise  # Let retry handle this
    except Exception as e:
        logger.warning(f"❌ OSF Preprints search failed: {e}")
        api_status["osf_preprints"] = False
        return []