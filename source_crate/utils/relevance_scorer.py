"""
Query Relevance Scorer

Implements sophisticated relevance scoring to improve search result quality.
Addresses Issue 4.3: Query Relevance Scoring Issues from COMPREHENSIVE_ISSUE_RESOLUTION.md
"""

import logging
import math
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Calculates relevance scores for academic papers based on query matching"""

    def __init__(self) -> None:
        # Load field weights from YAML config
        self.field_weights_profiles = self._load_field_weights_from_config()

        # Common stop words to ignore in relevance scoring
        self.stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "he",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "that",
            "the",
            "to",
            "was",
            "with",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
            "shall",
            "this",
            "these",
            "those",
            "they",
            "their",
            "them",
            "we",
            "our",
            "us",
            "you",
            "your",
            "i",
            "me",
            "my",
        }

        # Academic keywords that should get higher weight
        # Note: "review" and "survey" removed as they're too generic and cause false positives
        # (e.g., "egyptology" → "egyptology review" → papers about peer review)
        self.academic_keywords = {
            "study",
            "research",
            "analysis",
            "investigation",
            "examination",
            "evaluation",
            "assessment",
            "methodology",
            "approach",
            "method",
            "technique",
            "framework",
            "model",
            "theory",
            "hypothesis",
            "findings",
            "results",
            "conclusion",
            "evidence",
            "data",
            "experiment",
            "trial",
            "meta-analysis",  # Kept: specific academic term
            "systematic review",  # Kept: specific academic term
        }

    def _load_field_weights_from_config(self) -> dict[str, dict[str, float]]:
        """Load field weight profiles from YAML config."""
        try:
            from ..config import get_current_config

            config = get_current_config()
            if config and hasattr(config, "intent") and config.intent:
                return config.intent.field_weights
        except Exception as e:
            logger.debug(f"Could not load field weights from config: {e}")

        # Fallback to default field weights if config not available
        return {
            "default": {
                "title": 0.40,  # Most important for relevance
                "abstract": 0.30,  # Very important
                "keywords": 0.15,  # If available
                "authors": 0.10,  # Author names can be relevant
                "journal": 0.05,  # Journal name less important
            },
            "author_search": {
                "authors": 0.70,  # Prioritize author matches for author searches
                "title": 0.15,
                "abstract": 0.10,
                "keywords": 0.05,
                "journal": 0.00,
            },
        }

    def normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep spaces and hyphens
        text = re.sub(r"[^\w\s\-]", " ", text)

        # Replace multiple spaces with single space
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def extract_keywords(self, text: str) -> set[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return set()

        normalized = self.normalize_text(text)
        words = normalized.split()

        # Remove stop words and short words
        keywords = {
            word for word in words if len(word) > 2 and word not in self.stop_words
        }

        return keywords

    def calculate_tf_idf_score(
        self, query_keywords: set[str], text_keywords: set[str], total_docs: int = 1000
    ) -> float:
        """
        Calculate TF-IDF-like score for keyword matching

        Args:
            query_keywords: Keywords from the search query
            text_keywords: Keywords from the text field
            total_docs: Estimated total documents (for IDF calculation)

        Returns:
            TF-IDF score between 0 and 1
        """
        if not query_keywords or not text_keywords:
            return 0.0

        # Find intersection
        matching_keywords = query_keywords.intersection(text_keywords)
        if not matching_keywords:
            return 0.0

        # Calculate TF (term frequency) component
        tf_score = len(matching_keywords) / len(query_keywords)

        # Simple IDF approximation (assumes common words appear in 10% of docs)
        # Real IDF would require corpus statistics
        idf_boost = 1.0
        for keyword in matching_keywords:
            if keyword in self.academic_keywords:
                idf_boost += 0.2  # Boost academic terms

        # Combine TF and IDF-like boost
        score = tf_score * min(idf_boost, 2.0)  # Cap the boost

        return min(score, 1.0)

    def calculate_phrase_match_score(self, query: str, text: str) -> float:
        """Calculate score based on phrase matching"""
        if not query or not text:
            return 0.0

        normalized_query = self.normalize_text(query)
        normalized_text = self.normalize_text(text)

        # Check for exact phrase match
        if normalized_query in normalized_text:
            return 1.0

        # Check for partial phrase matches (consecutive words)
        query_words = normalized_query.split()
        if len(query_words) < 2:
            return 0.0

        max_consecutive = 0
        for i in range(len(query_words)):
            for j in range(i + 2, len(query_words) + 1):
                phrase = " ".join(query_words[i:j])
                if phrase in normalized_text:
                    max_consecutive = max(max_consecutive, j - i)

        if max_consecutive > 0:
            return max_consecutive / len(query_words)

        return 0.0

    def calculate_recency_score(self, year: int) -> float:
        """Calculate recency score (newer papers get higher scores)"""
        if not year:
            return 0.5  # Neutral score for unknown year

        current_year = datetime.now().year
        years_old = current_year - year

        if years_old <= 0:
            return 1.0  # Current or future year
        elif years_old <= 2:
            return 0.9  # Very recent
        elif years_old <= 5:
            return 0.7  # Recent
        elif years_old <= 10:
            return 0.5  # Moderate
        else:
            # Exponential decay for older papers
            return max(0.1, 0.5 * math.exp(-0.1 * (years_old - 10)))

    def calculate_citation_score(self, citation_count: int) -> float:
        """Calculate citation-based authority score"""
        if not citation_count or citation_count <= 0:
            return 0.2  # Low baseline for uncited papers

        # Logarithmic scaling for citation count
        # High-impact papers can have thousands of citations
        if citation_count >= 1000:
            return 1.0
        elif citation_count >= 100:
            return 0.9
        elif citation_count >= 50:
            return 0.8
        elif citation_count >= 20:
            return 0.7
        elif citation_count >= 10:
            return 0.6
        elif citation_count >= 5:
            return 0.5
        else:
            return 0.3

    def calculate_completeness_bonus(self, paper_data: dict[str, Any]) -> float:
        """Calculate bonus score based on metadata completeness"""
        completeness = paper_data.get("metadata_completeness", 0.0)

        # Ensure we have a float value
        if not isinstance(completeness, (int, float)):
            return 0.0

        # Convert completeness (0-1) to bonus (0-0.1)
        return float(completeness) * 0.1

    def score_paper_relevance(
        self, query: str, paper_data: dict, field_weights_profile: str = "default"
    ) -> float:
        """
        Calculate overall relevance score for a paper

        Args:
            query: Search query string
            paper_data: Paper metadata dictionary
            field_weights_profile: Field weight profile to use ("default" or "author_search")

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not query or not paper_data:
            return 0.0

        # Get field weights for the specified profile
        field_weights = self.field_weights_profiles.get(
            field_weights_profile, self.field_weights_profiles["default"]
        )

        query_keywords = self.extract_keywords(query)
        total_score = 0.0

        # 1. Content relevance score (weighted by field importance)
        content_score = 0.0

        for field, weight in field_weights.items():
            field_value = paper_data.get(field, "")

            if field == "authors" and isinstance(field_value, list):
                field_value = " ".join(str(author) for author in field_value)

            field_text = str(field_value) if field_value else ""

            if field_text:
                # TF-IDF score for keyword matching
                field_keywords = self.extract_keywords(field_text)
                tf_idf_score = self.calculate_tf_idf_score(
                    query_keywords, field_keywords
                )

                # Phrase matching score
                phrase_score = self.calculate_phrase_match_score(query, field_text)

                # Combined field score (weighted average)
                field_score = (0.7 * tf_idf_score) + (0.3 * phrase_score)
                content_score += weight * field_score

        # 2. Recency score (10% weight)
        year = paper_data.get("year")
        if isinstance(year, str):
            try:
                year = int(year)
            except ValueError:
                year = None

        recency_score = self.calculate_recency_score(year) if year else 0.5

        # 3. Citation authority score (10% weight)
        citation_count = paper_data.get("citation_count", 0)
        if isinstance(citation_count, str):
            try:
                citation_count = int(citation_count)
            except ValueError:
                citation_count = 0

        citation_score = self.calculate_citation_score(citation_count)

        # 4. Metadata completeness bonus (up to 10% bonus)
        completeness_bonus = self.calculate_completeness_bonus(paper_data)

        # Combine all scores
        # Content: 75%, Recency: 12.5%, Citations: 12.5%, Completeness: bonus
        total_score = (
            0.75 * content_score
            + 0.125 * recency_score
            + 0.125 * citation_score
            + completeness_bonus
        )

        return min(total_score, 1.0)  # Cap at 1.0

    def rank_papers(
        self, query: str, papers: list[dict], field_weights_profile: str = "default"
    ) -> list[dict]:
        """
        Rank papers by relevance score

        Args:
            query: Search query string
            papers: List of paper dictionaries
            field_weights_profile: Field weight profile to use ("default" or "author_search")

        Returns:
            Papers sorted by relevance score (highest first)
        """
        if not papers:
            return []

        # Calculate relevance scores
        scored_papers = []
        for paper in papers:
            relevance_score = self.score_paper_relevance(
                query, paper, field_weights_profile
            )
            paper_with_score = paper.copy()
            paper_with_score["relevance_score"] = relevance_score * 100
            scored_papers.append(paper_with_score)

        # Sort by relevance score (descending)
        ranked_papers = sorted(
            scored_papers, key=lambda p: p.get("relevance_score", 0.0), reverse=True
        )

        return ranked_papers

    def filter_low_relevance(
        self, papers: list[dict], min_threshold: float = 10
    ) -> list[dict]:
        """
        Filter out papers with very low relevance scores

        Args:
            papers: List of papers with relevance scores
            min_threshold: Minimum relevance percentage (0–100) to keep

        Returns:
            Filtered list of papers
        """
        return [
            paper
            for paper in papers
            if paper.get("relevance_score", 0.0) >= min_threshold
        ]


# Global instance for easy access
relevance_scorer = RelevanceScorer()
