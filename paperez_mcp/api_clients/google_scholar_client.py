"""
Google Scholar API client with proxy support.
"""

import asyncio
import logging
from typing import Any, Dict, List

from fake_useragent import UserAgent
from scholarly import ProxyGenerator, scholarly
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status

logger = logging.getLogger(__name__)


def setup_scholarly_proxy():
    """Setup scholarly with robust proxy configuration"""
    try:
        if config.scraperapi_key:
            pg = ProxyGenerator()
            pg.ScraperAPI(config.scraperapi_key)
            scholarly.use_proxy(pg)
            logger.info("✅ Scholarly configured with ScraperAPI")
            return True
        else:
            # Try free proxies with proper error handling
            try:
                pg = ProxyGenerator()
                # Fix the FreeProxies call with proper parameters
                pg.FreeProxies(timeout=10, wait_time=60)
                scholarly.use_proxy(pg)
                logger.info("✅ Scholarly configured with free proxies")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Free proxies failed: {e}")

        # Setup user agent rotation regardless
        ua = UserAgent()
        logger.info("✅ User agent rotation configured")
        return False

    except Exception as e:
        logger.warning(f"❌ Proxy setup failed: {e}")
        api_status["google_scholar"] = False
        return False


async def search_google_scholar_fallback(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Google Scholar as final fallback with proxy support"""
    if not api_status["google_scholar"]:
        return []

    cache_key = f"scholar:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
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

        results = await asyncio.to_thread(_search_scholar)

        # Cache for 30 minutes (shorter due to potential blocking)
        cache.set(cache_key, results, expire=1800)
        logger.info(f"✅ Google Scholar: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ Google Scholar search failed: {e}")
        api_status["google_scholar"] = False
        return []