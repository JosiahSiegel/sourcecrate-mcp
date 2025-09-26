"""
HTTP client configuration for API requests.
"""

import httpx
from fake_useragent import UserAgent


def create_http_client() -> httpx.AsyncClient:
    """Create HTTP client with redirect handling and HTTP/2 support"""
    try:
        ua = UserAgent()
        user_agent = ua.random
    except:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    return httpx.AsyncClient(
        follow_redirects=True,
        http2=True,
        timeout=60.0,
        headers={"User-Agent": user_agent},
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
    )