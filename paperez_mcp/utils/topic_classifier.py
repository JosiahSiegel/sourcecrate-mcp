"""
Topic classification system for academic queries.
"""



def classify_query_topic(query: str) -> dict[str, float]:
    """
    Classify query into topic categories.

    Args:
        query: The search query to classify

    Returns:
        Dictionary with topic scores (0.0 to 1.0)
    """

    # Keywords for different domains
    DOMAIN_KEYWORDS = {
        "stem": [
            "algorithm", "computation", "neural", "quantum", "equation",
            "theorem", "proof", "optimization", "machine learning", "AI",
            "artificial intelligence", "computer science", "mathematics",
            "physics", "chemistry", "engineering", "software", "programming",
            "data science", "statistics", "mathematical", "computational",
            "technology", "technical", "scientific computing", "modeling"
        ],
        "medical": [
            "disease", "treatment", "clinical", "patient", "therapy",
            "drug", "cancer", "diagnosis", "medical", "health",
            "medicine", "pharmaceutical", "hospital", "surgical",
            "epidemiology", "pathology", "cardiology", "oncology",
            "neurology", "psychiatry", "pediatric", "healthcare",
            "biomedical", "clinical trial", "pharmacology"
        ],
        "historical": [
            "history", "historical", "war", "century", "empire",
            "declaration", "treaty", "revolution", "colonial", "mandate",
            "ancient", "medieval", "renaissance", "enlightenment",
            "industrial revolution", "world war", "civil war",
            "independence", "constitution", "monarchy", "republic",
            "civilization", "archaeological", "heritage", "legacy",
            "period", "era", "dynasty", "chronicle", "archives",
            "american revolution", "french revolution", "balfour", "versailles"
        ],
        "social_science": [
            "society", "social", "political", "economic", "culture",
            "psychology", "anthropology", "sociology", "demographic",
            "governance", "policy", "public", "urban", "rural",
            "community", "behavioral", "cognitive", "development",
            "education", "pedagogy", "linguistics", "philosophy",
            "ethics", "law", "legal", "justice", "human rights",
            "gender", "race", "ethnicity", "class", "inequality"
        ],
        "humanities": [
            "literature", "literary", "art", "artistic", "music",
            "poetry", "novel", "drama", "theatre", "film",
            "philosophy", "philosophical", "ethics", "aesthetics",
            "religion", "religious", "theology", "spiritual",
            "language", "linguistic", "cultural studies", "criticism",
            "interpretation", "hermeneutics", "rhetoric", "narrative"
        ],
        "biological": [
            "biology", "biological", "genetics", "genome", "DNA",
            "protein", "cell", "molecular", "evolution", "ecology",
            "species", "organism", "biodiversity", "biotechnology",
            "biochemistry", "microbiology", "botany", "zoology",
            "physiology", "anatomy", "bioinformatics", "enzyme",
            "metabolism", "neuroscience", "brain", "nervous system"
        ]
    }

    query_lower = query.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in query_lower)
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

    return max(scores, key=scores.get)


def get_recommended_sources(query: str) -> list[str]:
    """
    Recommend sources based on query topic.

    Args:
        query: The search query to analyze

    Returns:
        List of recommended source names in priority order
    """
    classify_query_topic(query)
    primary_topic = get_primary_topic(query)

    # Determine sources based on primary topic and scores
    if primary_topic == "stem":
        return ["arxiv", "semantic_scholar", "crossref"]
    elif primary_topic == "medical" or primary_topic == "biological":
        return ["pubmed", "semantic_scholar", "crossref", "core"]
    elif primary_topic == "historical":
        return ["core", "doaj", "socarxiv", "google_scholar", "crossref"]
    elif primary_topic == "social_science":
        return ["socarxiv", "osf_preprints", "core", "semantic_scholar", "crossref"]
    elif primary_topic == "humanities":
        return ["core", "doaj", "google_scholar", "semantic_scholar", "crossref"]
    else:
        # General/mixed queries - use comprehensive search
        return ["semantic_scholar", "crossref", "arxiv", "core"]


def should_skip_source_for_topic(source: str, query: str, threshold: float = 0.05) -> bool:
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


def get_topic_explanation(query: str) -> dict[str, any]:
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

    return {
        "query": query,
        "scores": scores,
        "primary_topic": primary_topic,
        "recommended_sources": recommended_sources,
        "confidence": max(scores.values()) if scores else 0,
        "is_mixed_topic": len([s for s in scores.values() if s > 0.1]) > 2
    }
