"""
PubMed and PubMed Central API client for biomedical literature search.
Enhanced with PMC full-text access and improved medical research capabilities.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp
from pymed import PubMed
from tenacity import retry, stop_after_attempt, wait_exponential

# api_status and config are now managed by the configuration system
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class PubMedClient(BaseAPIClient):
    """PubMed API client with enhanced PDF validation and metadata normalization"""

    def __init__(self) -> None:
        super().__init__("PubMed", cache_expire=3600)  # 1 hour cache

    async def _perform_search(
        self, query: str, limit: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Perform PubMed search with PMC enhancement"""
        return await _search_pubmed_internal(query, limit)


class PubMedCentralClient(BaseAPIClient):
    """PubMed Central API client with enhanced PDF validation and metadata normalization"""

    def __init__(self) -> None:
        super().__init__("PubMed Central", cache_expire=3600)  # 1 hour cache

    async def _perform_search(
        self, query: str, limit: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Perform PMC search with full-text access"""
        return await _search_pmc_internal(query, limit)


def _parse_pmc_xml(xml_content: str) -> list[dict[str, Any]]:
    """Parse PMC XML response to extract article metadata"""
    results = []

    try:
        root = ET.fromstring(xml_content)

        # PMC XML structure: pmc-articleset > article
        for article in root.findall(".//article"):
            try:
                # Extract article metadata
                front = article.find(".//front")
                if front is None:
                    continue

                article_meta = front.find(".//article-meta")
                if article_meta is None:
                    continue

                # Extract title
                title_group = article_meta.find(".//title-group")
                title = ""
                if title_group is not None:
                    article_title = title_group.find("article-title")
                    if article_title is not None:
                        title = "".join(article_title.itertext()).strip()

                # Extract authors
                authors = []
                contrib_group = article_meta.find(".//contrib-group")
                if contrib_group is not None:
                    for contrib in contrib_group.findall(
                        './/contrib[@contrib-type="author"]'
                    ):
                        name = contrib.find(".//name")
                        if name is not None:
                            surname = name.find("surname")
                            given_names = name.find("given-names")
                            if surname is not None:
                                author_name = surname.text or ""
                                if given_names is not None and given_names.text:
                                    author_name = f"{given_names.text} {author_name}"
                                authors.append(author_name.strip())

                # Extract abstract
                abstract = ""
                abstract_elem = article_meta.find(".//abstract")
                if abstract_elem is not None:
                    abstract = "".join(abstract_elem.itertext()).strip()

                # Extract journal
                journal = ""
                journal_meta = front.find(".//journal-meta")
                if journal_meta is not None:
                    journal_title = journal_meta.find(".//journal-title")
                    if journal_title is not None:
                        journal = journal_title.text or ""

                # Extract publication date/year
                year = None
                pub_date = (
                    article_meta.find('.//pub-date[@pub-type="epub"]')
                    or article_meta.find('.//pub-date[@pub-type="ppub"]')
                    or article_meta.find(".//pub-date")
                )
                if pub_date is not None:
                    year_elem = pub_date.find("year")
                    if year_elem is not None and year_elem.text:
                        try:
                            year = int(year_elem.text)
                        except ValueError:
                            pass

                # Extract DOI
                doi = None
                article_ids = article_meta.findall(".//article-id")
                for article_id in article_ids:
                    if article_id.get("pub-id-type") == "doi":
                        doi = article_id.text
                        break

                # Extract PMC ID
                pmc_id = None
                for article_id in article_ids:
                    if article_id.get("pub-id-type") == "pmcid":
                        pmc_id = article_id.text  # Already includes PMC prefix
                        break

                if title:  # Only include if we have a real title
                    result = {
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "journal": journal,
                        "year": year,
                        "pmc_id": pmc_id,
                        "doi": doi,
                        "source": "PubMed Central",
                        "url": (
                            f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
                            if pmc_id
                            else ""
                        ),
                        "pdf_url": (
                            f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
                            if pmc_id
                            else None
                        ),
                        "open_access_pdf": (
                            f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
                            if pmc_id
                            else None
                        ),
                        "full_text_url": (
                            f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
                            if pmc_id
                            else ""
                        ),
                        "citation_count": 0,  # PMC doesn't provide citation counts directly
                    }
                    results.append(result)

            except Exception as e:
                logger.warning(f"Error parsing individual PMC article: {e}")
                continue

    except Exception as e:
        logger.warning(f"Error parsing PMC XML: {e}")

    return results


async def _check_pmc_availability(pmid: str) -> dict[str, str]:
    """Check if a PubMed article is available in PMC with full text"""
    if not pmid:
        return {}

    try:
        # Use NCBI elink to find PMC ID
        elink_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(elink_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    linksets = data.get("linksets", [])

                    for linkset in linksets:
                        linksetdbs = linkset.get("linksetdbs", [])
                        for linksetdb in linksetdbs:
                            if linksetdb.get("dbto") == "pmc":
                                pmc_ids = linksetdb.get("links", [])
                                if pmc_ids:
                                    pmc_id = pmc_ids[0]
                                    # Generate standardized PMC PDF URL
                                    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
                                    return {
                                        "pmc_id": f"PMC{pmc_id}",
                                        "pdf_url": pdf_url,
                                        "full_text_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/",
                                        "open_access_pdf": pdf_url,  # PMC PDFs are open access
                                    }
    except Exception as e:
        logger.debug(f"PMC availability check failed for PMID {pmid}: {e}")

    return {}


async def _search_pubmed_internal(query: str, limit: int) -> list[dict[str, Any]]:
    """Internal PubMed search function"""

    def _search_pubmed() -> list[dict[str, Any]]:
        pubmed = PubMed(tool="paperez-mcp", email="research@example.com")
        results = []

        for article in pubmed.query(query, max_results=limit):
            result = {
                "title": article.title,
                "authors": [str(author) for author in (article.authors or [])],
                "abstract": article.abstract,
                "journal": getattr(article, "journal", None),
                "year": (
                    article.publication_date.year
                    if article.publication_date
                    and hasattr(article.publication_date, "year")
                    else None
                ),
                "pubmed_id": article.pubmed_id,
                "doi": article.doi,
                "source": "PubMed",
                "url": (
                    f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/"
                    if article.pubmed_id
                    else ""
                ),
                "citation_count": 0,  # PubMed doesn't provide citation counts
            }
            results.append(result)
        return results

    results = await asyncio.to_thread(_search_pubmed)

    # Enhance results with PMC availability for better PDF access
    enhanced_results = []
    for result in results:
        if result.get("pubmed_id"):
            pmc_info = await _check_pmc_availability(result["pubmed_id"])
            if pmc_info:
                result.update(pmc_info)
                result["open_access_pdf"] = pmc_info.get("pdf_url")
                logger.debug(f"PMC available for {result['title'][:50]}...")
        enhanced_results.append(result)

    return enhanced_results


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_pubmed(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search PubMed for biomedical literature with enhanced PDF validation"""
    client = PubMedClient()

    try:
        # Get search results
        results = await _search_pubmed_internal(query, limit)

        # Enhance results with PDF validation and metadata normalization
        enhanced_results = []
        for result in results:
            # Apply base client standardization (includes metadata normalization)
            standardized = client._standardize_paper(result)

            # Enhance with PDF validation (async operation)
            enhanced = await client._enhance_pdf_availability(standardized)
            enhanced_results.append(enhanced)

        pmc_count = sum(1 for r in enhanced_results if r.get("pmc_id"))
        logger.info(
            f"✅ PubMed: Found {len(enhanced_results)} results ({pmc_count} with PMC full-text) for '{query}'"
        )
        return enhanced_results

    except Exception as e:
        logger.warning(f"❌ PubMed search failed: {e}")
        # api_status is now managed by config system
        return []


async def _search_pmc_internal(query: str, limit: int) -> list[dict[str, Any]]:
    """Internal PMC search function"""
    try:
        # Use NCBI E-utilities to search PMC directly
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pmc",
            "term": query,
            "retmax": str(limit),
            "retmode": "json",
            "sort": "relevance",
        }

        async with aiohttp.ClientSession() as session:
            # Search for PMC articles
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    logger.warning(f"PMC search failed with status {response.status}")
                    return []

                search_data = await response.json()
                pmc_ids = search_data.get("esearchresult", {}).get("idlist", [])

                if not pmc_ids:
                    logger.info(f"No PMC results found for '{query}'")
                    return []

                # Fetch detailed information for found articles
                fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                fetch_params = {"db": "pmc", "id": ",".join(pmc_ids), "retmode": "xml"}

                async with session.get(
                    fetch_url, params=fetch_params
                ) as fetch_response:
                    if fetch_response.status != 200:
                        logger.warning(
                            f"PMC fetch failed with status {fetch_response.status}"
                        )
                        return []

                    # Parse XML response to extract real article metadata
                    xml_content = await fetch_response.text()
                    results = _parse_pmc_xml(xml_content)

                    logger.info(
                        f"✅ PMC: Found {len(results)} full-text articles for {query}"
                    )
                    return results

    except Exception as e:
        logger.warning(f"❌ PMC search failed: {e}")
        return []


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_pubmed_central(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search PubMed Central for open access full-text articles with enhanced PDF validation"""
    client = PubMedCentralClient()

    try:
        # Get search results
        results = await _search_pmc_internal(query, limit)

        # Enhance results with PDF validation and metadata normalization
        enhanced_results = []
        for result in results:
            # Apply base client standardization (includes metadata normalization)
            standardized = client._standardize_paper(result)

            # Enhance with PDF validation (async operation)
            enhanced = await client._enhance_pdf_availability(standardized)
            enhanced_results.append(enhanced)

        logger.info(
            f"✅ PMC: Found {len(enhanced_results)} enhanced results for '{query}'"
        )
        return enhanced_results

    except Exception as e:
        logger.warning(f"❌ PMC search failed: {e}")
        return []
