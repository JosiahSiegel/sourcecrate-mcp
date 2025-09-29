"""
Fuzzy paper matching utilities for cross-source deduplication.
Implements various matching algorithms to identify duplicate papers from different sources.
"""

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MatchScore:
    """Represents a similarity score between two papers."""

    overall_score: float
    title_score: float
    author_score: float
    year_score: float
    doi_score: float
    confidence: str  # "high", "medium", "low"

    def is_match(self, threshold: float = 0.8) -> bool:
        """Determine if this represents a valid match."""
        return self.overall_score >= threshold


class FuzzyPaperMatcher:
    """Advanced fuzzy matching for academic papers across different sources."""

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the fuzzy matcher.

        Args:
            strict_mode: If True, requires higher similarity scores for matches
        """
        self.strict_mode = strict_mode
        self.match_threshold = 0.85 if strict_mode else 0.8

    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        if not title:
            return ""

        # Convert to lowercase
        normalized = title.lower().strip()

        # Remove common prefixes/suffixes
        prefixes = ["a ", "an ", "the "]
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]

        # Remove punctuation and extra whitespace
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Remove common academic words that don't affect matching
        # But preserve words that might be important for disambiguation
        stop_words = {
            "study",
            "investigation",
            "research",
            "case",
            "systematic",
            "meta",
        }
        words = normalized.split()
        words = [w for w in words if w not in stop_words and len(w) > 1]  # Also remove single letters

        return " ".join(words)

    def normalize_author_name(self, author: str) -> str:
        """Normalize author name for comparison."""
        if not author:
            return ""

        # Handle different author formats
        normalized = author.strip().lower()

        # Remove titles and suffixes
        titles = ["dr", "prof", "professor", "mr", "ms", "mrs"]
        suffixes = ["jr", "sr", "iii", "ii", "iv", "phd", "md"]

        words = normalized.split()
        words = [w.rstrip(".") for w in words if w.rstrip(".") not in titles + suffixes]

        return " ".join(words)

    def extract_author_list(self, authors: Any) -> list[str]:
        """Extract and normalize author list from various formats."""
        if not authors:
            return []

        author_list = []

        if isinstance(authors, str):
            # Split by common delimiters
            authors = re.split(r"[,;]|\sand\s", authors)

        if isinstance(authors, list):
            for author in authors:
                if isinstance(author, str):
                    author_list.append(self.normalize_author_name(author))
                elif isinstance(author, dict):
                    name = author.get("name") or author.get("full_name") or ""
                    if name:
                        author_list.append(self.normalize_author_name(name))

        return [a for a in author_list if a]  # Remove empty names

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)

        if not norm1 or not norm2:
            return 0.0

        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # Boost score for exact matches after normalization
        if norm1 == norm2:
            similarity = 1.0

        return similarity

    def calculate_author_similarity(self, authors1: Any, authors2: Any) -> float:
        """Calculate similarity between author lists."""
        list1 = self.extract_author_list(authors1)
        list2 = self.extract_author_list(authors2)

        if not list1 or not list2:
            return 0.0

        # Calculate overlap-based similarity
        set1 = set(list1)
        set2 = set(list2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        # Basic Jaccard similarity
        jaccard = intersection / union

        # Boost score if first authors match
        if list1[0] == list2[0]:
            jaccard = min(1.0, jaccard + 0.2)

        return jaccard

    def calculate_year_similarity(self, year1: Any, year2: Any) -> float:
        """Calculate similarity between publication years."""
        try:
            y1 = int(year1) if year1 else 0
            y2 = int(year2) if year2 else 0

            if y1 == 0 or y2 == 0:
                return 0.5  # Unknown year gets neutral score

            if y1 == y2:
                return 1.0
            elif abs(y1 - y2) == 1:
                return 0.8  # Close years might be pre-print vs published
            elif abs(y1 - y2) <= 2:
                return 0.6
            else:
                return 0.0

        except (ValueError, TypeError):
            return 0.5

    def calculate_doi_similarity(self, doi1: str, doi2: str) -> float:
        """Calculate similarity between DOIs."""
        if not doi1 or not doi2:
            return 0.0

        # Normalize DOIs
        norm1 = (
            doi1.strip()
            .lower()
            .replace("https://doi.org/", "")
            .replace("http://doi.org/", "")
        )
        norm2 = (
            doi2.strip()
            .lower()
            .replace("https://doi.org/", "")
            .replace("http://doi.org/", "")
        )

        if norm1 == norm2:
            return 1.0
        else:
            return 0.0

    def calculate_match_score(
        self, paper1: dict[str, Any], paper2: dict[str, Any]
    ) -> MatchScore:
        """Calculate comprehensive match score between two papers."""

        # Calculate individual component scores
        title_score = self.calculate_title_similarity(
            paper1.get("title", ""), paper2.get("title", "")
        )

        author_score = self.calculate_author_similarity(
            paper1.get("authors"), paper2.get("authors")
        )

        year_score = self.calculate_year_similarity(
            paper1.get("year"), paper2.get("year")
        )

        doi_score = self.calculate_doi_similarity(
            paper1.get("doi", ""), paper2.get("doi", "")
        )

        # Weighted overall score
        # Title is most important, followed by authors, then year, then DOI
        weights = {"title": 0.5, "author": 0.3, "year": 0.1, "doi": 0.1}

        # Calculate weighted overall score
        overall_score = (
            title_score * weights["title"]
            + author_score * weights["author"]
            + year_score * weights["year"]
            + doi_score * weights["doi"]
        )

        # If DOI exists and matches perfectly, boost the score but don't override completely
        if doi_score == 1.0:
            overall_score = min(1.0, overall_score + 0.1)  # Slight boost for matching DOI

        # Determine confidence level
        if overall_score >= 0.9:
            confidence = "high"
        elif overall_score >= 0.7:
            confidence = "medium"
        else:
            confidence = "low"

        return MatchScore(
            overall_score=overall_score,
            title_score=title_score,
            author_score=author_score,
            year_score=year_score,
            doi_score=doi_score,
            confidence=confidence,
        )

    def find_duplicates(self, papers: list[dict[str, Any]]) -> list[list[int]]:
        """
        Find duplicate papers in a list.

        Args:
            papers: List of paper dictionaries

        Returns:
            List of lists, where each inner list contains indices of duplicate papers
        """
        if not papers or len(papers) < 2:
            return []

        duplicates = []
        processed = set()

        for i, paper1 in enumerate(papers):
            if i in processed:
                continue

            current_group = [i]
            processed.add(i)

            for j, paper2 in enumerate(papers[i + 1 :], i + 1):
                if j in processed:
                    continue

                score = self.calculate_match_score(paper1, paper2)

                if score.is_match(self.match_threshold):
                    current_group.append(j)
                    processed.add(j)

                    logger.debug(
                        f"Found duplicate: '{paper1.get('title', '')[:50]}...' == "
                        f"'{paper2.get('title', '')[:50]}...' (score: {score.overall_score:.3f})"
                    )

            # Only add groups with actual duplicates
            if len(current_group) > 1:
                duplicates.append(current_group)

        return duplicates

    def merge_duplicate_papers(self, papers: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Merge multiple duplicate papers into a single enhanced version.

        Args:
            papers: List of duplicate papers to merge

        Returns:
            Single merged paper with best available metadata
        """
        if not papers:
            return {}

        if len(papers) == 1:
            return papers[0]

        # Start with the paper that has the most complete metadata
        best_paper = max(papers, key=lambda p: len([v for v in p.values() if v]))
        merged = best_paper.copy()

        # Track sources (preserve order)
        sources = []
        for paper in papers:
            source = paper.get("source", "unknown")
            if source not in sources:
                sources.append(source)

        merged["_merged_sources"] = sources
        merged["_merged_count"] = len(papers)

        # Merge specific fields intelligently
        for paper in papers:
            # Use the longest/most complete title
            if paper.get("title") and len(paper["title"]) > len(
                merged.get("title", "")
            ):
                merged["title"] = paper["title"]

            # Merge abstracts (use longest)
            if paper.get("abstract") and len(paper.get("abstract", "")) > len(
                merged.get("abstract", "")
            ):
                merged["abstract"] = paper["abstract"]

            # Use DOI if available
            if paper.get("doi") and not merged.get("doi"):
                merged["doi"] = paper["doi"]

            # Use PDF URL if available
            if paper.get("pdf_url") and not merged.get("pdf_url"):
                merged["pdf_url"] = paper["pdf_url"]

            # Merge authors (combine unique authors)
            if paper.get("authors"):
                existing_authors = set(
                    self.normalize_author_name(str(a))
                    for a in merged.get("authors", [])
                )
                for author in paper["authors"]:
                    normalized = self.normalize_author_name(str(author))
                    if normalized not in existing_authors:
                        if "authors" not in merged:
                            merged["authors"] = []
                        merged["authors"].append(author)
                        existing_authors.add(normalized)

        logger.info(
            f"Merged {len(papers)} papers from sources: {', '.join(sources)} "
            f"for paper: '{merged.get('title', '')[:50]}...'"
        )

        return merged

    def deduplicate_papers(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Remove duplicates from a list of papers and merge metadata.

        Args:
            papers: List of papers that may contain duplicates

        Returns:
            Deduplicated list with merged metadata
        """
        if not papers:
            return []

        duplicate_groups = self.find_duplicates(papers)

        if not duplicate_groups:
            return papers

        # Track which papers have been merged
        merged_indices = set()
        for group in duplicate_groups:
            merged_indices.update(group)

        result = []

        # Add merged papers
        for group in duplicate_groups:
            group_papers = [papers[i] for i in group]
            merged_paper = self.merge_duplicate_papers(group_papers)
            result.append(merged_paper)

        # Add non-duplicate papers
        for i, paper in enumerate(papers):
            if i not in merged_indices:
                result.append(paper)

        logger.info(
            f"Deduplication: {len(papers)} → {len(result)} papers "
            f"({len(papers) - len(result)} duplicates removed)"
        )

        return result


# Global instance for convenience
fuzzy_matcher = FuzzyPaperMatcher()
