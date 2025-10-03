"""
Metadata Normalizer Utility

Standardizes metadata across different academic sources to ensure consistent format and quality.
Addresses Issue 4.2: Incomplete Metadata Across Sources from COMPREHENSIVE_ISSUE_RESOLUTION.md
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class MetadataNormalizer:
    """Standardizes and normalizes metadata from academic sources"""

    def __init__(self) -> None:
        # Common academic title prefixes to handle
        self.title_prefixes = [
            "a ",
            "an ",
            "the ",
            "on ",
            "in ",
            "of ",
            "for ",
            "with ",
            "from ",
            "about ",
            "towards ",
            "toward ",
            "into ",
            "through ",
            "during ",
        ]

        # Common date patterns
        self.date_patterns = [
            r"(\d{4})-\d{2}-\d{2}",  # YYYY-MM-DD
            r"(\d{4})/\d{2}/\d{2}",  # YYYY/MM/DD
            r"(\d{4})-\d{2}",  # YYYY-MM
            r"(\d{4})/\d{2}",  # YYYY/MM
            r"(\d{4})",  # YYYY only
        ]

    def normalize_authors(self, authors: list | str | dict | None) -> list[str]:
        """
        Normalize author information to consistent string list format

        Args:
            authors: Authors in various formats (list, dict, string, None)

        Returns:
            List of normalized author names as strings
        """
        if not authors:
            return []

        # Handle PubMed dict format: [{'lastname': 'Smith', 'firstname': 'John', ...}]
        if (
            isinstance(authors, list)
            and len(authors) > 0
            and isinstance(authors[0], dict)
        ):
            normalized = []
            for author_dict in authors:
                if isinstance(author_dict, dict):
                    # Extract name parts
                    lastname = author_dict.get("lastname", "")
                    firstname = author_dict.get("firstname", "")
                    initials = author_dict.get("initials", "")

                    # Build full name
                    if firstname and lastname:
                        name = f"{firstname} {lastname}"
                    elif initials and lastname:
                        name = f"{initials} {lastname}"
                    elif lastname:
                        name = lastname
                    else:
                        # Fallback to string representation
                        name = str(author_dict)

                    normalized.append(name.strip())
                else:
                    normalized.append(str(author_dict))
            return normalized

        # Handle string format
        elif isinstance(authors, str):
            # Split by common separators
            if "," in authors:
                return [
                    author.strip() for author in authors.split(",") if author.strip()
                ]
            elif ";" in authors:
                return [
                    author.strip() for author in authors.split(";") if author.strip()
                ]
            else:
                return [authors.strip()]

        # Handle list of strings
        elif isinstance(authors, list):
            return [str(author).strip() for author in authors if author]

        # Fallback
        else:
            return [str(authors)]

    def normalize_date(self, date_value: str | int | None) -> int | None:
        """
        Normalize publication date to YYYY integer format

        Args:
            date_value: Date in various formats

        Returns:
            Year as integer or None if unparseable
        """
        if not date_value:
            return None

        date_str = str(date_value).strip()

        # Try each date pattern
        for pattern in self.date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    year = int(match.group(1))
                    # Validate year is reasonable (1900-2030)
                    if 1900 <= year <= 2030:
                        return year
                except (ValueError, IndexError):
                    continue

        # Direct integer conversion as fallback
        try:
            year = int(float(date_str))
            if 1900 <= year <= 2030:
                return year
        except (ValueError, TypeError):
            pass

        logger.warning(f"Could not parse date: {date_value}")
        return None

    def normalize_title(self, title: str) -> str:
        """
        Normalize title formatting

        Args:
            title: Raw title string

        Returns:
            Cleaned and normalized title
        """
        if not title:
            return ""

        # Clean up whitespace
        title = " ".join(title.split())

        # Remove trailing periods
        title = title.rstrip(".")

        # Capitalize first letter if not already
        if title and title[0].islower():
            title = title[0].upper() + title[1:]

        return title

    def normalize_abstract(self, abstract: str, max_length: int = 2000) -> str:
        """
        Normalize abstract text

        Args:
            abstract: Raw abstract text
            max_length: Maximum length to truncate to

        Returns:
            Cleaned abstract text
        """
        if not abstract:
            return ""

        # Clean up whitespace
        abstract = " ".join(abstract.split())

        # Truncate if too long
        if len(abstract) > max_length:
            # Try to truncate at sentence boundary
            sentences = abstract.split(".")
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ".") <= max_length:
                    truncated += sentence + "."
                else:
                    break

            if len(truncated) > 50:  # Keep if we got at least one sentence
                abstract = truncated
            else:
                abstract = abstract[:max_length] + "..."

        return abstract.strip()

    def normalize_url(self, url: str | None, source: str | None = None) -> str | None:
        """
        Normalize and convert relative URLs to absolute URLs based on source.

        This function handles source-specific URL formatting to ensure all URLs
        are absolute and properly formatted.

        Args:
            url: URL to normalize (can be relative or absolute)
            source: Source name for determining base URL

        Returns:
            Absolute URL or None if URL is invalid
        """
        if not url:
            return None

        # Already absolute
        if url.startswith("http://") or url.startswith("https://"):
            return url

        # Source-specific URL construction
        source_lower = source.lower() if source else ""

        # Define base URLs for each source
        source_base_urls: dict[str, str] = {
            "pubmed": "https://pubmed.ncbi.nlm.nih.gov",
            "pubmed_central": "https://www.ncbi.nlm.nih.gov/pmc",
            "europe_pmc": "https://europepmc.org/article/MED",
            "arxiv": "https://arxiv.org",
            "crossref": "https://doi.org",
            "openalex": "https://openalex.org",
            "semantic_scholar": "https://www.semanticscholar.org/paper",
            "openlibrary": "https://openlibrary.org",
            "doaj": "https://doaj.org/article",
            "core": "https://core.ac.uk/display",
            "biorxiv": "https://www.biorxiv.org/content",
            "medrxiv": "https://www.medrxiv.org/content",
            "chemrxiv": "https://chemrxiv.org/engage/chemrxiv/article-details",
            "ssrn": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=",
            "clinicaltrials": "https://clinicaltrials.gov/study",
            "eric": "https://eric.ed.gov/",
        }

        # ERIC uses special ?id= query parameter format
        if source_lower == "eric":
            eric_id = url[1:] if url.startswith("/") else url
            return f"https://eric.ed.gov/?id={eric_id}"

        # SSRN uses abstract_id parameter
        if source_lower == "ssrn":
            ssrn_id = re.sub(r"[^0-9]", "", url)  # Extract ID only
            return f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_id}"

        # Get base URL for source
        base_url = source_base_urls.get(source_lower)
        if base_url:
            # Add leading slash if not present
            if not url.startswith("/"):
                url = "/" + url
            return f"{base_url}{url}"

        # If we don't know the source, return None to avoid creating invalid URLs
        logger.debug(
            f"Cannot normalize relative URL without known source: {url} from {source}"
        )
        return None

    def calculate_completeness_score(self, paper_data: dict[str, Any]) -> float:
        """
        Calculate metadata completeness score (0.0 to 1.0)

        Args:
            paper_data: Paper metadata dictionary

        Returns:
            Completeness score between 0.0 and 1.0
        """
        # Define field weights (total = 1.0)
        field_weights = {
            "title": 0.25,  # Most important
            "authors": 0.20,  # Very important
            "abstract": 0.20,  # Very important
            "year": 0.15,  # Important for sorting/filtering
            "journal": 0.10,  # Helpful context
            "doi": 0.05,  # Nice to have
            "pdf_url": 0.05,  # Nice to have
        }

        score = 0.0

        for field, weight in field_weights.items():
            value = paper_data.get(field)

            if field == "title":
                if value and len(str(value).strip()) > 10:
                    score += weight
            elif field == "authors":
                if value and len(self.normalize_authors(value)) > 0:
                    score += weight
            elif field == "abstract":
                if value and len(str(value).strip()) > 50:
                    score += weight
            elif field == "year":
                if value and self.normalize_date(value) is not None:
                    score += weight
            else:
                # For other fields, just check if they exist and are non-empty
                if value and str(value).strip():
                    score += weight

        return min(1.0, score)  # Cap at 1.0

    def normalize_paper_metadata(self, paper_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize all metadata fields for a paper

        Args:
            paper_data: Raw paper metadata

        Returns:
            Normalized paper metadata with completeness score
        """
        normalized: dict[str, Any] = {}

        # Normalize each field
        normalized["title"] = self.normalize_title(paper_data.get("title", ""))
        normalized["authors"] = self.normalize_authors(paper_data.get("authors"))
        normalized["abstract"] = self.normalize_abstract(paper_data.get("abstract", ""))
        normalized["year"] = self.normalize_date(paper_data.get("year"))

        # Get source for URL normalization
        source = paper_data.get("source", "")
        normalized["source"] = source.strip() if isinstance(source, str) else source

        # Normalize URLs to ensure they're absolute
        normalized["url"] = self.normalize_url(paper_data.get("url"), source)
        normalized["pdf_url"] = self.normalize_url(paper_data.get("pdf_url"), source)
        normalized["open_access_pdf"] = self.normalize_url(
            paper_data.get("open_access_pdf"), source
        )

        # Pass through other fields as-is but clean strings
        for field in [
            "journal",
            "doi",
            "citation_count",
        ]:
            value = paper_data.get(field)
            if isinstance(value, str):
                normalized[field] = value.strip() if value else ""
            else:
                normalized[field] = value

        # Add any source-specific fields
        for field, value in paper_data.items():
            if field not in normalized:
                normalized[field] = value

        # Calculate and add completeness score
        normalized["metadata_completeness"] = self.calculate_completeness_score(
            normalized
        )

        return normalized


# Global instance for easy access
metadata_normalizer = MetadataNormalizer()
