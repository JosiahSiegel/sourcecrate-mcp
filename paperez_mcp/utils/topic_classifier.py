"""
Topic classification system for academic queries.
"""

from typing import Any


def classify_query_topic(query: str) -> dict[str, float]:
    """
    Classify query into topic categories.

    Args:
        query: The search query to classify

    Returns:
        Dictionary with topic scores (0.0 to 1.0)
    """

    # Keywords for different domains
    domain_keywords = {
        "stem": [
            "algorithm",
            "computation",
            "neural",
            "quantum",
            "equation",
            "theorem",
            "proof",
            "optimization",
            "machine learning",
            "AI",
            "artificial intelligence",
            "computer science",
            "mathematics",
            "physics",
            "chemistry",
            "engineering",
            "software",
            "programming",
            "data science",
            "statistics",
            "mathematical",
            "computational",
            "technology",
            "technical",
            "scientific computing",
            "modeling",
            "deep learning",
            "neural network",
            "data mining",
            "pattern recognition",
            "automated",
            "simulation",
            "digital",
        ],
        "medical": [
            "disease",
            "treatment",
            "clinical",
            "patient",
            "therapy",
            "drug",
            "cancer",
            "diagnosis",
            "medical",
            "health",
            "medicine",
            "pharmaceutical",
            "hospital",
            "surgical",
            "epidemiology",
            "pathology",
            "cardiology",
            "oncology",
            "neurology",
            "psychiatry",
            "pediatric",
            "healthcare",
            "biomedical",
            "clinical trial",
            "pharmacology",
            "drug discovery",
            "drug development",
            "therapeutic",
            "diagnostic",
            "precision medicine",
            "personalized medicine",
            "medical imaging",
            "radiotherapy",
            "immunotherapy",
        ],
        "historical": [
            "history",
            "historical",
            "war",
            "century",
            "empire",
            "declaration",
            "treaty",
            "revolution",
            "colonial",
            "mandate",
            "ancient",
            "medieval",
            "renaissance",
            "enlightenment",
            "industrial revolution",
            "world war",
            "civil war",
            "independence",
            "constitution",
            "monarchy",
            "republic",
            "civilization",
            "archaeological",
            "heritage",
            "legacy",
            "period",
            "era",
            "dynasty",
            "chronicle",
            "archives",
            "american revolution",
            "french revolution",
            "balfour",
            "versailles",
        ],
        "social_science": [
            "society",
            "social",
            "political",
            "economic",
            "culture",
            "psychology",
            "anthropology",
            "sociology",
            "demographic",
            "governance",
            "policy",
            "public",
            "urban",
            "rural",
            "community",
            "behavioral",
            "cognitive",
            "development",
            "education",
            "pedagogy",
            "linguistics",
            "philosophy",
            "ethics",
            "law",
            "legal",
            "justice",
            "human rights",
            "gender",
            "race",
            "ethnicity",
            "class",
            "inequality",
        ],
        "humanities": [
            "literature",
            "literary",
            "art",
            "artistic",
            "music",
            "poetry",
            "novel",
            "drama",
            "theatre",
            "film",
            "philosophy",
            "philosophical",
            "ethics",
            "aesthetics",
            "religion",
            "religious",
            "theology",
            "spiritual",
            "language",
            "linguistic",
            "cultural studies",
            "criticism",
            "interpretation",
            "hermeneutics",
            "rhetoric",
            "narrative",
        ],
        "biological": [
            "biology",
            "biological",
            "genetics",
            "genome",
            "DNA",
            "protein",
            "cell",
            "molecular",
            "evolution",
            "ecology",
            "species",
            "organism",
            "biodiversity",
            "biotechnology",
            "biochemistry",
            "microbiology",
            "botany",
            "zoology",
            "physiology",
            "anatomy",
            "bioinformatics",
            "enzyme",
            "metabolism",
            "neuroscience",
            "brain",
            "nervous system",
            "genomics",
            "proteomics",
            "transcriptomics",
            "systems biology",
            "computational biology",
            "structural biology",
            "molecular biology",
            "synthetic biology",
        ],
    }

    query_lower = query.lower()
    scores = {}

    for domain, keywords in domain_keywords.items():
        # Count keyword matches (ensure case-insensitive matching)
        matches = sum(1 for keyword in keywords if keyword.lower() in query_lower)
        # Normalize by number of keywords in domain
        scores[domain] = matches / len(keywords)

    return scores


def get_primary_topic(query: str) -> str:
    """
    Get the primary topic category for a query.

    Args:
        query: The search query to classify

    Returns:
        The primary topic category name
    """
    scores = classify_query_topic(query)

    # Find the topic with highest score
    if not scores or max(scores.values()) == 0:
        return "general"

    return max(scores, key=lambda x: scores[x])


def get_recommended_sources(query: str) -> list[str]:
    """
    Get recommended sources based on query topic classification.
    Now configuration-aware to support infinite custom sources with cross-disciplinary routing.

    Args:
        query: The search query to analyze

    Returns:
        List of recommended source names in priority order
    """
    scores = classify_query_topic(query)
    primary_topic = get_primary_topic(query)

    # Get available sources from configuration
    try:
        from ..config import get_current_config

        config = get_current_config()
        if not config or not config.sources:
            # Fallback to basic sources if config unavailable
            return ["semantic_scholar", "crossref", "arxiv", "core"]

        # Get all enabled sources
        available_sources = [
            name
            for name, source_config in config.sources.items()
            if getattr(source_config, "enabled", False)
        ]

        if not available_sources:
            return []

        # Categorize sources by inferring their focus from descriptions
        categorized_sources: dict[str, list[str]] = {
            "stem": [],
            "medical": [],
            "historical": [],
            "social_science": [],
            "humanities": [],
            "business": [],
            "general": [],
        }

        for source_name in available_sources:
            source_config = config.sources[source_name]
            category = _infer_source_category(source_name, source_config)
            categorized_sources[category].append(source_name)

        # Improved cross-disciplinary source selection
        recommended = []

        # Define cross-disciplinary threshold (lowered for better detection)
        significant_threshold = (
            0.02  # Much lower threshold for cross-disciplinary detection
        )

        # Get all significant topics (not just primary)
        significant_topics = [
            topic for topic, score in scores.items() if score >= significant_threshold
        ]

        # Detect cross-disciplinary queries
        is_cross_disciplinary = len(significant_topics) > 1

        if is_cross_disciplinary:
            # For cross-disciplinary queries, include sources from all significant topics
            for topic in significant_topics:
                if topic == "stem":
                    recommended.extend(categorized_sources["stem"])
                elif topic in ["medical", "biological"]:
                    recommended.extend(categorized_sources["medical"])
                elif topic == "historical":
                    recommended.extend(categorized_sources["historical"])
                elif topic == "social_science":
                    recommended.extend(categorized_sources["social_science"])
                elif topic == "humanities":
                    recommended.extend(categorized_sources["humanities"])
                elif topic == "business":
                    recommended.extend(categorized_sources["business"])

            # Add general sources for broader coverage
            recommended.extend(categorized_sources["general"][:2])

        else:
            # Single-topic queries - use original logic but add cross-pollination
            if primary_topic == "stem":
                recommended.extend(categorized_sources["stem"])
                recommended.extend(categorized_sources["general"][:2])
            elif primary_topic == "medical" or primary_topic == "biological":
                recommended.extend(categorized_sources["medical"])
                # For medical queries, also include STEM sources for computational approaches
                if any(
                    term in query.lower()
                    for term in [
                        "machine learning",
                        "AI",
                        "algorithm",
                        "computational",
                        "modeling",
                        "bioinformatics",
                    ]
                ):
                    recommended.extend(categorized_sources["stem"][:2])
                recommended.extend(categorized_sources["general"][:2])
            elif primary_topic == "historical":
                recommended.extend(categorized_sources["historical"])
                recommended.extend(categorized_sources["general"][:2])
            elif primary_topic == "social_science":
                recommended.extend(categorized_sources["social_science"])
                recommended.extend(categorized_sources["general"][:2])
            elif primary_topic == "humanities":
                recommended.extend(categorized_sources["humanities"])
                recommended.extend(categorized_sources["general"][:2])
            elif primary_topic == "business":
                recommended.extend(categorized_sources["business"])
                recommended.extend(categorized_sources["general"][:2])
            else:
                # General/mixed queries - prioritize general sources
                recommended.extend(categorized_sources["general"])
                # Add some from each category for comprehensive coverage
                for category_sources in categorized_sources.values():
                    if category_sources and category_sources[0] not in recommended:
                        recommended.append(category_sources[0])

        # Remove duplicates while preserving order
        unique_recommended = []
        seen = set()
        for source in recommended:
            if source not in seen:
                unique_recommended.append(source)
                seen.add(source)

        return unique_recommended[:8]  # Increased limit for cross-disciplinary coverage

    except Exception:
        # Ultimate fallback - return basic sources if anything fails
        return ["semantic_scholar", "crossref", "arxiv", "core"]


def _infer_source_category(source_name: str, source_config: Any) -> str:
    """
    Infer the category of a source from its name and configuration.
    This allows dynamic categorization of custom sources.
    """
    source_name_lower = source_name.lower()

    # Check source name patterns first
    if any(
        term in source_name_lower
        for term in ["arxiv", "preprint", "computer", "physics", "math"]
    ):
        return "stem"
    elif any(
        term in source_name_lower
        for term in ["pubmed", "medical", "clinical", "health", "bio"]
    ):
        return "medical"
    elif any(
        term in source_name_lower
        for term in ["history", "historical", "archive", "government"]
    ):
        return "historical"
    elif any(
        term in source_name_lower
        for term in ["social", "psychology", "sociology", "education"]
    ):
        return "social_science"
    elif any(
        term in source_name_lower
        for term in ["humanities", "literature", "art", "philosophy"]
    ):
        return "humanities"
    elif any(
        term in source_name_lower
        for term in ["business", "economics", "finance", "repec"]
    ):
        return "business"

    # Check source description/coverage if available
    if hasattr(source_config, "config") and source_config.config:
        config_obj = source_config.config
        description = getattr(config_obj, "description", "").lower()
        coverage = getattr(config_obj, "coverage", "").lower()
        text = f"{description} {coverage}"

        if any(
            term in text
            for term in [
                "computer",
                "algorithm",
                "physics",
                "mathematics",
                "engineering",
            ]
        ):
            return "stem"
        elif any(
            term in text
            for term in ["medical", "biomedical", "clinical", "health", "biological"]
        ):
            return "medical"
        elif any(
            term in text
            for term in ["historical", "history", "archive", "government", "policy"]
        ):
            return "historical"
        elif any(
            term in text
            for term in [
                "social",
                "psychology",
                "sociology",
                "education",
                "anthropology",
            ]
        ):
            return "social_science"
        elif any(
            term in text
            for term in ["humanities", "literature", "art", "philosophy", "culture"]
        ):
            return "humanities"
        elif any(
            term in text
            for term in ["business", "economics", "finance", "management", "corporate"]
        ):
            return "business"

    # Default to general if no clear category
    return "general"


def should_skip_source_for_topic(
    source: str, query: str, threshold: float = 0.05
) -> bool:
    """
    Determine if a source should be skipped for a given topic.

    Args:
        source: The source name to check
        query: The search query
        threshold: Minimum score threshold to consider a topic significant

    Returns:
        True if the source should be skipped, False otherwise
    """
    scores = classify_query_topic(query)

    # Skip arXiv for clearly non-STEM topics
    if source == "arxiv":
        stem_score = scores.get("stem", 0)
        medical_score = scores.get("medical", 0)
        biological_score = scores.get("biological", 0)

        # If it's clearly historical/social science and not STEM/medical/biological
        historical_score = scores.get("historical", 0)
        social_score = scores.get("social_science", 0)
        humanities_score = scores.get("humanities", 0)

        non_stem_score = max(historical_score, social_score, humanities_score)
        stem_related_score = max(stem_score, medical_score, biological_score)

        if non_stem_score > threshold and stem_related_score < threshold / 2:
            return True

    # Skip PubMed for clearly non-medical/biological topics
    if source == "pubmed":
        medical_score = scores.get("medical", 0)
        biological_score = scores.get("biological", 0)

        if max(medical_score, biological_score) < threshold / 2:
            return True

    return False


def get_topic_explanation(query: str) -> dict[str, Any]:
    """
    Get detailed topic analysis for debugging/logging.

    Args:
        query: The search query to analyze

    Returns:
        Dictionary with detailed topic analysis
    """
    scores = classify_query_topic(query)
    primary_topic = get_primary_topic(query)
    recommended_sources = get_recommended_sources(query)

    # Improved cross-disciplinary detection
    significant_threshold = 0.02  # Match the threshold used in get_recommended_sources
    significant_topics = [
        topic for topic, score in scores.items() if score >= significant_threshold
    ]

    return {
        "query": query,
        "scores": scores,
        "primary_topic": primary_topic,
        "significant_topics": significant_topics,
        "recommended_sources": recommended_sources,
        "confidence": max(scores.values()) if scores else 0,
        "is_mixed_topic": len(significant_topics) > 1,  # Improved detection logic
        "cross_disciplinary_score": len(significant_topics),
    }
