"""
Generic HTTP API client for config-based sources.

This allows users to add new academic sources just by providing configuration,
without needing to write any Python code.
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class GenericHTTPClient(BaseAPIClient):
    """
    Generic HTTP API client that works with any REST API via configuration.

    Users can add new sources by just providing config like:
    {
        "base_url": "https://api.example.com",
        "search_path": "/search",
        "query_param": "q",
        "limit_param": "max_results",
        "response_format": "json",
        "results_path": "data.results",
        "field_mappings": {
            "title": "title",
            "authors": "authors",
            "abstract": "description",
            "year": "publication_year",
            "doi": "doi",
            "url": "url"
        }
    }
    """

    def __init__(self, source_name: str, **config: Any) -> None:
        """
        Initialize generic HTTP client.

        Args:
            source_name: Name of the source
            **config: Source configuration
        """
        super().__init__(source_name, cache_expire=config.get("cache_expire", 3600))

        # Required configuration
        self.base_url = config.get("base_url")
        if not self.base_url:
            raise ValueError(f"base_url is required for {source_name}")

        # API endpoint configuration
        self.search_path = config.get("search_path", "/search")
        self.query_param = config.get("query_param", "q")
        self.limit_param = config.get("limit_param", "limit")

        # Authentication
        self.api_key = config.get("api_key")
        self.auth_header = config.get("auth_header", "Authorization")
        self.auth_type = config.get("auth_type", "Bearer")  # Bearer, Basic, ApiKey

        # Request configuration
        self.timeout = config.get("timeout", 30)
        self.headers = config.get("headers", {})
        self.extra_params = self._expand_env_vars(config.get("extra_params", {}))

        # Response parsing
        self.response_format = config.get("response_format", "json")
        self.results_path = config.get(
            "results_path", "results"
        )  # e.g., "data.results"
        self.total_path = config.get("total_path", "total")

        # Field mappings from API response to standard format
        self.field_mappings = config.get(
            "field_mappings",
            {
                "title": "title",
                "authors": "authors",
                "abstract": "abstract",
                "journal": "journal",
                "year": "year",
                "doi": "doi",
                "url": "url",
                "pdf_url": "pdf_url",
                "citation_count": "citation_count",
            },
        )

        # Rate limiting
        self.rate_limit_delay = config.get("rate_limit_delay", 0.1)

    def _expand_env_vars(self, params: dict[str, Any]) -> dict[str, Any]:
        """Expand environment variables in config parameters.

        Supports ${VAR_NAME} or $VAR_NAME syntax.
        Falls back to original value if env var not found.
        """
        import re

        expanded = {}
        for key, value in params.items():
            if isinstance(value, str):
                # Pattern matches ${VAR} or $VAR
                pattern = r'\$\{([A-Z_]+)\}|\$([A-Z_]+)'

                def replacer(match: re.Match[str]) -> str:
                    var_name = match.group(1) or match.group(2)
                    env_value = os.getenv(var_name)
                    if env_value:
                        logger.debug(
                            f"Expanded ${{{var_name}}} to environment value for {key}"
                        )
                        return env_value
                    # Keep original if env var not found
                    logger.debug(
                        f"Environment variable {var_name} not found, keeping original value"
                    )
                    return match.group(0)

                expanded[key] = re.sub(pattern, replacer, value)
            else:
                expanded[key] = value
        return expanded

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation path."""
        try:
            keys = path.split(".")
            value = data
            for key in keys:
                if isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                elif isinstance(value, dict):
                    value = value.get(key)  # type: ignore[assignment]
                else:
                    return None
            return value
        except (KeyError, IndexError, AttributeError):
            return None

    def _build_headers(self) -> dict[str, str]:
        """Build request headers including authentication."""
        headers = self.headers.copy()
        headers["User-Agent"] = "PaperezMCP Academic Research Tool"

        if self.api_key:
            if self.auth_type == "Bearer":
                headers[self.auth_header] = f"Bearer {self.api_key}"
            elif self.auth_type == "ApiKey":
                headers[self.auth_header] = self.api_key
            elif self.auth_type == "Basic":
                import base64

                encoded = base64.b64encode(f"{self.api_key}:".encode()).decode()
                headers[self.auth_header] = f"Basic {encoded}"

        return headers  # type: ignore[no-any-return]

    def _build_params(self, query: str, limit: int, **kwargs: Any) -> dict[str, Any]:
        """Build query parameters."""
        params = self.extra_params.copy()

        # Handle CrossRef-style query formatting
        formatted_query = query
        if self.source_name == "crossref":
            # Wrap multi-word queries in quotes for better phrase search
            if " " in query.strip() and not (
                query.strip().startswith('"') and query.strip().endswith('"')
            ):
                formatted_query = f'"{query}"'

        params[self.query_param] = formatted_query
        params[self.limit_param] = limit

        # Add any additional parameters from kwargs
        for key, value in kwargs.items():
            if key not in ["force_category"]:  # Skip internal parameters
                params[key] = value

        return params  # type: ignore[no-any-return]

    def _parse_authors(self, authors_data: Any) -> list[str]:
        """Parse authors from various formats."""
        if not authors_data:
            return []

        if isinstance(authors_data, str):
            # Handle comma-separated string
            return [
                author.strip() for author in authors_data.split(",") if author.strip()
            ]
        elif isinstance(authors_data, list):
            # Handle list of author objects or strings
            result = []
            for author in authors_data:
                if isinstance(author, str):
                    result.append(author.strip())
                elif isinstance(author, dict):
                    # Try common author field names
                    name = None

                    # CrossRef format: {"given": "John", "family": "Smith"}
                    if "given" in author and "family" in author:
                        name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    # Semantic Scholar format: {"name": "John Smith"}
                    elif "name" in author:
                        name = author.get("name", "").strip()
                    # PubMed format: {"firstname": "John", "lastname": "Smith"}
                    elif "firstname" in author and "lastname" in author:
                        name = f"{author.get('firstname', '')} {author.get('lastname', '')}".strip()
                    # Other common formats with underscores
                    elif "first_name" in author and "last_name" in author:
                        name = f"{author.get('first_name', '')} {author.get('last_name', '')}".strip()
                    # Single field formats
                    else:
                        name = (
                            author.get("full_name") or author.get("display_name") or ""
                        )

                    if name:
                        result.append(name)
            return result
        else:
            return [str(authors_data)]

    def _resolve_field_value(
        self, item: dict[str, Any], paper: dict[str, Any], field_config: Any
    ) -> Any:
        """
        Resolve field value supporting both simple paths and advanced configurations.

        Supports YAML configurations like:
        ```yaml
        field_mappings:
          url:
            alternatives:
              - path: fullTextUrlList.fullTextUrl
                filter_by: {field: site, values: ["Europe_PMC"]}
                extract: url
              - path: fullTextUrlList.fullTextUrl.0.url
              - template: "https://example.com/{pmcid}"
        ```

        Args:
            item: Raw API response item
            paper: Partially constructed paper dict (for template substitution)
            field_config: String path or dict with alternatives

        Returns:
            Resolved field value or None
        """
        # Simple case: String path (backward compatible)
        if isinstance(field_config, str):
            return self._get_nested_value(item, field_config)

        # Advanced case: Dict with alternatives
        if isinstance(field_config, dict) and "alternatives" in field_config:
            alternatives = field_config["alternatives"]
            if not isinstance(alternatives, list):
                alternatives = [alternatives]

            for alt in alternatives:
                if isinstance(alt, str):
                    # Simple path alternative
                    value = self._get_nested_value(item, alt)
                    if value:
                        return value

                elif isinstance(alt, dict):
                    # Advanced alternative with filtering/template

                    # Template-based construction
                    if "template" in alt:
                        template = alt["template"]
                        try:
                            # Replace {field} placeholders with values from paper dict
                            result = template
                            for key, val in paper.items():
                                if val and f"{{{key}}}" in template:
                                    result = result.replace(f"{{{key}}}", str(val))
                            # Also try from item dict
                            for key in ["pmcid", "doi", "pmid"]:
                                val = self._get_nested_value(item, key)
                                if val and f"{{{key}}}" in result:
                                    result = result.replace(f"{{{key}}}", str(val))
                            # Check if all placeholders were replaced
                            if "{" not in result:
                                return result
                        except Exception:
                            pass

                    # Path with filtering
                    elif "path" in alt:
                        value = self._get_nested_value(item, alt["path"])

                        # Apply filtering if specified
                        if value and "filter_by" in alt:
                            filter_config = alt["filter_by"]
                            filter_field = filter_config.get("field")
                            filter_values = filter_config.get("values", [])

                            if isinstance(value, list) and filter_field:
                                # Find first item matching filter
                                for item_in_list in value:
                                    if isinstance(item_in_list, dict):
                                        item_value = item_in_list.get(filter_field)
                                        if item_value in filter_values:
                                            # Extract specified field
                                            extract_field = alt.get("extract")
                                            if extract_field:
                                                return item_in_list.get(extract_field)
                                            return item_in_list
                            # Filtering failed - continue to next alternative
                            # (don't return unfiltered value)

                        # Return value as-is only if NO filtering was specified
                        elif value:
                            extract_field = alt.get("extract")
                            if extract_field and isinstance(value, dict):
                                return value.get(extract_field)
                            return value

        return None

    def _standardize_paper(self, item: dict[str, Any]) -> dict[str, Any]:
        """Convert API response item to standard paper format."""
        paper: dict[str, Any] = {}

        for standard_field, api_field in self.field_mappings.items():
            if api_field:
                # Use enhanced field resolver (supports both simple and advanced configs)
                value = self._resolve_field_value(item, paper, api_field)

                if standard_field == "authors":
                    paper[standard_field] = self._parse_authors(value)
                elif standard_field == "year" and value:
                    # Try to extract year from various date formats
                    try:
                        if isinstance(value, str):
                            # Extract first 4-digit number (likely year)
                            import re

                            year_match = re.search(r"\b(19|20)\d{2}\b", value)
                            paper[standard_field] = (
                                int(year_match.group()) if year_match else None
                            )
                        else:
                            paper[standard_field] = int(value)
                    except (ValueError, TypeError):
                        paper[standard_field] = None
                elif standard_field == "citation_count" and value:
                    try:
                        paper[standard_field] = int(value)
                    except (ValueError, TypeError):
                        paper[standard_field] = 0
                elif standard_field == "abstract":
                    # Handle special abstract formats
                    if isinstance(value, dict) and self.source_name == "openalex":
                        # OpenAlex abstract_inverted_index - convert back to text
                        if value:
                            # Reconstruct text from inverted index
                            word_positions = []
                            for word, positions in value.items():
                                for pos in positions:
                                    word_positions.append((pos, word))
                            word_positions.sort()
                            paper[standard_field] = " ".join(
                                word for _, word in word_positions
                            )
                        else:
                            paper[standard_field] = ""
                    elif isinstance(value, (dict, list)):
                        # Convert non-string abstract data to empty string
                        paper[standard_field] = ""
                    else:
                        paper[standard_field] = str(value) if value else ""
                elif standard_field == "title":
                    # Ensure title is always a string
                    if isinstance(value, (dict, list)):
                        # Try to extract title from complex data structures
                        if isinstance(value, list) and value:
                            paper[standard_field] = str(value[0]) if value[0] else ""
                        elif isinstance(value, dict):
                            # Try common title field names
                            paper[standard_field] = str(
                                value.get(
                                    "title",
                                    value.get("name", value.get("display_name", "")),
                                )
                            )
                        else:
                            paper[standard_field] = ""
                    else:
                        paper[standard_field] = str(value) if value else ""
                elif standard_field == "url":
                    # Source-specific URL handling
                    if self.source_name == "crossref":
                        # CrossRef: Generate DOI URL if no direct URL provided
                        if not value and paper.get("doi"):
                            paper[standard_field] = f"https://doi.org/{paper['doi']}"
                        else:
                            paper[standard_field] = value or ""
                    elif self.source_name == "openlibrary":
                        # OpenLibrary: Convert relative paths to absolute URLs
                        if value and isinstance(value, str) and value.startswith("/"):
                            paper[standard_field] = f"{self.base_url}{value}"
                        else:
                            paper[standard_field] = value or ""
                    elif self.source_name == "clinicaltrials":
                        # ClinicalTrials: Convert NCT ID to study URL
                        if value and isinstance(value, str):
                            # Handle both "NCT01832077" and "/NCT01832077" formats
                            nct_id = value.strip("/")
                            paper[standard_field] = (
                                f"https://clinicaltrials.gov/study/{nct_id}"
                            )
                        else:
                            paper[standard_field] = value or ""
                    else:
                        paper[standard_field] = value or ""
                else:
                    paper[standard_field] = value or ""
            else:
                # Set default values for unmapped fields
                if standard_field in ["authors"]:
                    paper[standard_field] = []
                elif standard_field in ["citation_count"]:
                    paper[standard_field] = 0
                else:
                    paper[standard_field] = ""

        return super()._standardize_paper(paper)

    async def _perform_search(
        self, query: str, limit: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """
        Perform search using generic HTTP API configuration.

        Args:
            query: Search query
            limit: Maximum results to return
            **kwargs: Additional search parameters

        Returns:
            List of standardized paper dictionaries
        """
        try:
            # Rate limiting
            if self.rate_limit_delay > 0:
                await asyncio.sleep(self.rate_limit_delay)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build request
                url = f"{(self.base_url or '').rstrip('/')}{self.search_path}"
                headers = self._build_headers()
                params = self._build_params(query, limit, **kwargs)

                self.logger.debug(f"Requesting {url} with params: {params}")

                # Make request
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 429:
                    # Rate limited - wait and retry once
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    response = await client.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    self.logger.warning(
                        f"API returned {response.status_code}: {response.text[:200]}"
                    )
                    return []

                # Parse response
                if self.response_format == "json":
                    data = response.json()
                else:
                    self.logger.error(
                        f"Unsupported response format: {self.response_format}"
                    )
                    return []

                # Extract results
                results = self._get_nested_value(data, self.results_path)
                if not isinstance(results, list):
                    self.logger.warning(
                        f"Expected list at {self.results_path}, got {type(results)}"
                    )
                    return []

                # Convert to standard format
                papers = []
                for item in results[:limit]:
                    try:
                        paper = self._standardize_paper(item)

                        # Quality filters: exclude junk metadata entries
                        if not paper.get("title"):
                            continue

                        # Filter out conference/journal metadata entries
                        # (e.g., "Table of Contents" entries with no authors)
                        title_lower = paper.get("title", "").lower()
                        has_authors = bool(paper.get("authors"))

                        # Skip metadata entries: ToC, front matter, back matter, etc.
                        metadata_titles = [
                            "table of contents",
                            "front matter",
                            "back matter",
                            "editorial board",
                            "author index",
                            "subject index",
                            "volume information",
                            "copyright",
                            "preface",
                        ]

                        # Exclude if title matches metadata patterns AND has no authors
                        if not has_authors and any(
                            title_lower == metadata
                            or title_lower.startswith(metadata + " ")
                            for metadata in metadata_titles
                        ):
                            self.logger.debug(
                                f"Filtered out metadata entry: '{paper.get('title')}' (no authors)"
                            )
                            continue

                        papers.append(paper)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse item: {e}")
                        continue

                self.logger.info(f"Found {len(papers)} papers from {self.source_name}")
                return papers

        except httpx.TimeoutException:
            self.logger.warning(f"Timeout searching {self.source_name}")
            return []
        except httpx.HTTPError as e:
            self.logger.warning(f"HTTP error searching {self.source_name}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error searching {self.source_name}: {e}")
            return []
