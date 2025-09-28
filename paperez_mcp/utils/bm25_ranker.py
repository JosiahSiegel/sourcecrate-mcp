"""
BM25-based source ranking for intelligent source selection.
Uses BM25 algorithm to rank academic sources based on query relevance.
"""

import math
from collections import Counter
from dataclasses import dataclass


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

    def __init__(self):
        self.source_profiles = self._build_source_profiles()
        self.idf_cache = {}
        self.k1 = 1.2  # Term frequency saturation parameter
        self.b = 0.75  # Document length normalization parameter
        self._compute_idf_scores()

    def _build_source_profiles(self) -> dict[str, SourceProfile]:
        """Build profiles for each academic source."""
        return {
            "arxiv": SourceProfile(
                name="arXiv",
                specialty_terms=[
                    # Computer Science
                    "algorithm", "machine learning", "neural network", "deep learning",
                    "artificial intelligence", "computer vision", "natural language processing",
                    "data mining", "software engineering", "distributed systems",
                    "cryptography", "computational complexity", "programming languages",

                    # Physics
                    "quantum mechanics", "particle physics", "astrophysics", "cosmology",
                    "condensed matter", "statistical mechanics", "relativity", "optics",
                    "plasma physics", "nuclear physics", "theoretical physics",

                    # Mathematics
                    "algebra", "topology", "analysis", "geometry", "number theory",
                    "combinatorics", "probability", "statistics", "optimization",
                    "differential equations", "mathematical physics",

                    # Preprint indicators
                    "preprint", "preliminary", "draft", "working paper", "submitted",
                    "under review", "recent", "latest", "new", "novel", "emerging"
                ],
                domain_focus=["stem", "computer_science", "physics", "mathematics"],
                content_type="preprint",
                temporal_coverage="recent",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.3,  # Not peer-reviewed
                    "recency": 0.9,      # Very recent
                    "technical_depth": 0.8,
                    "accessibility": 0.9
                }
            ),

            "semantic_scholar": SourceProfile(
                name="Semantic Scholar",
                specialty_terms=[
                    # Broad academic coverage
                    "research", "study", "analysis", "paper", "article", "publication",
                    "citation", "bibliography", "author", "conference", "journal",
                    "peer review", "methodology", "experiment", "data", "results",

                    # AI/CS focus
                    "artificial intelligence", "machine learning", "computer science",
                    "natural language processing", "computer vision", "robotics",
                    "human-computer interaction", "information retrieval",

                    # Cross-disciplinary
                    "interdisciplinary", "multidisciplinary", "collaboration",
                    "citation network", "impact factor", "h-index"
                ],
                domain_focus=["stem", "social_science", "medical", "general"],
                content_type="aggregator",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.8,
                    "recency": 0.7,
                    "technical_depth": 0.7,
                    "accessibility": 0.8
                }
            ),

            "crossref": SourceProfile(
                name="CrossRef",
                specialty_terms=[
                    # Formal publication terms
                    "journal", "article", "publication", "peer review", "publisher",
                    "doi", "citation", "reference", "bibliography", "academic",
                    "scholarly", "research", "study", "analysis", "methodology",
                    "experiment", "results", "conclusion", "abstract", "introduction",

                    # All academic domains (broad)
                    "science", "technology", "medicine", "humanities", "social science",
                    "engineering", "mathematics", "physics", "chemistry", "biology",
                    "psychology", "sociology", "economics", "political science",
                    "philosophy", "literature", "history", "art", "music"
                ],
                domain_focus=["all"],
                content_type="journal",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.6,
                    "technical_depth": 0.8,
                    "accessibility": 0.5
                }
            ),

            "pubmed": SourceProfile(
                name="PubMed",
                specialty_terms=[
                    # Medical/Biomedical
                    "medicine", "medical", "clinical", "patient", "disease", "treatment",
                    "therapy", "drug", "pharmaceutical", "healthcare", "hospital",
                    "diagnosis", "symptom", "syndrome", "pathology", "epidemiology",
                    "public health", "preventive medicine", "emergency medicine",

                    # Biological
                    "biology", "biomedical", "biochemistry", "molecular biology",
                    "cell biology", "genetics", "genomics", "proteomics", "bioinformatics",
                    "neuroscience", "immunology", "microbiology", "virology",
                    "anatomy", "physiology", "pharmacology", "toxicology",

                    # Research types
                    "clinical trial", "randomized controlled", "case study",
                    "cohort study", "meta-analysis", "systematic review"
                ],
                domain_focus=["medical", "biological"],
                content_type="journal",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.7,
                    "technical_depth": 0.9,
                    "accessibility": 0.6
                }
            ),

            "pubmed_central": SourceProfile(
                name="PubMed Central",
                specialty_terms=[
                    # Medical/Biomedical with full-text focus
                    "medicine", "medical", "clinical", "patient", "disease", "treatment",
                    "therapy", "drug", "pharmaceutical", "healthcare", "hospital",
                    "diagnosis", "symptom", "syndrome", "pathology", "epidemiology",
                    "public health", "preventive medicine", "emergency medicine",
                    # Biological
                    "biology", "biomedical", "biochemistry", "molecular biology",
                    "cell biology", "genetics", "genomics", "proteomics", "bioinformatics",
                    "neuroscience", "immunology", "microbiology", "virology",
                    "anatomy", "physiology", "pharmacology", "toxicology",
                    # Full-text specific terms
                    "full text", "open access", "pmc", "full paper", "complete text",
                    "detailed analysis", "comprehensive study", "in-depth research",
                    # Research types
                    "clinical trial", "randomized controlled", "case study",
                    "cohort study", "meta-analysis", "systematic review"
                ],
                domain_focus=["medical", "biological"],
                content_type="repository",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.7,
                    "technical_depth": 0.9,
                    "accessibility": 0.9  # Higher than PubMed due to open access
                }
            ),

            "clinicaltrials": SourceProfile(
                name="ClinicalTrials.gov",
                specialty_terms=[
                    # Clinical trial specific
                    "clinical trial", "trial", "study", "protocol", "intervention",
                    "randomized", "controlled", "blinded", "placebo", "treatment arm",
                    "primary endpoint", "secondary endpoint", "efficacy", "safety",
                    "adverse event", "side effect", "dosage", "dose", "administration",
                    # Medical conditions
                    "disease", "disorder", "condition", "syndrome", "cancer", "diabetes",
                    "hypertension", "depression", "alzheimer", "parkinson", "stroke",
                    "heart disease", "kidney disease", "liver disease", "lung disease",
                    # Treatment types
                    "drug", "medication", "therapy", "treatment", "pharmaceutical",
                    "vaccine", "immunotherapy", "chemotherapy", "surgery", "device",
                    "behavioral intervention", "dietary intervention", "exercise",
                    # Trial phases and status
                    "phase 1", "phase 2", "phase 3", "phase 4", "recruiting",
                    "active", "completed", "terminated", "withdrawn", "enrolling",
                    # Regulatory
                    "fda", "approval", "regulatory", "investigational", "experimental"
                ],
                domain_focus=["medical", "clinical"],
                content_type="repository",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.7,  # Protocols, not peer-reviewed papers
                    "recency": 0.8,      # Often current trials
                    "technical_depth": 0.8,
                    "accessibility": 0.9  # Public access
                }
            ),

            "google_scholar": SourceProfile(
                name="Google Scholar",
                specialty_terms=[
                    # General academic
                    "research", "study", "analysis", "paper", "thesis", "dissertation",
                    "conference", "workshop", "symposium", "proceedings", "book",
                    "chapter", "report", "working paper", "technical report",

                    # Broad coverage indicators
                    "academic", "scholarly", "university", "institution", "faculty",
                    "professor", "researcher", "student", "graduate", "undergraduate",

                    # Citation and impact
                    "citation", "cited", "reference", "bibliography", "impact",
                    "influence", "significance", "contribution", "innovation",

                    # Historical documents (comprehensive coverage)
                    "declaration", "treaty", "historical", "history", "document",
                    "archive", "primary source", "manuscript", "diplomatic",
                    "government", "official", "colonial", "political",

                    # Economic and financial topics
                    "banking", "federal reserve", "economics", "finance", "monetary",
                    "business", "corporate", "financial", "economic", "money"
                ],
                domain_focus=["all"],
                content_type="aggregator",
                temporal_coverage="comprehensive",
                access_type="mixed",
                quality_indicators={
                    "peer_review": 0.6,  # Mixed quality
                    "recency": 0.7,
                    "technical_depth": 0.6,
                    "accessibility": 0.8
                }
            ),

            "core": SourceProfile(
                name="CORE",
                specialty_terms=[
                    # Open access focus
                    "open access", "repository", "institutional", "archive",
                    "digital library", "collection", "preservation", "metadata",

                    # Humanities/Social Sciences
                    "humanities", "social science", "history", "literature",
                    "philosophy", "art", "culture", "society", "politics",
                    "economics", "anthropology", "sociology", "psychology",

                    # Historical document types
                    "declaration", "treaty", "proclamation", "manifesto", "charter",
                    "constitution", "agreement", "protocol", "memorandum", "correspondence",
                    "letter", "diplomatic", "government document", "official document",
                    "policy document", "legal document", "historic document",

                    # Historical periods and events
                    "colonial", "empire", "independence", "revolution", "war",
                    "conflict", "peace", "settlement", "mandate", "territory",
                    "nationalism", "sovereignty", "diplomacy", "international relations",
                    "british", "ottoman", "palestine", "zionism", "middle east",

                    # Economic and financial history
                    "banking", "federal reserve", "central bank", "monetary", "finance",
                    "economic", "financial", "capitalism", "business", "corporate",
                    "wall street", "investment", "securities", "bonds", "stock market",
                    "depression", "recession", "panic", "crisis", "bubble",
                    "morgan", "rockefeller", "rothschild", "warburg", "aldrich",
                    "jekyll island", "money trust", "banking reform", "currency",

                    # Historical/Cultural
                    "historical", "cultural", "heritage", "tradition", "civilization",
                    "archive", "manuscript", "document", "primary source",
                    "secondary source", "archaeological", "ethnographic"
                ],
                domain_focus=["humanities", "social_science", "historical"],
                content_type="repository",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.7,
                    "recency": 0.5,
                    "technical_depth": 0.6,
                    "accessibility": 0.9
                }
            ),

            "doaj": SourceProfile(
                name="DOAJ",
                specialty_terms=[
                    # Open access journals
                    "open access", "journal", "peer review", "editorial", "publication",
                    "scholarly", "academic", "research", "article", "paper",

                    # Quality indicators
                    "peer reviewed", "editorial board", "impact factor", "indexing",
                    "citation", "quality", "standards", "ethics", "transparency",

                    # Diverse fields
                    "interdisciplinary", "multidisciplinary", "cross-disciplinary",
                    "international", "global", "regional", "specialized"
                ],
                domain_focus=["all"],
                content_type="journal",
                temporal_coverage="comprehensive",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.9,
                    "recency": 0.6,
                    "technical_depth": 0.7,
                    "accessibility": 0.9
                }
            ),

            "socarxiv": SourceProfile(
                name="SocArXiv",
                specialty_terms=[
                    # Social Sciences
                    "social science", "sociology", "anthropology", "political science",
                    "economics", "psychology", "social psychology", "cognitive science",
                    "communication", "media studies", "cultural studies", "gender studies",

                    # Social phenomena
                    "society", "community", "culture", "identity", "behavior",
                    "social network", "social media", "public opinion", "survey",
                    "interview", "ethnography", "qualitative", "quantitative",

                    # Preprint characteristics
                    "preprint", "working paper", "draft", "preliminary", "submitted"
                ],
                domain_focus=["social_science"],
                content_type="preprint",
                temporal_coverage="recent",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.3,
                    "recency": 0.9,
                    "technical_depth": 0.6,
                    "accessibility": 0.8
                }
            ),

            "osf_preprints": SourceProfile(
                name="OSF Preprints",
                specialty_terms=[
                    # General preprint terms
                    "preprint", "working paper", "draft", "preliminary", "under review",
                    "submitted", "open science", "reproducible research", "transparency",

                    # Broad academic coverage
                    "research", "study", "experiment", "data", "methodology",
                    "analysis", "results", "findings", "conclusion", "discussion",

                    # Open science movement
                    "open access", "open data", "open source", "collaboration",
                    "sharing", "reproducibility", "replication", "transparency"
                ],
                domain_focus=["all"],
                content_type="preprint",
                temporal_coverage="recent",
                access_type="open",
                quality_indicators={
                    "peer_review": 0.3,
                    "recency": 0.9,
                    "technical_depth": 0.6,
                    "accessibility": 0.9
                }
            )
        }

    def _compute_idf_scores(self):
        """Pre-compute IDF scores for all terms across sources."""
        # Collect all terms from all sources (tokenize specialty terms)
        all_terms = set()
        for profile in self.source_profiles.values():
            for specialty_term in profile.specialty_terms:
                # Tokenize each specialty term to get individual words
                words = self._tokenize_query(specialty_term)
                all_terms.update(words)

        # Calculate IDF for each term
        total_sources = len(self.source_profiles)

        for term in all_terms:
            # Count sources containing this term (check within specialty term strings)
            sources_with_term = sum(
                1 for profile in self.source_profiles.values()
                if any(term in specialty_term.lower() for specialty_term in profile.specialty_terms)
            )

            # Calculate IDF
            idf = math.log((total_sources - sources_with_term + 0.5) / (sources_with_term + 0.5))
            self.idf_cache[term] = max(0.0, idf)  # Ensure non-negative

    def _tokenize_query(self, query: str) -> list[str]:
        """Tokenize and normalize query."""
        import re
        # Convert to lowercase and extract words
        query = query.lower()
        words = re.findall(r'\b[a-zA-Z]+\b', query)
        return [word for word in words if len(word) > 2]  # Filter short words

    def _calculate_bm25_score(self, query_terms: list[str], source_profile: SourceProfile) -> float:
        """Calculate BM25 score for a query against a source profile."""
        source_terms = [term.lower() for term in source_profile.specialty_terms]
        source_length = len(source_terms)

        # Calculate average document length across all sources
        avg_length = sum(len(profile.specialty_terms) for profile in self.source_profiles.values()) / len(self.source_profiles)

        score = 0.0
        query_term_counts = Counter(query_terms)

        for term, _query_tf in query_term_counts.items():
            # Calculate term frequency in source (count occurrences in all specialty terms)
            source_tf = sum(source_term.count(term) for source_term in source_terms)

            if source_tf > 0:

                # Get IDF score
                idf = self.idf_cache.get(term, 0.0)

                # BM25 calculation
                numerator = source_tf * (self.k1 + 1)
                denominator = source_tf + self.k1 * (1 - self.b + self.b * (source_length / avg_length))

                score += idf * (numerator / denominator)

        return score

    def _apply_domain_boost(self, base_score: float, query_terms: list[str], source_profile: SourceProfile) -> float:
        """Apply domain-specific boosts to the base BM25 score."""
        boost_factor = 1.0

        # Domain matching boost
        domain_keywords = {
            "stem": ["algorithm", "computation", "mathematical", "technical", "engineering"],
            "medical": ["medical", "clinical", "disease", "treatment", "patient", "health"],
            "historical": ["historical", "history", "ancient", "heritage", "archive"],
            "social_science": ["social", "society", "community", "culture", "political"],
            "humanities": ["literature", "art", "philosophy", "cultural", "linguistic"],
            "biological": ["biology", "genetic", "organism", "species", "evolution"]
        }

        for domain in source_profile.domain_focus:
            if domain in domain_keywords:
                domain_matches = sum(1 for term in query_terms if term in domain_keywords[domain])
                if domain_matches > 0:
                    boost_factor += 0.2 * domain_matches

        # Content type boost
        content_boosts = {
            ("recent", "preprint"): 1.3,      # Recent queries prefer preprints
            ("review", "journal"): 1.2,       # Review queries prefer journals
            ("historical", "repository"): 1.3, # Historical queries prefer repositories
            ("comprehensive", "aggregator"): 1.1 # Comprehensive queries prefer aggregators
        }

        query_str = " ".join(query_terms)
        for (query_type, content_type), boost in content_boosts.items():
            if query_type in query_str and source_profile.content_type == content_type:
                boost_factor += (boost - 1.0)

        # Quality boost based on indicators
        quality_score = sum(source_profile.quality_indicators.values()) / len(source_profile.quality_indicators)
        boost_factor += 0.1 * quality_score

        return base_score * boost_factor

    def _apply_temporal_adjustment(self, score: float, query_terms: list[str], source_profile: SourceProfile) -> float:
        """Apply temporal preference adjustments."""
        query_str = " ".join(query_terms)

        # Recent preference indicators
        recent_indicators = ["recent", "latest", "new", "current", "2024", "2025", "emerging"]
        historical_indicators = ["historical", "classic", "traditional", "foundational", "early"]

        recent_matches = sum(1 for indicator in recent_indicators if indicator in query_str)
        historical_matches = sum(1 for indicator in historical_indicators if indicator in query_str)

        if recent_matches > 0 and source_profile.temporal_coverage == "recent":
            score *= 1.3
        elif historical_matches > 0 and source_profile.temporal_coverage == "comprehensive":
            score *= 1.2
        elif recent_matches > 0 and source_profile.temporal_coverage == "comprehensive":
            score *= 0.9  # Slight penalty for non-recent sources with recent queries

        return score

    def rank_sources(self, query: str, available_sources: list[str] = None) -> list[tuple[str, float]]:
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
            if source_name not in self.source_profiles:
                continue

            profile = self.source_profiles[source_name]

            # Calculate base BM25 score
            base_score = self._calculate_bm25_score(query_terms, profile)

            # Apply domain-specific boosts
            boosted_score = self._apply_domain_boost(base_score, query_terms, profile)

            # Apply temporal adjustments
            final_score = self._apply_temporal_adjustment(boosted_score, query_terms, profile)

            scored_sources.append((source_name, final_score))

        # Sort by score (descending)
        scored_sources.sort(key=lambda x: x[1], reverse=True)

        # Normalize scores to 0-1 range
        if scored_sources:
            max_score = max(score for _, score in scored_sources)
            if max_score > 0:
                scored_sources = [(name, score/max_score) for name, score in scored_sources]

        return scored_sources

    def get_source_recommendations(self, query: str, max_sources: int = 5) -> dict[str, any]:
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
                        "temporal_coverage": self.source_profiles[name].temporal_coverage,
                        "access_type": self.source_profiles[name].access_type,
                        "domain_focus": self.source_profiles[name].domain_focus
                    }
                }
                for name, score in top_sources
            ],
            "reasoning": self._explain_ranking(query, top_sources),
            "alternative_strategies": self._suggest_alternatives(query, ranked_sources)
        }

        return recommendations

    def _explain_ranking(self, query: str, top_sources: list[tuple[str, float]]) -> dict[str, str]:
        """Explain why sources were ranked as they were."""
        explanations = {}
        query_terms = self._tokenize_query(query)

        for source_name, _score in top_sources:
            profile = self.source_profiles[source_name]

            explanation_parts = []

            # Domain match explanation
            matching_domains = [domain for domain in profile.domain_focus
                              if any(term in profile.specialty_terms for term in query_terms)]
            if matching_domains:
                explanation_parts.append(f"Strong match for {', '.join(matching_domains)} domains")

            # Content type explanation
            if profile.content_type == "preprint" and any(term in ["recent", "latest", "new"] for term in query_terms):
                explanation_parts.append("Preprint source ideal for recent research")
            elif profile.content_type == "journal" and any(term in ["review", "comprehensive"] for term in query_terms):
                explanation_parts.append("Journal source good for peer-reviewed content")

            # Access type explanation
            if profile.access_type == "open":
                explanation_parts.append("Open access increases download likelihood")

            explanations[source_name] = "; ".join(explanation_parts) if explanation_parts else "General relevance match"

        return explanations

    def _suggest_alternatives(self, query: str, all_ranked: list[tuple[str, float]]) -> list[dict[str, str]]:
        """Suggest alternative search strategies."""
        alternatives = []

        # If top scores are low, suggest query expansion
        if all_ranked and all_ranked[0][1] < 0.3:
            alternatives.append({
                "strategy": "query_expansion",
                "description": "Consider adding domain-specific terms or synonyms to improve matching"
            })

        # If preprint sources rank high, suggest also searching journals
        preprint_sources = ["arxiv", "socarxiv", "osf_preprints"]
        top_names = [name for name, _ in all_ranked[:3]]

        if any(name in preprint_sources for name in top_names):
            alternatives.append({
                "strategy": "include_journals",
                "description": "Also search established journals for peer-reviewed versions"
            })

        # If only general sources rank high, suggest domain-specific sources
        general_sources = ["google_scholar", "crossref"]
        if all(name in general_sources for name in top_names[:2]):
            alternatives.append({
                "strategy": "try_specialized",
                "description": "Consider domain-specific repositories for more targeted results"
            })

        return alternatives

# Convenience functions
def rank_sources_bm25(query: str, available_sources: list[str] = None) -> list[tuple[str, float]]:
    """Rank sources using BM25 algorithm."""
    ranker = BM25SourceRanker()
    return ranker.rank_sources(query, available_sources)


def get_bm25_recommendations(query: str, max_sources: int = 5) -> dict[str, any]:
    """Get BM25-based source recommendations."""
    ranker = BM25SourceRanker()
    return ranker.get_source_recommendations(query, max_sources)
