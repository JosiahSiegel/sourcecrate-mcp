"""
Query processing and reformulation for better search coverage.
"""

import re


def generate_alternative_queries(query: str) -> list[str]:
    """
    Generate alternative queries for better coverage.

    Args:
        query: Original search query

    Returns:
        List of alternative query formulations
    """
    alternatives = [query]

    # Historical topic patterns and expansions
    historical_expansions = {
        "Balfour Declaration": [
            "British Mandate Palestine",
            "1917 Balfour",
            "Zionism British",
            "Palestine British policy",
            "Jewish national home",
            "McMahon Hussein",
        ],
        "World War I": [
            "Great War",
            "WWI",
            "1914-1918",
            "First World War",
            "European war 1914",
            "war to end all wars",
        ],
        "World War II": [
            "WWII",
            "Second World War",
            "1939-1945",
            "Nazi Germany",
            "Allied powers",
            "Axis powers",
            "Holocaust",
        ],
        "American Revolution": [
            "Revolutionary War",
            "War of Independence",
            "1776",
            "thirteen colonies",
            "Continental Congress",
            "Declaration Independence",
        ],
        "French Revolution": [
            "1789 Revolution",
            "Reign of Terror",
            "Jacobins",
            "Louis XVI",
            "Marie Antoinette",
            "Bastille",
        ],
        "Industrial Revolution": [
            "industrialization",
            "factory system",
            "steam engine",
            "textile industry",
            "urbanization",
            "working class",
        ],
        "Cold War": [
            "US Soviet rivalry",
            "Iron Curtain",
            "nuclear deterrence",
            "proxy wars",
            "containment policy",
            "détente",
        ],
        "Renaissance": [
            "rebirth",
            "humanism",
            "Italian Renaissance",
            "Northern Renaissance",
            "artistic revival",
            "Leonardo da Vinci",
        ],
        "Treaty of Versailles": [
            "Paris Peace Conference",
            "League of Nations",
            "German reparations",
            "Wilson fourteen points",
            "territorial changes",
        ],
    }

    # Scientific and technical expansions
    technical_expansions = {
        "machine learning": [
            "artificial intelligence",
            "neural networks",
            "deep learning",
            "supervised learning",
            "unsupervised learning",
            "reinforcement learning",
        ],
        "quantum computing": [
            "quantum mechanics",
            "qubits",
            "quantum algorithms",
            "quantum supremacy",
            "quantum entanglement",
            "quantum gates",
        ],
        "climate change": [
            "global warming",
            "greenhouse effect",
            "carbon emissions",
            "environmental impact",
            "sustainability",
            "renewable energy",
        ],
        "artificial intelligence": [
            "machine learning",
            "AI",
            "neural networks",
            "computer vision",
            "natural language processing",
            "robotics",
        ],
    }

    # Medical and biological expansions
    medical_expansions = {
        "COVID-19": [
            "coronavirus",
            "SARS-CoV-2",
            "pandemic",
            "vaccine development",
            "public health",
            "epidemiology",
        ],
        "cancer research": [
            "oncology",
            "tumor biology",
            "chemotherapy",
            "immunotherapy",
            "radiation therapy",
            "metastasis",
        ],
        "Alzheimer disease": [
            "dementia",
            "neurodegenerative",
            "amyloid plaques",
            "tau protein",
            "memory loss",
            "cognitive decline",
        ],
    }

    # Social science expansions
    social_expansions = {
        "economic inequality": [
            "income disparity",
            "wealth distribution",
            "social stratification",
            "poverty",
            "class differences",
            "economic mobility",
        ],
        "urban planning": [
            "city development",
            "metropolitan design",
            "zoning",
            "transportation planning",
            "sustainable cities",
            "smart cities",
        ],
        "educational policy": [
            "school reform",
            "curriculum development",
            "teacher training",
            "educational assessment",
            "learning outcomes",
            "pedagogy",
        ],
    }

    # Combine all expansion dictionaries
    all_expansions = {
        **historical_expansions,
        **technical_expansions,
        **medical_expansions,
        **social_expansions,
    }

    # Check for direct matches
    query_lower = query.lower()
    for pattern, expansions in all_expansions.items():
        if pattern.lower() in query_lower:
            alternatives.extend(expansions)

    # Generate variations based on query structure
    alternatives.extend(_generate_structural_variations(query))

    # Remove duplicates while preserving order
    seen = set()
    unique_alternatives = []
    for alt in alternatives:
        if alt.lower() not in seen:
            seen.add(alt.lower())
            unique_alternatives.append(alt)

    return unique_alternatives


def _generate_structural_variations(query: str) -> list[str]:
    """
    Generate structural variations of the query.

    Args:
        query: Original query

    Returns:
        List of structural variations
    """
    variations = []

    # Remove/add quotes for phrase vs keyword search
    if query.startswith('"') and query.endswith('"'):
        # Remove quotes for keyword search
        variations.append(query[1:-1])
    elif " " in query:
        # Add quotes for phrase search
        variations.append(f'"{query}"')

    # Generate synonym substitutions for common academic terms
    synonyms = {
        "study": ["research", "analysis", "investigation", "examination"],
        "analysis": ["study", "research", "investigation", "examination"],
        "research": ["study", "analysis", "investigation", "examination"],
        "effect": ["impact", "influence", "consequence", "result"],
        "impact": ["effect", "influence", "consequence", "result"],
        "method": ["approach", "technique", "methodology", "procedure"],
        "approach": ["method", "technique", "methodology", "procedure"],
        "development": ["evolution", "progress", "advancement", "growth"],
        "evolution": ["development", "progress", "advancement", "growth"],
        "theory": ["model", "framework", "hypothesis", "concept"],
        "model": ["theory", "framework", "hypothesis", "concept"],
    }

    words = query.lower().split()
    for i, word in enumerate(words):
        if word in synonyms:
            for synonym in synonyms[word]:
                new_words = words.copy()
                new_words[i] = synonym
                variations.append(" ".join(new_words))

    # Generate related term expansions
    if len(words) >= 2:
        # Try removing common stopwords that might be too restrictive
        stopwords = {
            "and",
            "or",
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
        }
        filtered_words = [w for w in words if w not in stopwords]
        if len(filtered_words) != len(words) and len(filtered_words) >= 1:
            variations.append(" ".join(filtered_words))

    return variations


def expand_historical_query(query: str) -> list[str]:
    """
    Specialized expansion for historical queries.

    Args:
        query: Historical query

    Returns:
        List of expanded historical queries
    """
    expansions = []

    # Extract potential years or periods
    year_pattern = r"\b(19|20)\d{2}\b|\b\d{4}\b"
    years = re.findall(year_pattern, query)

    # Extract potential names (capitalized words)
    name_pattern = r"\b[A-Z][a-z]+\b"
    re.findall(name_pattern, query)

    # Add period context
    historical_periods = {
        "1914": "World War I",
        "1918": "post-World War I",
        "1939": "World War II",
        "1945": "post-World War II",
        "1776": "American Revolution",
        "1789": "French Revolution",
        "1917": "Russian Revolution",
        "1929": "Great Depression",
    }

    for year in years:
        if year in historical_periods:
            period = historical_periods[year]
            expansions.append(f"{query} {period}")

    # Add geographical context for historical events
    if any(
        term in query.lower() for term in ["declaration", "treaty", "agreement", "pact"]
    ):
        expansions.extend(
            [
                f"{query} international relations",
                f"{query} diplomatic history",
                f"{query} foreign policy",
            ]
        )

    # Add archival and document-related terms
    if any(
        term in query.lower()
        for term in ["declaration", "document", "text", "manuscript"]
    ):
        expansions.extend(
            [
                f"{query} primary source",
                f"{query} archival document",
                f"{query} historical text",
            ]
        )

    return expansions


def optimize_query_for_source(query: str, source: str) -> str:
    """
    Optimize query formatting for specific sources.

    Args:
        query: Original query
        source: Target source name

    Returns:
        Optimized query for the source
    """
    if source == "arxiv":
        # arXiv works well with field-specific searches
        if (
            " " in query
            and not query.startswith("ti:")
            and not query.startswith("abs:")
        ):
            return f'ti:"{query}" OR abs:"{query}"'

    elif source == "pubmed":
        # PubMed supports MeSH terms and field tags
        if " " in query:
            # Add field tags for better precision
            return f'"{query}"[Title/Abstract]'

    elif source == "semantic_scholar":
        # Semantic Scholar works well with quoted phrases
        if " " in query and not (query.startswith('"') and query.endswith('"')):
            return f'"{query}"'

    elif source == "crossref":
        # CrossRef is more flexible with natural language
        return query

    elif source in ["core", "doaj", "socarxiv"]:
        # These APIs generally work better with simpler queries
        # Remove quotes if present
        if query.startswith('"') and query.endswith('"'):
            return query[1:-1]

    return query
