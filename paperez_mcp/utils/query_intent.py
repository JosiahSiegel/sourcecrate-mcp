"""
Query intent detection for academic search optimization.
Uses pattern matching and statistical analysis to understand user intent.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class QueryIntent(Enum):
    """Enumeration of query intent types."""

    SURVEY_REVIEW = "survey_review"
    RECENT_RESEARCH = "recent_research"
    HISTORICAL_FOUNDATIONAL = "historical_foundational"
    APPLIED_PRACTICAL = "applied_practical"
    THEORETICAL = "theoretical"
    COMPARATIVE = "comparative"
    TUTORIAL_EDUCATIONAL = "tutorial_educational"
    EMPIRICAL_EXPERIMENTAL = "empirical_experimental"
    GENERAL = "general"


class TemporalPreference(Enum):
    """Enumeration of temporal preferences."""

    RECENT = "recent"  # Last 1-3 years
    CURRENT = "current"  # Last 5 years
    HISTORICAL = "historical"  # Older, foundational
    NEUTRAL = "neutral"  # No preference


@dataclass
class QueryAnalysis:
    """Result of query intent analysis."""

    intent: QueryIntent
    temporal_preference: TemporalPreference
    confidence: float
    complexity: str  # simple, phrase, complex, boolean
    keywords: list[str]
    phrases: list[str]
    academic_indicators: list[str]
    source_preferences: dict[str, float]


class QueryIntentDetector:
    """Detect query intent using pattern matching and statistical analysis."""

    def __init__(self) -> None:
        self.intent_patterns = self._build_intent_patterns()
        self.temporal_patterns = self._build_temporal_patterns()
        self.academic_indicators = self._build_academic_indicators()
        self.complexity_thresholds = {
            "simple": 2,  # 1-2 words
            "phrase": 5,  # 3-5 words
            "complex": 15,  # 6-15 words
            "boolean": 100,  # >15 words or boolean operators
        }

    def _build_intent_patterns(self) -> dict[QueryIntent, dict[str, list[str]]]:
        """Build patterns for intent detection."""
        return {
            QueryIntent.SURVEY_REVIEW: {
                "keywords": [
                    "review",
                    "survey",
                    "overview",
                    "summary",
                    "state of the art",
                    "comprehensive",
                    "systematic review",
                    "meta-analysis",
                    "literature review",
                    "scoping review",
                    "narrative review",
                ],
                "patterns": [
                    r"\b(systematic|comprehensive|scoping|narrative)\s+review\b",
                    r"\bstate\s+of\s+the\s+art\b",
                    r"\bmeta[-\s]analysis\b",
                    r"\bliterature\s+survey\b",
                    r"\brecent\s+(advances|developments|progress)\b",
                ],
            },
            QueryIntent.RECENT_RESEARCH: {
                "keywords": [
                    "recent",
                    "latest",
                    "new",
                    "current",
                    "emerging",
                    "novel",
                    "cutting-edge",
                    "state-of-the-art",
                    "breakthrough",
                    "2023",
                    "2024",
                    "2025",
                    "advances",
                    "developments",
                ],
                "patterns": [
                    r"\b(recent|latest|new|current|emerging)\s+(research|work|study|advances)\b",
                    r"\b(2023|2024|2025)\b",
                    r"\bcutting[-\s]edge\b",
                    r"\bstate[-\s]of[-\s]the[-\s]art\b",
                    r"\bemerging\s+trends\b",
                ],
            },
            QueryIntent.HISTORICAL_FOUNDATIONAL: {
                "keywords": [
                    "history",
                    "historical",
                    "origin",
                    "evolution",
                    "development",
                    "foundation",
                    "foundational",
                    "classic",
                    "seminal",
                    "early",
                    "traditional",
                    "original",
                    "pioneering",
                ],
                "patterns": [
                    r"\bhistory\s+of\b",
                    r"\bevolution\s+of\b",
                    r"\bdevelopment\s+of\b",
                    r"\b(foundational|seminal|classic|pioneering)\s+(work|paper|study)\b",
                    r"\b(early|original)\s+(research|work)\b",
                ],
            },
            QueryIntent.APPLIED_PRACTICAL: {
                "keywords": [
                    "application",
                    "implementation",
                    "practical",
                    "real-world",
                    "case study",
                    "deployment",
                    "industry",
                    "commercial",
                    "production",
                    "use case",
                    "applied",
                    "experimental",
                ],
                "patterns": [
                    r"\b(practical|real[-\s]world)\s+(application|implementation)\b",
                    r"\bcase\s+study\b",
                    r"\bindustry\s+(application|use)\b",
                    r"\bproduction\s+(deployment|system)\b",
                    r"\bapplied\s+(research|study)\b",
                ],
            },
            QueryIntent.THEORETICAL: {
                "keywords": [
                    "theory",
                    "theoretical",
                    "model",
                    "framework",
                    "formalization",
                    "mathematical",
                    "formal",
                    "abstract",
                    "conceptual",
                    "principle",
                    "foundation",
                    "axiom",
                    "theorem",
                ],
                "patterns": [
                    r"\b(theoretical|mathematical)\s+(framework|model|foundation)\b",
                    r"\b(formal|abstract)\s+(model|theory)\b",
                    r"\bconceptual\s+framework\b",
                    r"\b(principle|axiom|theorem)\b",
                ],
            },
            QueryIntent.COMPARATIVE: {
                "keywords": [
                    "comparison",
                    "compare",
                    "versus",
                    "vs",
                    "comparative",
                    "benchmark",
                    "evaluation",
                    "analysis",
                    "performance",
                    "difference",
                    "similarity",
                    "contrast",
                ],
                "patterns": [
                    r"\b(comparison|compare|comparative)\s+(study|analysis)\b",
                    r"\bvs\b|\bversus\b",
                    r"\bbenchmark\s+(analysis|study)\b",
                    r"\bperformance\s+(comparison|evaluation)\b",
                    r"\b(difference|similarity)\s+between\b",
                ],
            },
            QueryIntent.TUTORIAL_EDUCATIONAL: {
                "keywords": [
                    "tutorial",
                    "introduction",
                    "beginner",
                    "guide",
                    "howto",
                    "learning",
                    "educational",
                    "teaching",
                    "course",
                    "primer",
                    "basics",
                    "fundamentals",
                    "getting started",
                ],
                "patterns": [
                    r"\b(introduction|beginner)\s+(guide|tutorial)\b",
                    r"\bhow\s+to\b",
                    r"\b(getting\s+started|basics|fundamentals)\b",
                    r"\b(learning|educational)\s+(material|resource)\b",
                ],
            },
            QueryIntent.EMPIRICAL_EXPERIMENTAL: {
                "keywords": [
                    "experiment",
                    "experimental",
                    "empirical",
                    "study",
                    "trial",
                    "test",
                    "validation",
                    "evaluation",
                    "measurement",
                    "observation",
                    "data",
                    "results",
                ],
                "patterns": [
                    r"\b(experimental|empirical)\s+(study|research|analysis)\b",
                    r"\b(controlled|randomized)\s+(trial|experiment)\b",
                    r"\bvalidation\s+study\b",
                    r"\b(measurement|observation)\s+(study|data)\b",
                ],
            },
        }

    def _build_temporal_patterns(
        self,
    ) -> dict[TemporalPreference, dict[str, list[str]]]:
        """Build patterns for temporal preference detection."""
        return {
            TemporalPreference.RECENT: {
                "keywords": [
                    "recent",
                    "latest",
                    "new",
                    "2024",
                    "2025",
                    "current",
                    "emerging",
                    "cutting-edge",
                    "breakthrough",
                    "novel",
                    "advancing",
                    "ongoing",
                ],
                "patterns": [
                    r"\b(recent|latest|new)\s+(research|work|study|advances|developments|findings)\b",
                    r"\b(2024|2025)\b",
                    r"\bcurrent\s+(research|work|study|trends|developments)\b",
                    r"\bup[-\s]to[-\s]date\b",
                    r"\bemerging\s+(trends|technologies|methods|approaches)\b",
                    r"\bcutting[-\s]edge\s+(research|technology|methods)\b",
                    r"\bbreakthrough\s+(research|discoveries|findings)\b",
                    r"\blatest\s+(advances|developments|progress|findings)\b",
                    r"\bin\s+the\s+last\s+(year|two\s+years|few\s+years)\b",
                    r"\bthis\s+year\s+(research|work|study)\b",
                ],
            },
            TemporalPreference.CURRENT: {
                "keywords": [
                    "current",
                    "contemporary",
                    "modern",
                    "2020",
                    "2021",
                    "2022",
                    "2023",
                    "present",
                    "today",
                    "nowadays",
                    "currently",
                ],
                "patterns": [
                    r"\b(current|contemporary|modern|present)\s+(research|work|study|approaches)\b",
                    r"\b(2020|2021|2022|2023)\b",
                    r"\bpast\s+(few|several|5|five)\s+years\b",
                    r"\brecent\s+(5|five|several)\s+years\b",
                    r"\btoday\'?s\s+(research|technology|methods)\b",
                    r"\bcurrently\s+(available|used|developed)\b",
                    r"\bnowadays\b",
                    r"\bsince\s+(2020|2021|2022)\b",
                    r"\bin\s+recent\s+years\b",
                ],
            },
            TemporalPreference.HISTORICAL: {
                "keywords": [
                    "historical",
                    "classic",
                    "traditional",
                    "foundational",
                    "early",
                    "original",
                    "seminal",
                    "pioneering",
                    "legacy",
                    "vintage",
                    "old",
                    "ancient",
                    "genesis",
                    "origins",
                    "birth",
                    "inception",
                    "roots",
                ],
                "patterns": [
                    r"\bhistory\s+of\b",
                    r"\bevolution\s+of\b",
                    r"\bdevelopment\s+of\b",
                    r"\borigins?\s+of\b",
                    r"\bgenesis\s+of\b",
                    r"\binception\s+of\b",
                    r"\broots\s+of\b",
                    r"\b(foundational|seminal|classic|pioneering|landmark)\s+(work|paper|study|research)\b",
                    r"\b(early|original|initial)\s+(research|development|work|studies)\b",
                    r"\b(historical|classic|traditional)\s+(approach|method|theory|work)\b",
                    r"\bfrom\s+the\s+(beginning|start|early\s+days)\b",
                    r"\blegacy\s+(systems|methods|approaches)\b",
                    r"\b(before|prior\s+to)\s+(2000|2010|2015)\b",
                    r"\bold\s+(methods|approaches|techniques|studies)\b",
                    r"\bvintage\s+(research|work|studies)\b",
                ],
            },
        }

    def _build_academic_indicators(self) -> dict[str, list[str]]:
        """Build academic language indicators."""
        return {
            "methodology": [
                "method",
                "methodology",
                "approach",
                "technique",
                "procedure",
                "algorithm",
                "protocol",
                "framework",
                "model",
                "system",
            ],
            "research_type": [
                "study",
                "research",
                "investigation",
                "analysis",
                "examination",
                "evaluation",
                "assessment",
                "survey",
                "review",
                "experiment",
            ],
            "academic_domains": [
                "computer science",
                "machine learning",
                "artificial intelligence",
                "biology",
                "physics",
                "chemistry",
                "medicine",
                "psychology",
                "sociology",
                "economics",
                "mathematics",
                "engineering",
            ],
            "publication_types": [
                "paper",
                "article",
                "journal",
                "conference",
                "publication",
                "manuscript",
                "thesis",
                "dissertation",
                "report",
                "book",
            ],
        }

    def _detect_complexity(self, query: str) -> str:
        """Determine query complexity."""
        # Check for boolean operators
        boolean_operators = ["AND", "OR", "NOT", "+", "-", '"']
        if any(op in query.upper() for op in boolean_operators):
            return "boolean"

        # Count words
        words = len(query.split())

        if words <= self.complexity_thresholds["simple"]:
            return "simple"
        elif words <= self.complexity_thresholds["phrase"]:
            return "phrase"
        elif words <= self.complexity_thresholds["complex"]:
            return "complex"
        else:
            return "boolean"  # Very long queries treated as boolean

    def _extract_patterns(self, query: str, patterns: list[str]) -> int:
        """Count pattern matches in query."""
        query_lower = query.lower()
        matches = 0

        for pattern in patterns:
            if re.search(pattern, query_lower):
                matches += 1

        return matches

    def _extract_keywords(self, query: str, keywords: list[str]) -> int:
        """Count keyword matches in query."""
        query_lower = query.lower()
        matches = 0

        for keyword in keywords:
            if keyword.lower() in query_lower:
                matches += 1

        return matches

    def _calculate_intent_scores(self, query: str) -> dict[QueryIntent, float]:
        """Calculate confidence scores for each intent."""
        scores = {}

        for intent, patterns in self.intent_patterns.items():
            keyword_matches = self._extract_keywords(query, patterns["keywords"])
            pattern_matches = self._extract_patterns(query, patterns["patterns"])

            # Weight pattern matches higher than keyword matches
            score = (pattern_matches * 2.0 + keyword_matches) / (
                len(patterns["patterns"]) * 2.0 + len(patterns["keywords"])
            )
            scores[intent] = min(score, 1.0)  # Cap at 1.0

        return scores

    def _calculate_temporal_scores(self, query: str) -> dict[TemporalPreference, float]:
        """Calculate confidence scores for temporal preferences."""
        scores = {}

        for temporal, patterns in self.temporal_patterns.items():
            keyword_matches = self._extract_keywords(query, patterns["keywords"])
            pattern_matches = self._extract_patterns(query, patterns["patterns"])

            score = (pattern_matches * 2.0 + keyword_matches) / (
                len(patterns["patterns"]) * 2.0 + len(patterns["keywords"])
            )
            scores[temporal] = min(score, 1.0)

        return scores

    def _get_source_preferences(
        self, intent: QueryIntent, temporal: TemporalPreference
    ) -> dict[str, float]:
        """Get source preferences based on intent and temporal preference."""
        # Get all available sources from configuration
        preferences = self._get_base_source_preferences()
        if not preferences:
            # Ultimate fallback if no configuration available
            preferences = {
                "arxiv": 0.5,
                "semantic_scholar": 0.6,
                "crossref": 0.5,
                "pubmed": 0.3,
                "core": 0.4,
                "doaj": 0.4,
            }

        # Adjust based on intent
        if intent == QueryIntent.SURVEY_REVIEW:
            preferences.update(
                {
                    "semantic_scholar": 0.9,  # Good for reviews
                    "crossref": 0.8,  # Comprehensive journals
                    "core": 0.7,  # Open access reviews
                    "arxiv": 0.6,  # Preprint reviews
                }
            )
        elif intent == QueryIntent.RECENT_RESEARCH:
            preferences.update(
                {
                    "arxiv": 0.9,  # Latest preprints
                    "semantic_scholar": 0.8,  # Recent papers
                    "osf_preprints": 0.7,  # Recent preprints
                    "socarxiv": 0.7,  # Social science preprints
                }
            )
        elif intent == QueryIntent.HISTORICAL_FOUNDATIONAL:
            preferences.update(
                {
                    "core": 0.9,  # Historical archives
                    "crossref": 0.8,  # Established journals
                    "doaj": 0.6,  # Open access archives
                }
            )
        elif intent == QueryIntent.APPLIED_PRACTICAL:
            preferences.update(
                {
                    "core": 0.8,  # Applied research
                    "semantic_scholar": 0.7,  # Industry connections
                    "doaj": 0.6,  # Practical journals
                    "arxiv": 0.5,  # Some applied work
                }
            )

        # Enhanced temporal-based routing rules
        if temporal == TemporalPreference.RECENT:
            # Strong bias towards preprint servers for recent work
            preferences["arxiv"] *= 1.3
            preferences["osf_preprints"] *= 1.3
            preferences["socarxiv"] *= 1.3
            # Moderate boost for fast-indexing databases
            preferences["semantic_scholar"] *= 1.1
            # Reduce preference for slower-updating archives
            preferences["core"] *= 0.8
            preferences["crossref"] *= 0.9
        elif temporal == TemporalPreference.CURRENT:
            # Balanced approach favoring comprehensive databases
            preferences["semantic_scholar"] *= 1.2
            preferences["arxiv"] *= 1.1
            preferences["crossref"] *= 1.1
        elif temporal == TemporalPreference.HISTORICAL:
            # Strong preference for comprehensive archives
            preferences["core"] *= 1.4  # Best for historical content
            preferences["crossref"] *= 1.2  # Established journals
            preferences["doaj"] *= 1.1  # Open access archives
            # Reduce preprint preferences for historical searches
            preferences["arxiv"] *= 0.7
            preferences["osf_preprints"] *= 0.6
            preferences["socarxiv"] *= 0.6

        # Apply temporal penalty/bonus based on database update frequency
        temporal_adjustments = self._get_temporal_source_adjustments(temporal)
        for source, adjustment in temporal_adjustments.items():
            if source in preferences:
                preferences[source] *= adjustment

        # Normalize to 0-1 range
        max_pref = max(preferences.values())
        if max_pref > 1.0:
            preferences = {k: v / max_pref for k, v in preferences.items()}

        return preferences

    def _get_temporal_source_adjustments(
        self, temporal: TemporalPreference
    ) -> dict[str, float]:
        """Get temporal-specific adjustments based on source characteristics."""
        # Get source characteristics from configuration or infer from source names/descriptions
        source_temporal_profiles = self._get_source_temporal_profiles()

        adjustments = {}

        if temporal == TemporalPreference.RECENT:
            # Favor sources with high update frequency and recent bias
            for source, profile in source_temporal_profiles.items():
                if profile["update_frequency"] == "daily":
                    adjustments[source] = 1.2
                elif profile["update_frequency"] == "weekly":
                    adjustments[source] = 1.0
                else:
                    adjustments[source] = 0.8
        elif temporal == TemporalPreference.HISTORICAL:
            # Favor sources with high historical depth
            for source, profile in source_temporal_profiles.items():
                if profile["historical_depth"] == "very_high":
                    adjustments[source] = 1.2
                elif profile["historical_depth"] == "high":
                    adjustments[source] = 1.0
                else:
                    adjustments[source] = 0.7
        else:
            # Neutral temporal preference - no adjustments
            adjustments = {source: 1.0 for source in source_temporal_profiles.keys()}

        return adjustments

    def _get_base_source_preferences(self) -> dict[str, float]:
        """Get base source preferences from configuration."""
        try:
            from ..config import get_current_config

            config = get_current_config()
            if not config or not config.sources:
                return {}

            # Create base preferences for all enabled sources
            preferences = {}
            for source_name, source_config in config.sources.items():
                if getattr(source_config, "enabled", False):
                    # Default preference based on source type/category
                    preferences[source_name] = self._infer_base_preference(
                        source_name, source_config
                    )

            return preferences
        except Exception:
            return {}

    def _infer_base_preference(self, source_name: str, source_config: Any) -> float:
        """Infer base preference score for a source."""
        source_name_lower = source_name.lower()

        # High-quality comprehensive sources
        if any(term in source_name_lower for term in ["semantic_scholar", "crossref"]):
            return 0.6
        # Preprint servers (good for recent content)
        elif any(term in source_name_lower for term in ["arxiv", "socarxiv", "osf"]):
            return 0.5
        # Specialized medical sources
        elif any(term in source_name_lower for term in ["pubmed", "pmc", "clinical"]):
            return 0.4
        # Open access repositories
        elif any(term in source_name_lower for term in ["core", "doaj", "openalex"]):
            return 0.4
        # Business/economics sources
        elif any(term in source_name_lower for term in ["repec", "ssrn"]):
            return 0.4
        # Default for unknown sources
        else:
            return 0.3

    def _get_source_temporal_profiles(self) -> dict[str, dict[str, Any]]:
        """Get temporal profiles for all configured sources."""
        try:
            from ..config import get_current_config

            config = get_current_config()
            if not config or not config.sources:
                # Fallback to basic profiles
                return self._get_fallback_temporal_profiles()

            profiles = {}
            for source_name, source_config in config.sources.items():
                if getattr(source_config, "enabled", False):
                    profiles[source_name] = self._infer_temporal_profile(
                        source_name, source_config
                    )

            return profiles
        except Exception:
            return self._get_fallback_temporal_profiles()

    def _infer_temporal_profile(
        self, source_name: str, source_config: Any
    ) -> dict[str, Any]:
        """Infer temporal profile for a source based on its characteristics."""
        source_name_lower = source_name.lower()

        # Preprint servers - fast updates, recent bias
        if any(
            term in source_name_lower
            for term in ["arxiv", "socarxiv", "osf", "preprint"]
        ):
            return {
                "update_frequency": "daily",
                "historical_depth": (
                    "low"
                    if "socarxiv" in source_name_lower or "osf" in source_name_lower
                    else "medium"
                ),
                "recent_bias": 1.0,
            }
        # Comprehensive academic databases
        elif any(
            term in source_name_lower
            for term in ["semantic_scholar", "crossref", "openalex"]
        ):
            return {
                "update_frequency": "weekly",
                "historical_depth": (
                    "very_high" if "crossref" in source_name_lower else "high"
                ),
                "recent_bias": 0.6 if "crossref" in source_name_lower else 0.8,
            }
        # Medical databases
        elif any(term in source_name_lower for term in ["pubmed", "pmc", "clinical"]):
            return {
                "update_frequency": "daily",
                "historical_depth": "high",
                "recent_bias": 0.7,
            }
        # Repository/archive sources
        elif any(term in source_name_lower for term in ["core", "doaj"]):
            return {
                "update_frequency": (
                    "weekly" if "doaj" in source_name_lower else "monthly"
                ),
                "historical_depth": "very_high",
                "recent_bias": 0.5 if "doaj" in source_name_lower else 0.3,
            }
        # Default profile for unknown sources
        else:
            return {
                "update_frequency": "weekly",
                "historical_depth": "medium",
                "recent_bias": 0.5,
            }

    def _get_fallback_temporal_profiles(self) -> dict[str, dict[str, Any]]:
        """Get fallback temporal profiles for basic sources."""
        return {
            "arxiv": {
                "update_frequency": "daily",
                "historical_depth": "medium",
                "recent_bias": 1.0,
            },
            "semantic_scholar": {
                "update_frequency": "weekly",
                "historical_depth": "high",
                "recent_bias": 0.8,
            },
            "crossref": {
                "update_frequency": "weekly",
                "historical_depth": "very_high",
                "recent_bias": 0.6,
            },
            "pubmed": {
                "update_frequency": "daily",
                "historical_depth": "high",
                "recent_bias": 0.7,
            },
            "core": {
                "update_frequency": "monthly",
                "historical_depth": "very_high",
                "recent_bias": 0.3,
            },
            "doaj": {
                "update_frequency": "weekly",
                "historical_depth": "high",
                "recent_bias": 0.5,
            },
        }

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Comprehensive query analysis to determine intent and preferences.

        Args:
            query: The search query to analyze

        Returns:
            QueryAnalysis object with detected intent and preferences
        """
        # Calculate intent scores
        intent_scores = self._calculate_intent_scores(query)
        primary_intent = (
            max(intent_scores, key=lambda x: intent_scores[x])
            if intent_scores
            else QueryIntent.GENERAL
        )
        intent_confidence = intent_scores.get(primary_intent, 0.0)

        # Calculate temporal scores
        temporal_scores = self._calculate_temporal_scores(query)
        primary_temporal = (
            max(temporal_scores, key=lambda x: temporal_scores[x])
            if temporal_scores
            else TemporalPreference.NEUTRAL
        )

        # If no strong temporal preference, default to neutral
        if temporal_scores.get(primary_temporal, 0.0) < 0.1:
            primary_temporal = TemporalPreference.NEUTRAL

        # Detect complexity
        complexity = self._detect_complexity(query)

        # Extract keywords and phrases
        words = query.lower().split()
        keywords = [word for word in words if len(word) > 2]  # Filter short words
        phrases = []

        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        phrases.extend(quoted_phrases)

        # Extract noun phrases (simple heuristic)
        if complexity in ["phrase", "complex"]:
            for i in range(len(words) - 1):
                if len(words[i]) > 2 and len(words[i + 1]) > 2:
                    phrases.append(f"{words[i]} {words[i+1]}")

        # Identify academic indicators
        academic_indicators = []
        for category, indicators in self.academic_indicators.items():
            for indicator in indicators:
                if indicator.lower() in query.lower():
                    academic_indicators.append(f"{category}:{indicator}")

        # Get source preferences
        source_preferences = self._get_source_preferences(
            primary_intent, primary_temporal
        )

        return QueryAnalysis(
            intent=primary_intent,
            temporal_preference=primary_temporal,
            confidence=intent_confidence,
            complexity=complexity,
            keywords=keywords,
            phrases=phrases,
            academic_indicators=academic_indicators,
            source_preferences=source_preferences,
        )

    def get_routing_recommendations(self, query: str) -> dict[str, Any]:
        """
        Get routing recommendations based on query analysis.

        Args:
            query: The search query

        Returns:
            Dictionary with routing recommendations
        """
        analysis = self.analyze_query(query)

        recommendations = {
            "primary_intent": analysis.intent.value,
            "temporal_preference": analysis.temporal_preference.value,
            "confidence": analysis.confidence,
            "complexity": analysis.complexity,
            "recommended_sources": sorted(
                analysis.source_preferences.items(), key=lambda x: x[1], reverse=True
            )[
                :5
            ],  # Top 5 sources
            "search_strategy": self._get_search_strategy(analysis),
            "query_expansions": self._suggest_query_expansions(query, analysis),
        }

        return recommendations

    def _get_search_strategy(self, analysis: QueryAnalysis) -> dict[str, str]:
        """Suggest search strategy based on analysis."""
        strategy = {
            "primary_approach": "standard",
            "fallback_needed": "true",
            "parallel_search": "false",
        }

        # Intent-based strategies
        if analysis.intent == QueryIntent.SURVEY_REVIEW:
            strategy.update(
                {
                    "primary_approach": "comprehensive",
                    "parallel_search": "true",
                    "result_merging": "weighted_by_impact",
                }
            )
        elif analysis.intent == QueryIntent.RECENT_RESEARCH:
            strategy.update(
                {
                    "primary_approach": "preprint_focused",
                    "temporal_filter": "last_2_years",
                    "sort_by": "date_desc",
                }
            )

        # Enhanced temporal-based strategies
        if analysis.temporal_preference == TemporalPreference.RECENT:
            strategy.update(
                {
                    "primary_approach": "recent_focused",
                    "temporal_filter": "last_1_year",
                    "sort_by": "date_desc",
                    "source_priority": "preprint_servers",
                    "fallback_temporal": "last_2_years",
                    "result_freshness_weight": "0.8",
                }
            )
        elif analysis.temporal_preference == TemporalPreference.CURRENT:
            strategy.update(
                {
                    "primary_approach": "current_focused",
                    "temporal_filter": "last_5_years",
                    "sort_by": "relevance_date_weighted",
                    "source_priority": "balanced",
                    "fallback_temporal": "last_10_years",
                    "result_freshness_weight": "0.5",
                }
            )
        elif analysis.temporal_preference == TemporalPreference.HISTORICAL:
            strategy.update(
                {
                    "primary_approach": "archive_focused",
                    "temporal_filter": "all_time",
                    "sort_by": "relevance_citation_weighted",
                    "source_priority": "comprehensive_archives",
                    "fallback_temporal": "older_than_5_years",
                    "result_freshness_weight": "0.2",
                    "historical_boost": "true",
                }
            )

        # Complexity-based adjustments
        if analysis.complexity == "boolean":
            strategy.update(
                {"query_preprocessing": "minimal", "exact_match_weight": "0.9"}
            )
        elif analysis.complexity == "phrase":
            strategy.update(
                {"phrase_matching": "enhanced", "exact_phrase_weight": "0.7"}
            )

        return strategy

    def _suggest_query_expansions(
        self, query: str, analysis: QueryAnalysis
    ) -> list[str]:
        """Suggest query expansions based on analysis."""
        expansions = []

        # Add temporal modifiers based on preference
        if analysis.temporal_preference == TemporalPreference.RECENT:
            expansions.extend(
                [f"{query} 2024", f"{query} 2025", f"recent {query}", f"latest {query}"]
            )
        elif analysis.temporal_preference == TemporalPreference.HISTORICAL:
            expansions.extend(
                [f"history of {query}", f"historical {query}", f"evolution of {query}"]
            )

        # Add intent-based modifiers
        if analysis.intent == QueryIntent.SURVEY_REVIEW:
            expansions.extend(
                [f"{query} review", f"{query} survey", f"{query} state of the art"]
            )
        elif analysis.intent == QueryIntent.APPLIED_PRACTICAL:
            expansions.extend(
                [
                    f"{query} application",
                    f"{query} implementation",
                    f"practical {query}",
                ]
            )

        return expansions[:5]  # Limit to top 5 suggestions


# Convenience functions
def analyze_query_intent(query: str) -> QueryAnalysis:
    """Analyze query intent using the detector."""
    detector = QueryIntentDetector()
    return detector.analyze_query(query)


def get_routing_recommendations(query: str) -> dict[str, Any]:
    """Get routing recommendations for a query."""
    detector = QueryIntentDetector()
    return detector.get_routing_recommendations(query)
