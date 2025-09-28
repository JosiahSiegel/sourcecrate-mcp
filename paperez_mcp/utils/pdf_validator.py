"""
PDF Validator Utility

Validates PDF URLs and improves PDF availability across academic sources.
Addresses Issue 4.1: Low PDF Availability Across Sources from COMPREHENSIVE_ISSUE_RESOLUTION.md
"""

import asyncio
import logging
import re

import aiohttp

from ..config import get_current_config

logger = logging.getLogger(__name__)


class PDFValidator:
    """Validates PDF URLs and provides fallback mechanisms for better PDF availability"""

    def __init__(self) -> None:
        # Common PDF URL patterns for different sources
        self.pdf_patterns = {
            "arxiv": {
                "pattern": r"arxiv\.org/abs/(\d{4}\.\d{4,5})",
                "pdf_url": "http://arxiv.org/pdf/{}.pdf",
            },
            "pmc": {
                "pattern": r"pmc/articles/PMC(\d+)",
                "pdf_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{}/pdf/",
            },
            "doi": {
                "pattern": r"10\.\d{4,}\/[^\s]+",
                "unpaywall_url": "https://api.unpaywall.org/v2/{}?email=paperez-mcp@github.com",
            },
        }

        # Cache for validated URLs to avoid repeated checks
        self._validation_cache: dict[str, bool] = {}

        # Timeout for HTTP requests
        self.timeout = aiohttp.ClientTimeout(total=10, connect=5)

    def get_all_pdf_patterns(self) -> dict[str, list[str]]:
        """
        Get all PDF patterns including both built-in and capability-based patterns.

        Returns:
            Dict mapping source names to lists of regex patterns
        """
        all_patterns = {}

        # Add built-in patterns
        for source, pattern_info in self.pdf_patterns.items():
            if "pattern" in pattern_info:
                all_patterns[source] = [pattern_info["pattern"]]

        # Add capability-based patterns from configuration
        try:
            config = get_current_config()
            for source_name, source_config in config.sources.items():
                if (
                    source_config.enabled
                    and source_config.capabilities
                    and source_config.capabilities.pdf_url_patterns
                ):
                    if source_name not in all_patterns:
                        all_patterns[source_name] = []
                    all_patterns[source_name].extend(
                        source_config.capabilities.pdf_url_patterns
                    )
        except Exception as e:
            logger.warning(f"Could not load capability-based PDF patterns: {e}")

        return all_patterns

    async def validate_pdf_url(self, url: str) -> tuple[bool, str | None]:
        """
        Validate if a PDF URL is accessible

        Args:
            url: PDF URL to validate

        Returns:
            Tuple of (is_valid, actual_url)
        """
        if not url or not isinstance(url, str):
            return False, None

        url = url.strip()
        if not url:
            return False, None

        # Check cache first
        if url in self._validation_cache:
            return self._validation_cache[url], (
                url if self._validation_cache[url] else None
            )

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Use HEAD request to check if URL exists without downloading
                async with session.head(url, allow_redirects=True) as response:
                    is_valid = (
                        response.status == 200
                        and "application/pdf"
                        in response.headers.get("content-type", "").lower()
                    )

                    self._validation_cache[url] = is_valid
                    return is_valid, url if is_valid else None

        except Exception as e:
            logger.debug(f"PDF validation failed for {url}: {e}")
            self._validation_cache[url] = False
            return False, None

    def extract_arxiv_pdf_url(self, text: str) -> str | None:
        """Extract arXiv PDF URL from text containing arXiv identifier"""
        match = re.search(self.pdf_patterns["arxiv"]["pattern"], text)
        if match:
            arxiv_id = match.group(1)
            return self.pdf_patterns["arxiv"]["pdf_url"].format(arxiv_id)
        return None

    def extract_pmc_pdf_url(self, text: str) -> str | None:
        """Extract PMC PDF URL from text containing PMC identifier"""
        match = re.search(self.pdf_patterns["pmc"]["pattern"], text)
        if match:
            pmc_id = match.group(1)
            return self.pdf_patterns["pmc"]["pdf_url"].format(pmc_id)
        return None

    def fix_common_pdf_url_issues(self, url: str) -> str:
        """Fix common issues with PDF URLs"""
        if not url:
            return url

        # Remove extra whitespace
        url = url.strip()

        # Fix missing protocol
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Fix common malformed URLs
        # Fix duplicate slashes (except after protocol)
        url = re.sub(r"(?<!:)//+", "/", url)

        # Fix missing file extension for known PDF paths
        if "/pdf/" in url and not url.endswith(".pdf"):
            if not url.endswith("/"):
                url += "/"

        return url

    async def find_alternative_pdf_urls(self, paper_data: dict) -> list[str]:
        """
        Find alternative PDF URLs for a paper using various strategies

        Args:
            paper_data: Paper metadata dictionary

        Returns:
            List of potential PDF URLs
        """
        alternatives = []

        # Strategy 1: Extract from arXiv ID
        for field in ["arxiv_id", "url", "title"]:
            value = paper_data.get(field, "")
            if isinstance(value, str):
                arxiv_url = self.extract_arxiv_pdf_url(value)
                if arxiv_url:
                    alternatives.append(arxiv_url)

        # Strategy 2: Extract from PMC ID
        for field in ["pmc_id", "url", "full_text_url"]:
            value = paper_data.get(field, "")
            if isinstance(value, str):
                pmc_url = self.extract_pmc_pdf_url(value)
                if pmc_url:
                    alternatives.append(pmc_url)

        # Strategy 3: Try to construct URLs from DOI
        doi = paper_data.get("doi")
        if doi:
            # Some publishers have predictable PDF URL patterns
            doi_alternatives = await self._get_doi_pdf_alternatives(doi)
            alternatives.extend(doi_alternatives)

        # Remove duplicates while preserving order
        seen = set()
        unique_alternatives = []
        for url in alternatives:
            if url and url not in seen:
                seen.add(url)
                unique_alternatives.append(url)

        return unique_alternatives

    async def _get_doi_pdf_alternatives(self, doi: str) -> list[str]:
        """Get alternative PDF URLs based on DOI using multiple sources"""
        alternatives = []

        # Strategy 1: Try Unpaywall API for open access PDFs
        try:
            unpaywall_url = self.pdf_patterns["doi"]["unpaywall_url"].format(doi)
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(unpaywall_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("is_oa"):
                            # Get best open access location
                            best_oa = data.get("best_oa_location")
                            if best_oa and best_oa.get("url_for_pdf"):
                                alternatives.append(best_oa["url_for_pdf"])

                            # Also check all open access locations for additional PDFs
                            oa_locations = data.get("oa_locations", [])
                            for location in oa_locations:
                                pdf_url = location.get("url_for_pdf")
                                if pdf_url and pdf_url not in alternatives:
                                    alternatives.append(pdf_url)

                        logger.debug(
                            f"Unpaywall found {len(alternatives)} open access PDFs for DOI {doi}"
                        )
                    elif response.status == 404:
                        logger.debug(f"DOI {doi} not found in Unpaywall database")
                    else:
                        logger.debug(
                            f"Unpaywall API returned status {response.status} for DOI {doi}"
                        )
        except Exception as e:
            logger.debug(f"Unpaywall lookup failed for DOI {doi}: {e}")

        # Strategy 2: Try publisher-specific PDF URL patterns
        publisher_patterns = self._get_publisher_pdf_patterns(doi)
        for pattern_url in publisher_patterns:
            if pattern_url not in alternatives:
                alternatives.append(pattern_url)

        # Strategy 3: Try DOI.org resolution with PDF hints
        try:
            doi_resolution_url = f"https://doi.org/{doi}"
            # Some publishers redirect to PDF when Accept header is set to application/pdf
            alternatives.append(doi_resolution_url)
        except Exception:
            pass

        return alternatives

    def _get_publisher_pdf_patterns(self, doi: str) -> list[str]:
        """Get publisher-specific PDF URL patterns based on DOI"""
        patterns = []

        # Common publisher PDF URL patterns
        publisher_patterns = {
            "10.1371": "https://journals.plos.org/plosone/article/file?id={}&type=printable",  # PLOS
            "10.1038": "https://www.nature.com/articles/{}.pdf",  # Nature
            "10.1126": "https://www.science.org/doi/pdf/{}",  # Science
            "10.1016": "https://www.sciencedirect.com/science/article/pii/{}/pdfft",  # Elsevier
            "10.1186": "https://link.springer.com/content/pdf/{}.pdf",  # BMC/Springer
            "10.1080": "https://www.tandfonline.com/doi/pdf/{}",  # Taylor & Francis
            "10.1177": "https://journals.sagepub.com/doi/pdf/{}",  # SAGE
        }

        for prefix, pattern in publisher_patterns.items():
            if doi.startswith(prefix):
                try:
                    formatted_url = pattern.format(doi)
                    patterns.append(formatted_url)
                except Exception:
                    continue

        return patterns

    async def enhance_pdf_availability(self, paper_data: dict) -> dict:
        """
        Enhance paper data with validated PDF URLs and alternatives

        Args:
            paper_data: Paper metadata dictionary

        Returns:
            Enhanced paper data with validated PDF information
        """
        enhanced_data = paper_data.copy()

        # Get current PDF URLs
        current_pdf_urls = []
        for field in ["pdf_url", "open_access_pdf"]:
            url = paper_data.get(field)
            if url:
                fixed_url = self.fix_common_pdf_url_issues(url)
                current_pdf_urls.append(fixed_url)

        # Find alternative URLs
        alternative_urls = await self.find_alternative_pdf_urls(paper_data)

        # Combine and validate all URLs
        all_urls = current_pdf_urls + alternative_urls
        validated_urls = []

        # Validate URLs in parallel (but limit concurrency)
        validation_tasks = [
            self.validate_pdf_url(url) for url in all_urls[:5]
        ]  # Limit to 5 URLs
        if validation_tasks:
            validation_results = await asyncio.gather(
                *validation_tasks, return_exceptions=True
            )

            for i, result in enumerate(validation_results):
                if isinstance(result, tuple) and result[0]:  # is_valid=True
                    validated_urls.append(all_urls[i])

        # Update paper data with best PDF URLs
        if validated_urls:
            enhanced_data["pdf_url"] = validated_urls[0]  # Primary PDF URL
            if len(validated_urls) > 1:
                enhanced_data["open_access_pdf"] = validated_urls[
                    1
                ]  # Alternative PDF URL
                enhanced_data["alternative_pdf_urls"] = validated_urls[
                    2:
                ]  # Additional alternatives

        # Add PDF availability metadata
        enhanced_data["pdf_validated"] = len(validated_urls) > 0
        enhanced_data["pdf_availability_score"] = min(
            1.0, len(validated_urls) / 2.0
        )  # Score 0-1

        return enhanced_data

    def get_validation_stats(self) -> dict[str, int | float]:
        """Get PDF validation statistics"""
        total_checked = len(self._validation_cache)
        valid_count = sum(1 for is_valid in self._validation_cache.values() if is_valid)

        return {
            "total_urls_checked": total_checked,
            "valid_urls": valid_count,
            "invalid_urls": total_checked - valid_count,
            "success_rate": (
                round(valid_count / total_checked * 100, 1)
                if total_checked > 0
                else 0.0
            ),
        }

    def clear_cache(self) -> None:
        """Clear the validation cache"""
        self._validation_cache.clear()


# Global instance for easy access
pdf_validator = PDFValidator()
