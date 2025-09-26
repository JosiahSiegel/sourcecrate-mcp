#!/usr/bin/env python3
"""
Enhanced Configuration for Scholarly MCP Server

This module provides configuration management for the enhanced scholarly server,
including API keys, proxy settings, and caching configurations.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from scholarly import scholarly, ProxyGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration for external APIs"""
    semantic_scholar_key: Optional[str] = None
    core_api_key: Optional[str] = None
    unpaywall_email: str = "research@example.com"
    enable_rate_limiting: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30

@dataclass
class PDFConfig:
    """Configuration for PDF processing"""
    max_pdf_size_mb: int = 50
    extraction_timeout: int = 60
    temp_dir: str = "/tmp"
    cleanup_temp_files: bool = True

@dataclass
class CacheConfig:
    """Configuration for caching"""
    enable_caching: bool = False
    cache_ttl_hours: int = 24
    redis_url: Optional[str] = None
    disk_cache_dir: str = "/tmp/scholarly_cache"

class EnhancedConfig:
    """Main configuration class for the enhanced server"""

    def __init__(self):
        self.api = APIConfig()
        self.pdf = PDFConfig()
        self.cache = CacheConfig()
        self._load_from_environment()

    def _load_from_environment(self):
        """Load configuration from environment variables"""

        # API Configuration
        self.api.semantic_scholar_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        self.api.core_api_key = os.getenv('CORE_API_KEY')
        self.api.unpaywall_email = os.getenv('UNPAYWALL_EMAIL', self.api.unpaywall_email)

        # PDF Configuration
        if os.getenv('MAX_PDF_SIZE_MB'):
            self.pdf.max_pdf_size_mb = int(os.getenv('MAX_PDF_SIZE_MB'))

        if os.getenv('PDF_TIMEOUT'):
            self.pdf.extraction_timeout = int(os.getenv('PDF_TIMEOUT'))

        self.pdf.temp_dir = os.getenv('TEMP_DIR', self.pdf.temp_dir)

        # Cache Configuration
        self.cache.enable_caching = os.getenv('ENABLE_CACHING', 'false').lower() == 'true'
        self.cache.redis_url = os.getenv('REDIS_URL')
        self.cache.disk_cache_dir = os.getenv('CACHE_DIR', self.cache.disk_cache_dir)

        if os.getenv('CACHE_TTL_HOURS'):
            self.cache.cache_ttl_hours = int(os.getenv('CACHE_TTL_HOURS'))

def setup_proxy():
    """
    Setup proxy configuration for scholarly if needed.
    This helps avoid being blocked by Google Scholar.
    """
    proxy_type = os.getenv('PROXY_TYPE', 'none').lower()

    if proxy_type == 'none':
        logger.info("No proxy configured, using direct connection")
        return

    pg = ProxyGenerator()
    success = False

    try:
        if proxy_type == 'free':
            logger.info("Setting up free proxy...")
            success = pg.FreeProxies()

        elif proxy_type == 'scraperapi':
            api_key = os.getenv('SCRAPERAPI_KEY')
            if api_key:
                logger.info("Setting up ScraperAPI proxy...")
                success = pg.ScraperAPI(api_key)
            else:
                logger.error("SCRAPERAPI_KEY not found in environment variables")

        elif proxy_type == 'luminati':
            username = os.getenv('LUMINATI_USERNAME')
            password = os.getenv('LUMINATI_PASSWORD')
            port = os.getenv('LUMINATI_PORT')

            if username and password and port:
                logger.info("Setting up Luminati proxy...")
                success = pg.Luminati(usr=username, passwd=password, port=port)
            else:
                logger.error("Luminati credentials not complete in environment variables")

        elif proxy_type == 'single':
            http_proxy = os.getenv('HTTP_PROXY')
            https_proxy = os.getenv('HTTPS_PROXY')

            if http_proxy or https_proxy:
                logger.info("Setting up single proxy...")
                success = pg.SingleProxy(http=http_proxy, https=https_proxy)
            else:
                logger.error("HTTP_PROXY or HTTPS_PROXY not found")

        if success:
            scholarly.use_proxy(pg)
            logger.info("Proxy setup successful")
        else:
            logger.warning("Proxy setup failed, using direct connection")

    except Exception as e:
        logger.error(f"Proxy setup error: {e}, using direct connection")

def get_api_headers() -> Dict[str, Dict[str, str]]:
    """Get API headers for external services"""
    config = EnhancedConfig()
    headers = {}

    # Semantic Scholar headers
    if config.api.semantic_scholar_key:
        headers['semantic_scholar'] = {
            'x-api-key': config.api.semantic_scholar_key
        }

    # CORE API headers
    if config.api.core_api_key:
        headers['core'] = {
            'Authorization': f'Bearer {config.api.core_api_key}'
        }

    return headers

def validate_environment():
    """Validate environment configuration and log warnings"""
    config = EnhancedConfig()
    warnings = []

    # Check for recommended API keys
    if not config.api.semantic_scholar_key:
        warnings.append("SEMANTIC_SCHOLAR_API_KEY not set - using rate-limited free tier")

    if not config.api.core_api_key:
        warnings.append("CORE_API_KEY not set - CORE API features will be limited")

    # Check email for Unpaywall
    if config.api.unpaywall_email == "research@example.com":
        warnings.append("Using default email for Unpaywall API - consider setting UNPAYWALL_EMAIL")

    # Check disk space for temp files
    temp_dir = config.pdf.temp_dir
    if not os.path.exists(temp_dir):
        try:
            os.makedirs(temp_dir, exist_ok=True)
            logger.info(f"Created temp directory: {temp_dir}")
        except Exception as e:
            warnings.append(f"Cannot create temp directory {temp_dir}: {e}")

    # Log warnings
    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    else:
        logger.info("Environment configuration validated successfully")

    return len(warnings) == 0

# Global configuration instance
CONFIG = EnhancedConfig()

# Environment setup on import
if __name__ != "__main__":
    validate_environment()
    setup_proxy()

if __name__ == "__main__":
    # Test configuration when run directly
    print("Enhanced Scholarly MCP Server Configuration")
    print("=" * 50)

    config = EnhancedConfig()
    print(f"Semantic Scholar API Key: {'Set' if config.api.semantic_scholar_key else 'Not set'}")
    print(f"CORE API Key: {'Set' if config.api.core_api_key else 'Not set'}")
    print(f"Unpaywall Email: {config.api.unpaywall_email}")
    print(f"Max PDF Size: {config.pdf.max_pdf_size_mb} MB")
    print(f"Caching Enabled: {config.cache.enable_caching}")
    print(f"Proxy Type: {os.getenv('PROXY_TYPE', 'none')}")

    print("\nValidating configuration...")
    is_valid = validate_environment()
    print(f"Configuration valid: {is_valid}")

    print("\nTesting proxy setup...")
    setup_proxy()