"""
Google Scholar API client with proxy support.
"""

import asyncio
import logging
from typing import Any

from fake_useragent import UserAgent
from scholarly import ProxyGenerator, scholarly
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import api_status, cache, config

logger = logging.getLogger(__name__)


def setup_scraperapi():
    """Try ScraperAPI proxy setup"""
    try:
        if config.scraperapi_key:
            pg = ProxyGenerator()
            pg.ScraperAPI(config.scraperapi_key)
            scholarly.use_proxy(pg)
            # Light test the proxy with timeout
            try:
                test_query = scholarly.search_pubs("ai")
                next(test_query)
            except:
                # If test fails, still try - might work for actual queries
                pass
            return True
    except:
        return False


def setup_free_proxies():
    """Try free proxies setup"""
    try:
        pg = ProxyGenerator()
        pg.FreeProxies(timeout=5, wait_time=30)  # Shorter timeouts
        scholarly.use_proxy(pg)
        # Light test the proxy
        try:
            test_query = scholarly.search_pubs("ai")
            next(test_query)
        except:
            # If test fails, still try - might work for actual queries
            pass
        return True
    except:
        return False


def setup_tor_proxy():
    """Try Tor proxy setup"""
    try:
        pg = ProxyGenerator()
        pg.Tor()  # Requires tor to be installed
        scholarly.use_proxy(pg)
        # Light test the proxy
        try:
            test_query = scholarly.search_pubs("ai")
            next(test_query)
        except:
            # If test fails, still try - might work for actual queries
            pass
        return True
    except:
        return False


def setup_no_proxy():
    """Try direct connection with user agent rotation"""
    try:
        # Clear any existing proxy
        scholarly.use_proxy(None)
        # Setup user agent rotation
        UserAgent()
        # Skip test query for direct connection - it should work
        return True
    except:
        return False


def setup_scholarly_proxy():
    """Enhanced proxy setup with multiple fallbacks"""
    proxy_methods = [
        ("scraperapi", setup_scraperapi),
        ("free_proxies", setup_free_proxies),
        ("tor", setup_tor_proxy),
        ("no_proxy", setup_no_proxy)
    ]

    for name, setup_func in proxy_methods:
        try:
            if setup_func():
                logger.info(f"✅ Google Scholar configured with {name}")
                api_status["google_scholar"] = True
                return True
        except Exception as e:
            logger.warning(f"⚠️ {name} failed: {e}")

    logger.warning("❌ All proxy methods failed")
    api_status["google_scholar"] = False
    return False


async def _search_google_scholar(query: str, limit: int) -> list[dict[str, Any]]:
    """Internal Google Scholar search function"""
    def _search_scholar():
        search_query = scholarly.search_pubs(query)
        results = []

        for i, pub in enumerate(search_query):
            if i >= limit:
                break

            bib = pub.get('bib', {})
            result = {
                "title": bib.get('title', ''),
                "authors": bib.get('author', []),
                "year": bib.get('pub_year', ''),
                "abstract": bib.get('abstract', ''),
                "venue": bib.get('venue', ''),
                "citation_count": pub.get('num_citations', 0),
                "url": pub.get('pub_url', ''),
                "source": "Google Scholar"
            }
            results.append(result)
        return results

    return await asyncio.to_thread(_search_scholar)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=30))
async def search_google_scholar_with_retry(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search with automatic proxy rotation on failure"""
    try:
        return await _search_google_scholar(query, limit)
    except Exception as e:
        logger.warning(f"Google Scholar search failed, rotating proxy: {e}")
        setup_scholarly_proxy()  # Try different proxy
        raise  # Trigger retry


async def search_google_scholar_fallback(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Google Scholar as final fallback with enhanced proxy support"""
    # Initialize proxy if not already done
    if not api_status.get("google_scholar", False):
        setup_scholarly_proxy()

    if not api_status.get("google_scholar", False):
        logger.info("⏭️ Google Scholar unavailable, skipping")
        return []

    cache_key = f"scholar:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        results = await search_google_scholar_with_retry(query, limit)

        # Cache for 30 minutes (shorter due to potential blocking)
        cache.set(cache_key, results, expire=1800)
        logger.info(f"✅ Google Scholar: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ Google Scholar search failed after retries: {e}")
        api_status["google_scholar"] = False
        return []
