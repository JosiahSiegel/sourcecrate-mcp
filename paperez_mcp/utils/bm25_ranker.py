"""
BM25-based source ranking for intelligent source selection.
Uses BM25 algorithm to rank academic sources based on query relevance.
Supports both built-in and custom user-defined sources.

Uses bm25s library for high-performance BM25 implementation (500x faster than rank-bm25).
"""

from dataclasses import dataclass
from typing import Any

import bm25s  # type: ignore

from ..config import get_current_config


@dataclass
class SourceProfile:
    """Profile of an academic source with its specialty terms and characteristics."""

    name: str
    specialty_terms: list[str]
    domain_focus: list[str]
    content_type: str  # "journal", "preprint", "repository", "aggregator"
    temporal_coverage: str  # "recent", "comprehensive", "historical"
    access_type: str  # "open", "mixed", "subscription"
    quality_indicators: dict[str, float]


class BM25SourceRanker:
    """BM25-based ranking system for academic sources."""

    def __init__(self) -> None:
        self.source_profiles = self._build_source_profiles()
        self.k1 = 1.2  # Term frequency saturation parameter
        self.b = 0.75  # Document length normalization parameter

        # Initialize rank-bm25 with source profiles as corpus
        self._initialize_bm25_index()

    def _create_default_profile(
        self, source_name: str, source_config: Any
    ) -> SourceProfile:
        """Create a default profile for unknown/custom sources."""
        # Extract keywords from source description/coverage if available
        specialty_terms = []
        domain_focus = ["general"]
        content_type = "repository"
        temporal_coverage = "comprehensive"
        access_type = "mixed"

        if hasattr(source_config, "config") and source_config.config:
            config = source_config.config
            # Extract terms from description and coverage
            description = getattr(config, "description", "")
            coverage = getattr(config, "coverage", "")

            # Basic keyword extraction from description/coverage
            text = f"{description} {coverage}".lower()
            keywords = [word.strip() for word in text.split() if len(word.strip()) > 3]
            specialty_terms.extend(keywords[:20])  # Limit to reasonable size

            # Infer characteristics from description
            if any(term in text for term in ["medical", "biomedical", "health"]):
                domain_focus = ["medical"]
            elif any(term in text for term in ["computer", "ai", "algorithm", "tech"]):
                domain_focus = ["computer_science"]
            elif any(term in text for term in ["history", "historical", "archive"]):
                domain_focus = ["historical"]
                temporal_coverage = "historical"
            elif any(term in text for term in ["business", "economics", "finance"]):
                domain_focus = ["business"]
            elif any(term in text for term in ["social", "psychology", "sociology"]):
                domain_focus = ["social_science"]
            elif any(term in text for term in ["humanities", "literature", "art"]):
                domain_focus = ["humanities"]

            # Infer access type
            if any(term in text for term in ["open", "free", "public"]):
                access_type = "open"
            elif any(term in text for term in ["subscription", "commercial"]):
                access_type = "subscription"

            # Infer content type
            if any(term in text for term in ["preprint", "arxiv"]):
                content_type = "preprint"
            elif any(term in text for term in ["journal", "peer"]):
                content_type = "journal"
            elif any(term in text for term in ["repository", "archive"]):
                content_type = "repository"

        # Add source name as a specialty term
        specialty_terms.append(source_name.lower())

        return SourceProfile(
            name=source_name.title(),
            specialty_terms=specialty_terms or ["research", "academic", "papers"],
            domain_focus=domain_focus,
            content_type=content_type,
            temporal_coverage=temporal_coverage,
            access_type=access_type,
            quality_indicators={
                "peer_review": 0.5,  # Default moderate quality
                "recency": 0.6,
                "technical_depth": 0.5,
                "accessibility": 0.7,
            },
        )

    def _build_source_profiles(self) -> dict[str, SourceProfile]:
        """Build profiles for academic sources from configuration and built-in knowledge."""
        profiles = {}

        # Try to get current configuration
        try:
            config = get_current_config()
            configured_sources = config.sources if config else {}
        except Exception:
            # Fallback if config not available
            configured_sources = {}

        # Built-in profiles for known sources (optimized for performance)
        builtin_profiles = {
            "arxiv": SourceProfile(
                name="arXiv",
                specialty_terms=[
                    # Computer Science
                    "algorithm",
                    "machine learning",
                    "neural network",
                    "deep learning",
                    "artificial intelligence",
                    "computer vision",
                    "natural language processing",
                    "data mining",
                    "software engineering",
                    "distributed systems",
                    "cryptography",
                    "computational complexity",
                    "programming languages",
                    # Physics
                    "quantum mechanics",
                    "particle physics",
                    "astrophysics",
                    "cosmology",
                    "condensed matter",
                    "statistical mechanics",
                    "relativity",
                    "optics",
                    "plasma physics",
                    "nuclear physics",
                    "theoretical physics",
                    # Mathematics
                    "algebra",
                    "topology",
                    "analysis",
                    "geometry",
                    "number theory",
                    "combinatorics",
                    "probability",
                    "statistics",
                    "optimization",
                    "differential equations",
                    "mathematical physics",
                    # Preprint indicators
                    "preprint",
                    "preliminary",
                    "draft",
                    "working paper",
                    "submitted",
                    "under review",
                    "recent",
                    "latest",
                    "new",
                    "novel",
                    "emerging",
                ],
                domain_focus=["stem", "computer_science", "physics", "mathematics"],
                content_type="preprint",
                temporal_coverage="recent",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.3,  # Not peer-reviewed
                    "recency": 0.9,  # Very recent
                    "technical_depth": 0.8,
                    "accessibility": 0.9,
                },
            ),
            "semantic_scholar": SourceProfile(
                name="Semantic Scholar",
                specialty_terms=[
                    # Broad academic coverage
                    "research",
                    "study",
                    "analysis",
                    "paper",
                    "article",
                    "publication",
                    "citation",
                    "bibliography",
                    "author",
                    "conference",
                    "journal",
                    "peer review",
                    "methodology",
                    "experiment",
                    "data",
                    "results",
                    # AI/CS focus
                    "artificial intelligence",
                    "machine learning",
                    "computer science",
                    "natural language processing",
                    "computer vision",
                    "robotics",
                    "human-computer interaction",
                    "information retrieval",
                    # Cross-disciplinary
                    "interdisciplinary",
                    "multidisciplinary",
                    "collaboration",
                    "citation network",
                    "impact factor",
                    "h-index",
                ],
                domain_focus=["stem", "social_science", "medical", "general"],
                content_type="aggregator",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.8,
                    "recency": 0.7,
                    "technical_depth": 0.7,
                    "accessibility": 0.8,
                },
            ),
            "crossref": SourceProfile(
                name="CrossRef",
                specialty_terms=[
                    # Formal publication terms
                    "journal",
                    "article",
                    "publication",
                    "peer review",
                    "publisher",
                    "doi",
                    "citation",
                    "reference",
                    "bibliography",
                    "academic",
                    "scholarly",
                    "research",
                    "study",
                    "analysis",
                    "methodology",
                    "experiment",
                    "results",
                    "conclusion",
                    "abstract",
                    "introduction",
                    # All academic domains (broad)
                    "science",
                    "technology",
                    "medicine",
                    "humanities",
                    "social science",
                    "engineering",
                    "mathematics",
                    "physics",
                    "chemistry",
                    "biology",
                    "psychology",
                    "sociology",
                    "economics",
                    "political science",
                    "philosophy",
                    "literature",
                    "history",
                    "art",
                    "music",
                ],
                domain_focus=["all"],
                content_type="journal",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.6,
                    "technical_depth": 0.8,
                    "accessibility": 0.5,
                },
            ),
            "pubmed": SourceProfile(
                name="PubMed",
                specialty_terms=[
                    # Medical/Biomedical
                    "medicine",
                    "medical",
                    "clinical",
                    "patient",
                    "disease",
                    "treatment",
                    "therapy",
                    "drug",
                    "pharmaceutical",
                    "healthcare",
                    "hospital",
                    "diagnosis",
                    "symptom",
                    "syndrome",
                    "pathology",
                    "epidemiology",
                    "public health",
                    "preventive medicine",
                    "emergency medicine",
                    # Biological
                    "biology",
                    "biomedical",
                    "biochemistry",
                    "molecular biology",
                    "cell biology",
                    "genetics",
                    "genomics",
                    "proteomics",
                    "bioinformatics",
                    "neuroscience",
                    "immunology",
                    "microbiology",
                    "virology",
                    "anatomy",
                    "physiology",
                    "pharmacology",
                    "toxicology",
                    # Research types
                    "clinical trial",
                    "randomized controlled",
                    "case study",
                    "cohort study",
                    "meta-analysis",
                    "systematic review",
                ],
                domain_focus=["medical", "biological"],
                content_type="journal",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.7,
                    "technical_depth": 0.9,
                    "accessibility": 0.6,
                },
            ),
            "pubmed_central": SourceProfile(
                name="PubMed Central",
                specialty_terms=[
                    # Medical/Biomedical with full-text focus
                    "medicine",
                    "medical",
                    "clinical",
                    "patient",
                    "disease",
                    "treatment",
                    "therapy",
                    "drug",
                    "pharmaceutical",
                    "healthcare",
                    "hospital",
                    "diagnosis",
                    "symptom",
                    "syndrome",
                    "pathology",
                    "epidemiology",
                    "public health",
                    "preventive medicine",
                    "emergency medicine",
                    # Biological
                    "biology",
                    "biomedical",
                    "biochemistry",
                    "molecular biology",
                    "cell biology",
                    "genetics",
                    "genomics",
                    "proteomics",
                    "bioinformatics",
                    "neuroscience",
                    "immunology",
                    "microbiology",
                    "virology",
                    "anatomy",
                    "physiology",
                    "pharmacology",
                    "toxicology",
                    # Full-text specific terms
                    "full text",
                    "open access",
                    "pmc",
                    "full paper",
                    "complete text",
                    "detailed analysis",
                    "comprehensive study",
                    "in-depth research",
                    # Research types
                    "clinical trial",
                    "randomized controlled",
                    "case study",
                    "cohort study",
                    "meta-analysis",
                    "systematic review",
                ],
                domain_focus=["medical", "biological"],
                content_type="repository",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.7,
                    "technical_depth": 0.9,
                    "accessibility": 0.9,  # Higher than PubMed due to open access
                },
            ),
            "clinicaltrials": SourceProfile(
                name="ClinicalTrials.gov",
                specialty_terms=[
                    # Clinical trial specific
                    "clinical trial",
                    "trial",
                    "study",
                    "protocol",
                    "intervention",
                    "randomized",
                    "controlled",
                    "blinded",
                    "placebo",
                    "treatment arm",
                    "primary endpoint",
                    "secondary endpoint",
                    "efficacy",
                    "safety",
                    "adverse event",
                    "side effect",
                    "dosage",
                    "dose",
                    "administration",
                    # Medical conditions
                    "disease",
                    "disorder",
                    "condition",
                    "syndrome",
                    "cancer",
                    "diabetes",
                    "hypertension",
                    "depression",
                    "alzheimer",
                    "parkinson",
                    "stroke",
                    "heart disease",
                    "kidney disease",
                    "liver disease",
                    "lung disease",
                    # Treatment types
                    "drug",
                    "medication",
                    "therapy",
                    "treatment",
                    "pharmaceutical",
                    "vaccine",
                    "immunotherapy",
                    "chemotherapy",
                    "surgery",
                    "device",
                    "behavioral intervention",
                    "dietary intervention",
                    "exercise",
                    # Trial phases and status
                    "phase 1",
                    "phase 2",
                    "phase 3",
                    "phase 4",
                    "recruiting",
                    "active",
                    "completed",
                    "terminated",
                    "withdrawn",
                    "enrolling",
                    # Regulatory
                    "fda",
                    "approval",
                    "regulatory",
                    "investigational",
                    "experimental",
                ],
                domain_focus=["medical", "clinical"],
                content_type="repository",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.7,  # Protocols, not peer-reviewed papers
                    "recency": 0.8,  # Often current trials
                    "technical_depth": 0.8,
                    "accessibility": 0.9,  # Public access
                },
            ),
            "core": SourceProfile(
                name="CORE",
                specialty_terms=[
                    # Open access focus
                    "open access",
                    "repository",
                    "institutional",
                    "archive",
                    "digital library",
                    "collection",
                    "preservation",
                    "metadata",
                    # Humanities/Social Sciences
                    "humanities",
                    "social science",
                    "history",
                    "literature",
                    "philosophy",
                    "art",
                    "culture",
                    "society",
                    "politics",
                    "economics",
                    "anthropology",
                    "sociology",
                    "psychology",
                    # Historical document types
                    "declaration",
                    "treaty",
                    "proclamation",
                    "manifesto",
                    "charter",
                    "constitution",
                    "agreement",
                    "protocol",
                    "memorandum",
                    "correspondence",
                    "letter",
                    "diplomatic",
                    "government document",
                    "official document",
                    "policy document",
                    "legal document",
                    "historic document",
                    # Historical periods and events
                    "colonial",
                    "empire",
                    "independence",
                    "revolution",
                    "war",
                    "conflict",
                    "peace",
                    "settlement",
                    "mandate",
                    "territory",
                    "nationalism",
                    "sovereignty",
                    "diplomacy",
                    "international relations",
                    "british",
                    "ottoman",
                    "palestine",
                    "zionism",
                    "middle east",
                    # Economic and financial history
                    "banking",
                    "federal reserve",
                    "central bank",
                    "monetary",
                    "finance",
                    "economic",
                    "financial",
                    "capitalism",
                    "business",
                    "corporate",
                    "wall street",
                    "investment",
                    "securities",
                    "bonds",
                    "stock market",
                    "depression",
                    "recession",
                    "panic",
                    "crisis",
                    "bubble",
                    "morgan",
                    "rockefeller",
                    "rothschild",
                    "warburg",
                    "aldrich",
                    "jekyll island",
                    "money trust",
                    "banking reform",
                    "currency",
                    # Historical/Cultural
                    "historical",
                    "cultural",
                    "heritage",
                    "tradition",
                    "civilization",
                    "archive",
                    "manuscript",
                    "document",
                    "primary source",
                    "secondary source",
                    "archaeological",
                    "ethnographic",
                ],
                domain_focus=["humanities", "social_science", "historical"],
                content_type="repository",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.7,
                    "recency": 0.5,
                    "technical_depth": 0.6,
                    "accessibility": 0.9,
                },
            ),
            "doaj": SourceProfile(
                name="DOAJ",
                specialty_terms=[
                    # Open access journals
                    "open access",
                    "journal",
                    "peer review",
                    "editorial",
                    "publication",
                    "scholarly",
                    "academic",
                    "research",
                    "article",
                    "paper",
                    # Quality indicators
                    "peer reviewed",
                    "editorial board",
                    "impact factor",
                    "indexing",
                    "citation",
                    "quality",
                    "standards",
                    "ethics",
                    "transparency",
                    # Diverse fields
                    "interdisciplinary",
                    "multidisciplinary",
                    "cross-disciplinary",
                    "international",
                    "global",
                    "regional",
                    "specialized",
                    # Humanities and social sciences
                    "humanities",
                    "history",
                    "historical",
                    "archaeology",
                    "archaeological",
                    "social science",
                    "cultural",
                    "anthropology",
                    # Sciences
                    "science",
                    "medicine",
                    "medical",
                    "biology",
                    "physics",
                    "chemistry",
                ],
                domain_focus=["all"],
                content_type="journal",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.6,
                    "technical_depth": 0.7,
                    "accessibility": 0.9,
                },
            ),
            "socarxiv": SourceProfile(
                name="SocArXiv",
                specialty_terms=[
                    # Social Sciences
                    "social science",
                    "sociology",
                    "anthropology",
                    "political science",
                    "economics",
                    "psychology",
                    "social psychology",
                    "cognitive science",
                    "communication",
                    "media studies",
                    "cultural studies",
                    "gender studies",
                    # Social phenomena
                    "society",
                    "community",
                    "culture",
                    "identity",
                    "behavior",
                    "social network",
                    "social media",
                    "public opinion",
                    "survey",
                    "interview",
                    "ethnography",
                    "qualitative",
                    "quantitative",
                    # Preprint characteristics
                    "preprint",
                    "working paper",
                    "draft",
                    "preliminary",
                    "submitted",
                ],
                domain_focus=["social_science"],
                content_type="preprint",
                temporal_coverage="recent",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.3,
                    "recency": 0.9,
                    "technical_depth": 0.6,
                    "accessibility": 0.8,
                },
            ),
            "osf_preprints": SourceProfile(
                name="OSF Preprints",
                specialty_terms=[
                    # General preprint terms
                    "preprint",
                    "working paper",
                    "draft",
                    "preliminary",
                    "under review",
                    "submitted",
                    "open science",
                    "reproducible research",
                    "transparency",
                    # Broad academic coverage
                    "research",
                    "study",
                    "experiment",
                    "data",
                    "methodology",
                    "analysis",
                    "results",
                    "findings",
                    "conclusion",
                    "discussion",
                    # Open science movement
                    "open access",
                    "open data",
                    "open source",
                    "collaboration",
                    "sharing",
                    "reproducibility",
                    "replication",
                    "transparency",
                ],
                domain_focus=["all"],
                content_type="preprint",
                temporal_coverage="recent",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.3,
                    "recency": 0.9,
                    "technical_depth": 0.6,
                    "accessibility": 0.9,
                },
            ),
        }

        # Start with built-in profiles for known sources
        for source_name, profile in builtin_profiles.items():
            profiles[source_name] = profile

        # Add profiles for any configured sources not in built-ins
        for source_name, source_config in configured_sources.items():
            if source_name not in profiles and getattr(source_config, "enabled", False):
                # Create dynamic profile for custom source
                profiles[source_name] = self._create_default_profile(
                    source_name, source_config
                )

        return profiles

    def get_source_profile(self, source_name: str) -> SourceProfile:
        """Get or create a profile for any source (supports runtime addition of custom sources)."""
        if source_name in self.source_profiles:
            return self.source_profiles[source_name]

        # If source not found, try to get from current config and create profile
        try:
            config = get_current_config()
            if config and source_name in config.sources:
                source_config = config.sources[source_name]
                if getattr(source_config, "enabled", False):
                    # Create and cache the profile
                    profile = self._create_default_profile(source_name, source_config)
                    self.source_profiles[source_name] = profile
                    return profile
        except Exception:
            pass

        # Ultimate fallback - create minimal profile
        fallback_profile = SourceProfile(
            name=source_name.title(),
            specialty_terms=[source_name.lower(), "research", "academic"],
            domain_focus=["general"],
            content_type="repository",
            temporal_coverage="comprehensive",
            access_type="mixed",
            quality_indicators={
                "peer_review": 0.5,
                "recency": 0.5,
                "technical_depth": 0.5,
                "accessibility": 0.5,
            },
        )
        self.source_profiles[source_name] = fallback_profile
        return fallback_profile

    def _initialize_bm25_index(self) -> None:
        """Initialize BM25 index using bm25s library (500x faster than rank-bm25)."""
        # Build corpus from source profiles
        # Each document is the tokenized specialty terms of a source
        self.source_names_ordered = list(self.source_profiles.keys())
        corpus_tokens = []

        for source_name in self.source_names_ordered:
            profile = self.source_profiles[source_name]
            # Tokenize all specialty terms for this source into a single document
            doc_tokens = []
            for specialty_term in profile.specialty_terms:
                tokens = self._tokenize_query(specialty_term)
                doc_tokens.extend(tokens)
            corpus_tokens.append(doc_tokens)

        # Initialize BM25S with custom parameters and index the corpus
        # Using method="lucene" for compatibility with academic search conventions
        self.bm25 = bm25s.BM25(k1=self.k1, b=self.b, method="lucene")
        self.bm25.index(corpus_tokens)

    def _tokenize_query(self, query: str) -> list[str]:
        """Tokenize and normalize query."""
        import re

        # Convert to lowercase and extract words
        query = query.lower()
        words = re.findall(r"\b[a-zA-Z]+\b", query)
        return [word for word in words if len(word) > 2]  # Filter short words

    def _calculate_bm25_score(self, query_terms: list[str], source_name: str) -> float:
        """Calculate BM25 score for a query against a source using bm25s."""
        if not query_terms:
            return 0.0

        # BM25S retrieve returns (results, scores) where:
        # - results: document indices sorted by score (shape: n_queries x k)
        # - scores: BM25 scores for those documents (shape: n_queries x k)
        # We request all documents to get scores for all sources
        results, scores = self.bm25.retrieve(
            query_terms, k=len(self.source_names_ordered)
        )

        # Find the score for this specific source by name
        try:
            source_idx = self.source_names_ordered.index(source_name)

            # BM25S returns arrays: results[0] has doc indices, scores[0] has their scores
            # We need to find where our source_idx appears in results[0]
            if len(results) > 0 and len(results[0]) > 0:
                # Find position of source_idx in the results array
                result_indices = results[0]
                for i, doc_idx in enumerate(result_indices):
                    if doc_idx == source_idx:
                        return float(scores[0][i])

            # Source not in results or no results
            return 0.0
        except (ValueError, IndexError):
            # Source not in index, return 0
            return 0.0

    def _apply_domain_boost(
        self, base_score: float, query_terms: list[str], source_profile: SourceProfile
    ) -> float:
        """Apply domain-specific boosts to the base BM25 score."""
        boost_factor = 1.0

        # Domain matching boost
        domain_keywords = {
            "stem": [
                "algorithm",
                "computation",
                "mathematical",
                "technical",
                "engineering",
            ],
            "medical": [
                "medical",
                "clinical",
                "disease",
                "treatment",
                "patient",
                "health",
            ],
            "historical": ["historical", "history", "ancient", "heritage", "archive"],
            "social_science": [
                "social",
                "society",
                "community",
                "culture",
                "political",
            ],
            "humanities": ["literature", "art", "philosophy", "cultural", "linguistic"],
            "biological": ["biology", "genetic", "organism", "species", "evolution"],
        }

        for domain in source_profile.domain_focus:
            if domain in domain_keywords:
                domain_matches = sum(
                    1 for term in query_terms if term in domain_keywords[domain]
                )
                if domain_matches > 0:
                    boost_factor += 0.2 * domain_matches

        # Content type boost
        content_boosts = {
            ("recent", "preprint"): 1.3,  # Recent queries prefer preprints
            ("review", "journal"): 1.2,  # Review queries prefer journals
            ("historical", "repository"): 1.3,  # Historical queries prefer repositories
            (
                "comprehensive",
                "aggregator",
            ): 1.1,  # Comprehensive queries prefer aggregators
        }

        query_str = " ".join(query_terms)
        for (query_type, content_type), boost in content_boosts.items():
            if query_type in query_str and source_profile.content_type == content_type:
                boost_factor += boost - 1.0

        # Quality boost based on indicators
        quality_score = sum(source_profile.quality_indicators.values()) / len(
            source_profile.quality_indicators
        )
        boost_factor += 0.1 * quality_score

        return base_score * boost_factor

    def _apply_temporal_adjustment(
        self, score: float, query_terms: list[str], source_profile: SourceProfile
    ) -> float:
        """Apply temporal preference adjustments."""
        query_str = " ".join(query_terms)

        # Recent preference indicators
        recent_indicators = [
            "recent",
            "latest",
            "new",
            "current",
            "2024",
            "2025",
            "emerging",
        ]
        historical_indicators = [
            "historical",
            "classic",
            "traditional",
            "foundational",
            "early",
        ]

        recent_matches = sum(
            1 for indicator in recent_indicators if indicator in query_str
        )
        historical_matches = sum(
            1 for indicator in historical_indicators if indicator in query_str
        )

        if recent_matches > 0 and source_profile.temporal_coverage == "recent":
            score *= 1.3
        elif (
            historical_matches > 0
            and source_profile.temporal_coverage == "comprehensive"
        ):
            score *= 1.2
        elif recent_matches > 0 and source_profile.temporal_coverage == "comprehensive":
            score *= 0.9  # Slight penalty for non-recent sources with recent queries

        return score

    def rank_sources(
        self, query: str, available_sources: list[str] | None = None
    ) -> list[tuple[str, float]]:
        """
        Rank sources based on BM25 relevance to the query.

        Args:
            query: The search query
            available_sources: List of available source names (if None, uses all)

        Returns:
            List of (source_name, score) tuples sorted by score (descending)
        """
        if available_sources is None:
            available_sources = list(self.source_profiles.keys())

        query_terms = self._tokenize_query(query)
        if not query_terms:
            # If no valid terms, return equal scores
            return [(source, 0.5) for source in available_sources]

        scored_sources = []

        for source_name in available_sources:
            # Use get_source_profile to handle unknown/custom sources
            profile = self.get_source_profile(source_name)

            # Calculate base BM25 score (pass source_name for indexing)
            base_score = self._calculate_bm25_score(query_terms, source_name)

            # Apply domain-specific boosts
            boosted_score = self._apply_domain_boost(base_score, query_terms, profile)

            # Apply temporal adjustments
            final_score = self._apply_temporal_adjustment(
                boosted_score, query_terms, profile
            )

            scored_sources.append((source_name, final_score))

        # Sort by score (descending)
        scored_sources.sort(key=lambda x: x[1], reverse=True)

        # Normalize scores to 0-1 range
        if scored_sources:
            max_score = max(score for _, score in scored_sources)
            if max_score > 0:
                scored_sources = [
                    (name, score / max_score) for name, score in scored_sources
                ]

        return scored_sources

    def get_source_recommendations(
        self, query: str, max_sources: int = 5
    ) -> dict[str, Any]:
        """
        Get comprehensive source recommendations with explanations.

        Args:
            query: The search query
            max_sources: Maximum number of sources to recommend

        Returns:
            Dictionary with recommendations and explanations
        """
        ranked_sources = self.rank_sources(query)
        top_sources = ranked_sources[:max_sources]

        recommendations = {
            "query": query,
            "top_sources": [
                {
                    "name": name,
                    "score": score,
                    "profile": {
                        "content_type": self.source_profiles[name].content_type,
                        "temporal_coverage": self.source_profiles[
                            name
                        ].temporal_coverage,
                        "access_type": self.source_profiles[name].access_type,
                        "domain_focus": self.source_profiles[name].domain_focus,
                    },
                }
                for name, score in top_sources
            ],
            "reasoning": self._explain_ranking(query, top_sources),
            "alternative_strategies": self._suggest_alternatives(query, ranked_sources),
        }

        return recommendations

    def _explain_ranking(
        self, query: str, top_sources: list[tuple[str, float]]
    ) -> dict[str, str]:
        """Explain why sources were ranked as they were."""
        explanations = {}
        query_terms = self._tokenize_query(query)

        for source_name, _score in top_sources:
            profile = self.source_profiles[source_name]

            explanation_parts = []

            # Domain match explanation
            matching_domains = [
                domain
                for domain in profile.domain_focus
                if any(term in profile.specialty_terms for term in query_terms)
            ]
            if matching_domains:
                explanation_parts.append(
                    f"Strong match for {', '.join(matching_domains)} domains"
                )

            # Content type explanation
            if profile.content_type == "preprint" and any(
                term in ["recent", "latest", "new"] for term in query_terms
            ):
                explanation_parts.append("Preprint source ideal for recent research")
            elif profile.content_type == "journal" and any(
                term in ["review", "comprehensive"] for term in query_terms
            ):
                explanation_parts.append(
                    "Journal source good for peer-reviewed content"
                )

            # Access type explanation
            if profile.access_type == "open":
                explanation_parts.append("Open access increases download likelihood")

            explanations[source_name] = (
                "; ".join(explanation_parts)
                if explanation_parts
                else "General relevance match"
            )

        return explanations

    def _suggest_alternatives(
        self, query: str, all_ranked: list[tuple[str, float]]
    ) -> list[dict[str, str]]:
        """Suggest alternative search strategies."""
        alternatives = []

        # If top scores are low, suggest query expansion
        if all_ranked and all_ranked[0][1] < 0.3:
            alternatives.append(
                {
                    "strategy": "query_expansion",
                    "description": "Consider adding domain-specific terms or synonyms to improve matching",
                }
            )

        # If preprint sources rank high, suggest also searching journals
        preprint_sources = ["arxiv", "socarxiv", "osf_preprints"]
        top_names = [name for name, _ in all_ranked[:3]]

        if any(name in preprint_sources for name in top_names):
            alternatives.append(
                {
                    "strategy": "include_journals",
                    "description": "Also search established journals for peer-reviewed versions",
                }
            )

        # If only general sources rank high, suggest domain-specific sources
        general_sources = ["crossref"]
        if all(name in general_sources for name in top_names[:2]):
            alternatives.append(
                {
                    "strategy": "try_specialized",
                    "description": "Consider domain-specific repositories for more targeted results",
                }
            )

        return alternatives


# Convenience functions
def rank_sources_bm25(
    query: str, available_sources: list[str] | None = None
) -> list[tuple[str, float]]:
    """Rank sources using BM25 algorithm."""
    ranker = BM25SourceRanker()
    return ranker.rank_sources(query, available_sources)


def get_bm25_recommendations(query: str, max_sources: int = 5) -> dict[str, Any]:
    """Get BM25-based source recommendations."""
    ranker = BM25SourceRanker()
    return ranker.get_source_recommendations(query, max_sources)
