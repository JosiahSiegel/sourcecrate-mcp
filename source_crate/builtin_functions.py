"""
Builtin search functions for sources that require specialized libraries.

These minimal functions are only for sources that cannot be handled by the
generic HTTP client (e.g., they require special Python libraries).

All configuration and behavior should still be driven by YAML files.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any

logger = logging.getLogger(__name__)


async def search_arxiv(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search arXiv using the arxiv Python library.

    This is a minimal wrapper - all configuration like URL transformation
    and rate limiting is handled by the download layer via YAML config.
    """
    try:
        import arxiv  # type: ignore[import-untyped]

        def _search() -> list[dict[str, Any]]:
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            results = []
            for paper in search.results():
                result = {
                    "title": paper.title,
                    "authors": [str(author) for author in paper.authors],
                    "abstract": paper.summary,
                    "year": paper.published.year if paper.published else None,
                    "arxiv_id": paper.entry_id.split("/")[-1],
                    "pdf_url": paper.pdf_url,  # URL transformation happens at download time
                    "source": "arXiv",
                    "categories": paper.categories,
                    "url": paper.entry_id,
                }
                results.append(result)
            return results

        return await asyncio.to_thread(_search)

    except Exception as e:
        logger.error(f"arXiv search failed: {e}")
        return []


async def search_pubmed(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search PubMed using the pymed library.

    Minimal wrapper - configuration is handled via YAML.
    """
    try:
        from pymed import PubMed  # type: ignore[import-untyped]

        def _search() -> list[dict[str, Any]]:
            pubmed = PubMed(tool="sourcecrate-mcp", email="research@example.com")
            results = []

            for article in pubmed.query(query, max_results=limit):
                # Format authors properly from pymed objects
                authors = []
                if article.authors:
                    for author in article.authors:
                        if isinstance(author, dict):
                            # Extract firstname and lastname from dict
                            firstname = author.get("firstname", "")
                            lastname = author.get("lastname", "")
                            if firstname and lastname:
                                authors.append(f"{firstname} {lastname}")
                            elif lastname:
                                authors.append(lastname)
                            elif firstname:
                                authors.append(firstname)
                        elif hasattr(author, "firstname") and hasattr(
                            author, "lastname"
                        ):
                            # Extract from object attributes
                            firstname = getattr(author, "firstname", "")
                            lastname = getattr(author, "lastname", "")
                            if firstname and lastname:
                                authors.append(f"{firstname} {lastname}")
                            elif lastname:
                                authors.append(lastname)
                            elif firstname:
                                authors.append(firstname)
                        else:
                            # Fallback to string representation
                            authors.append(str(author))

                result = {
                    "title": article.title,
                    "authors": authors,
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
                }
                results.append(result)
            return results

        return await asyncio.to_thread(_search)

    except Exception as e:
        logger.error(f"PubMed search failed: {e}")
        return []


async def search_pubmed_central(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search PubMed Central for full-text articles.

    Uses NCBI E-utilities API. Could potentially be converted to
    generic HTTP client with proper YAML configuration.
    """
    try:

        import aiohttp

        # Search for PMC articles
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pmc",
            "term": query,
            "retmax": str(limit),
            "retmode": "json",
            "sort": "relevance",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    return []

                search_data = await response.json()
                pmc_ids = search_data.get("esearchresult", {}).get("idlist", [])

                if not pmc_ids:
                    return []

                # Fetch article details
                fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                fetch_params = {"db": "pmc", "id": ",".join(pmc_ids), "retmode": "xml"}

                async with session.get(
                    fetch_url, params=fetch_params
                ) as fetch_response:
                    if fetch_response.status != 200:
                        return []

                    xml_content = await fetch_response.text()
                    return _parse_pmc_xml(xml_content)

    except Exception as e:
        logger.error(f"PMC search failed: {e}")
        return []


def _parse_pmc_xml(xml_content: str) -> list[dict[str, Any]]:
    """Parse PMC XML response - simplified version."""
    results = []

    try:
        root = ET.fromstring(xml_content)

        for article in root.findall(".//article"):
            try:
                # Basic metadata extraction
                title = ""
                title_elem = article.find(".//article-title")
                if title_elem is not None:
                    title = "".join(title_elem.itertext()).strip()

                if not title:
                    continue

                # Extract PMC ID
                pmc_id = None
                for article_id in article.findall(".//article-id"):
                    if article_id.get("pub-id-type") == "pmcid":
                        pmc_id = article_id.text
                        break

                result: dict[str, Any] = {
                    "title": title,
                    "authors": [],  # Simplified - could be expanded
                    "abstract": "",  # Simplified - could be expanded
                    "pmc_id": pmc_id,
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
                }
                results.append(result)

            except Exception:
                continue

    except Exception as e:
        logger.error(f"PMC XML parsing failed: {e}")

    return results


# Export all builtin functions
__all__ = [
    "search_arxiv",
    "search_pubmed",
    "search_pubmed_central",
]
