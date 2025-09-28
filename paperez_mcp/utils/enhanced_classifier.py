"""
Enhanced topic classification using statistical similarity methods.
No external APIs or ML models required - uses Jaccard similarity, n-grams, and TF-IDF.
"""

import math
import re
from collections import Counter


class EnhancedTopicClassifier:
    """Statistical topic classifier using Jaccard similarity and n-gram analysis."""

    def __init__(self) -> None:
        self.hierarchical_taxonomy = self._build_hierarchical_taxonomy()
        self.synonym_dictionary = self._build_synonym_dictionary()
        self.stopwords = self._get_stopwords()

    def _get_stopwords(self) -> set[str]:
        """Common English stopwords for filtering."""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'or', 'but', 'if', 'this', 'their',
            'they', 'we', 'you', 'have', 'had', 'what', 'when', 'where', 'who',
            'which', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'may', 'might',
            'must', 'shall', 'should', 'would', 'could'
        }

    def _build_hierarchical_taxonomy(self) -> dict:
        """Build hierarchical keyword taxonomy for better classification."""
        return {
            "stem": {
                "keywords": [
                    "algorithm", "computation", "neural", "quantum", "equation",
                    "theorem", "proof", "optimization", "machine learning", "AI",
                    "artificial intelligence", "computer science", "mathematics",
                    "physics", "chemistry", "engineering", "software", "programming",
                    "data science", "statistics", "mathematical", "computational",
                    "technology", "technical", "scientific computing", "modeling"
                ],
                "subcategories": {
                    "computer_science": {
                        "keywords": [
                            "algorithm", "programming", "software", "hardware", "database",
                            "network", "cybersecurity", "operating system", "compiler",
                            "data structure", "complexity", "parallel", "distributed"
                        ],
                        "subcategories": {
                            "machine_learning": [
                                "neural network", "deep learning", "supervised learning",
                                "unsupervised learning", "reinforcement learning", "CNN",
                                "RNN", "transformer", "attention", "embedding", "classification",
                                "regression", "clustering", "feature", "model", "training"
                            ],
                            "systems": [
                                "distributed system", "operating system", "database system",
                                "file system", "memory management", "concurrency", "threading",
                                "process", "kernel", "virtualization", "cloud computing"
                            ]
                        }
                    },
                    "physics": {
                        "keywords": [
                            "quantum", "particle", "relativity", "mechanics", "thermodynamics",
                            "electromagnetism", "optics", "atomic", "nuclear", "plasma"
                        ],
                        "subcategories": {
                            "quantum_physics": [
                                "quantum mechanics", "quantum computing", "quantum field",
                                "entanglement", "superposition", "decoherence", "qubit",
                                "quantum gate", "quantum algorithm", "quantum cryptography"
                            ],
                            "astrophysics": [
                                "galaxy", "cosmology", "black hole", "dark matter", "dark energy",
                                "neutron star", "supernova", "exoplanet", "telescope", "redshift"
                            ]
                        }
                    },
                    "mathematics": {
                        "keywords": [
                            "algebra", "calculus", "geometry", "topology", "analysis",
                            "probability", "statistics", "discrete", "continuous", "function"
                        ]
                    }
                }
            },
            "medical": {
                "keywords": [
                    "disease", "treatment", "clinical", "patient", "therapy",
                    "drug", "cancer", "diagnosis", "medical", "health",
                    "medicine", "pharmaceutical", "hospital", "surgical",
                    "epidemiology", "pathology", "cardiology", "oncology",
                    "neurology", "psychiatry", "pediatric", "healthcare",
                    "biomedical", "clinical trial", "pharmacology"
                ],
                "subcategories": {
                    "clinical_medicine": [
                        "clinical trial", "randomized control", "double blind", "placebo",
                        "efficacy", "adverse event", "side effect", "dosage", "protocol"
                    ],
                    "pharmacology": [
                        "drug discovery", "pharmaceutical", "pharmacokinetics", "metabolism",
                        "toxicity", "bioavailability", "drug interaction", "receptor"
                    ]
                }
            },
            "historical": {
                "keywords": [
                    "history", "historical", "war", "century", "empire",
                    "declaration", "treaty", "revolution", "colonial", "mandate",
                    "ancient", "medieval", "renaissance", "enlightenment",
                    "industrial revolution", "world war", "civil war",
                    "independence", "constitution", "monarchy", "republic",
                    "civilization", "archaeological", "heritage", "legacy",
                    "period", "era", "dynasty", "chronicle", "archives",
                    "american revolution", "french revolution", "balfour", "versailles"
                ],
                "subcategories": {
                    "ancient_history": [
                        "ancient", "antiquity", "classical", "roman empire", "greek",
                        "mesopotamia", "egypt", "pyramid", "archaeology", "artifact"
                    ],
                    "modern_history": [
                        "modern", "contemporary", "20th century", "21st century",
                        "world war", "cold war", "decolonization", "globalization"
                    ]
                }
            },
            "social_science": {
                "keywords": [
                    "society", "social", "political", "economic", "culture",
                    "psychology", "anthropology", "sociology", "demographic",
                    "governance", "policy", "public", "urban", "rural",
                    "community", "behavioral", "cognitive", "development",
                    "education", "pedagogy", "linguistics", "philosophy",
                    "ethics", "law", "legal", "justice", "human rights",
                    "gender", "race", "ethnicity", "class", "inequality"
                ],
                "subcategories": {
                    "economics": [
                        "market", "capitalism", "socialism", "trade", "finance",
                        "monetary", "fiscal", "inflation", "recession", "GDP"
                    ],
                    "political_science": [
                        "government", "democracy", "authoritarian", "election",
                        "voting", "parliament", "congress", "policy", "legislation"
                    ]
                }
            },
            "humanities": {
                "keywords": [
                    "literature", "literary", "art", "artistic", "music",
                    "poetry", "novel", "drama", "theatre", "film",
                    "philosophy", "philosophical", "ethics", "aesthetics",
                    "religion", "religious", "theology", "spiritual",
                    "language", "linguistic", "cultural studies", "criticism",
                    "interpretation", "hermeneutics", "rhetoric", "narrative"
                ],
                "subcategories": {
                    "literature": [
                        "novel", "poetry", "drama", "fiction", "non-fiction",
                        "narrative", "character", "plot", "theme", "literary criticism"
                    ],
                    "philosophy": [
                        "metaphysics", "epistemology", "ethics", "logic", "aesthetics",
                        "phenomenology", "existentialism", "pragmatism", "utilitarianism"
                    ]
                }
            },
            "biological": {
                "keywords": [
                    "biology", "biological", "genetics", "genome", "DNA",
                    "protein", "cell", "molecular", "evolution", "ecology",
                    "species", "organism", "biodiversity", "biotechnology",
                    "biochemistry", "microbiology", "botany", "zoology",
                    "physiology", "anatomy", "bioinformatics", "enzyme",
                    "metabolism", "neuroscience", "brain", "nervous system"
                ],
                "subcategories": {
                    "molecular_biology": [
                        "DNA", "RNA", "protein", "gene", "genome", "chromosome",
                        "mutation", "transcription", "translation", "enzyme"
                    ],
                    "ecology": [
                        "ecosystem", "biodiversity", "conservation", "habitat",
                        "species", "population", "community", "food web", "climate change"
                    ]
                }
            }
        }

    def _build_synonym_dictionary(self) -> dict[str, list[str]]:
        """Build synonym dictionary for query expansion."""
        return {
            # Academic terms
            "paper": ["article", "publication", "manuscript", "study", "research", "document"],
            "research": ["study", "investigation", "analysis", "examination", "inquiry"],
            "study": ["research", "analysis", "investigation", "examination", "survey"],
            "analysis": ["study", "research", "investigation", "examination", "evaluation"],
            "method": ["approach", "technique", "methodology", "procedure", "strategy"],
            "approach": ["method", "technique", "methodology", "procedure", "strategy"],
            "result": ["finding", "outcome", "conclusion", "discovery", "output"],
            "finding": ["result", "outcome", "conclusion", "discovery", "observation"],

            # Technology terms
            "machine learning": ["ML", "deep learning", "neural networks", "AI", "artificial intelligence"],
            "artificial intelligence": ["AI", "machine learning", "ML", "neural networks", "deep learning"],
            "deep learning": ["neural networks", "machine learning", "ML", "AI", "artificial intelligence"],
            "neural network": ["neural net", "deep learning", "machine learning", "connectionist model"],
            "algorithm": ["method", "procedure", "technique", "approach", "process"],
            "computer": ["computational", "digital", "electronic", "automated"],
            "software": ["program", "application", "system", "code", "tool"],
            "data": ["information", "dataset", "records", "statistics", "evidence"],

            # Medical terms
            "disease": ["illness", "disorder", "condition", "pathology", "syndrome"],
            "treatment": ["therapy", "intervention", "medication", "procedure", "cure"],
            "patient": ["subject", "participant", "individual", "case", "client"],
            "drug": ["medication", "pharmaceutical", "medicine", "compound", "agent"],
            "clinical": ["medical", "therapeutic", "healthcare", "diagnostic", "hospital"],

            # Historical terms
            "war": ["conflict", "battle", "warfare", "military", "combat"],
            "revolution": ["uprising", "revolt", "rebellion", "transformation", "change"],
            "ancient": ["old", "historical", "classical", "archaic", "antiquated"],
            "historical": ["past", "former", "previous", "ancient", "bygone"],

            # Time-related terms
            "recent": ["latest", "new", "current", "contemporary", "modern", "up-to-date"],
            "latest": ["recent", "new", "current", "newest", "most recent"],
            "current": ["present", "contemporary", "modern", "recent", "ongoing"],
            "modern": ["contemporary", "current", "recent", "present-day", "up-to-date"],

            # General academic
            "review": ["survey", "overview", "summary", "analysis", "examination"],
            "survey": ["review", "overview", "study", "examination", "analysis"],
            "theory": ["model", "framework", "hypothesis", "concept", "principle"],
            "model": ["theory", "framework", "system", "representation", "simulation"],
            "effect": ["impact", "influence", "consequence", "result", "outcome"],
            "impact": ["effect", "influence", "consequence", "result", "significance"]
        }

    def _extract_ngrams(self, text: str, n: int = 2) -> list[str]:
        """Extract n-grams from text."""
        words = self._tokenize_and_normalize(text)
        if len(words) < n:
            return words
        return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

    def _tokenize_and_normalize(self, text: str) -> list[str]:
        """Tokenize and normalize text."""
        # Convert to lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        # Remove stopwords
        words = [word for word in words if word not in self.stopwords and len(word) > 2]
        return words

    def _expand_query_with_synonyms(self, query: str) -> set[str]:
        """Expand query with synonyms."""
        expanded_terms = set()
        query_lower = query.lower()

        # Add original query terms
        original_terms = self._tokenize_and_normalize(query)
        expanded_terms.update(original_terms)

        # Add synonyms
        for term, synonyms in self.synonym_dictionary.items():
            if term in query_lower:
                expanded_terms.update(synonyms)

        # Add n-grams for phrase matching
        bigrams = self._extract_ngrams(query, 2)
        trigrams = self._extract_ngrams(query, 3)
        expanded_terms.update(bigrams)
        expanded_terms.update(trigrams)

        return expanded_terms

    def _flatten_taxonomy(self, taxonomy: dict, prefix: str = "") -> list[str]:
        """Flatten hierarchical taxonomy to get all keywords."""
        keywords = []

        if "keywords" in taxonomy:
            keywords.extend(taxonomy["keywords"])

        if "subcategories" in taxonomy:
            for subcat_name, subcat_data in taxonomy["subcategories"].items():
                if isinstance(subcat_data, list):
                    keywords.extend(subcat_data)
                else:
                    keywords.extend(self._flatten_taxonomy(subcat_data, f"{prefix}_{subcat_name}"))

        return keywords

    def _jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 and not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _tf_idf_score(self, query_terms: list[str], domain_keywords: list[str]) -> float:
        """Calculate TF-IDF style score for query-domain matching."""
        query_counter = Counter(query_terms)
        domain_counter = Counter(domain_keywords)

        score = 0.0
        total_domains = len(self.hierarchical_taxonomy)

        for term, tf in query_counter.items():
            if term in domain_counter:
                # Term frequency in domain (normalized)
                domain_tf = domain_counter[term] / len(domain_keywords)

                # Inverse document frequency (how rare the term is across domains)
                domains_with_term = sum(1 for domain_data in self.hierarchical_taxonomy.values()
                                      if term in self._flatten_taxonomy(domain_data))
                idf = math.log(total_domains / (domains_with_term + 1))

                score += tf * domain_tf * idf

        return score

    def classify_query_enhanced(self, query: str) -> dict[str, float]:
        """
        Enhanced query classification using multiple statistical methods.

        Args:
            query: Search query to classify

        Returns:
            Dictionary with domain scores (0.0 to 1.0)
        """
        # Expand query with synonyms and n-grams
        expanded_query_terms = self._expand_query_with_synonyms(query)
        query_words = self._tokenize_and_normalize(query)

        scores = {}

        for domain, domain_data in self.hierarchical_taxonomy.items():
            # Get all keywords for this domain (flattened)
            domain_keywords = self._flatten_taxonomy(domain_data)
            domain_keywords_set = set(domain_keywords)

            # Method 1: Jaccard similarity with expanded query
            jaccard_score = self._jaccard_similarity(expanded_query_terms, domain_keywords_set)

            # Method 2: TF-IDF style scoring
            tfidf_score = self._tf_idf_score(query_words, domain_keywords)

            # Method 3: N-gram overlap
            query_bigrams = set(self._extract_ngrams(query, 2))
            domain_bigrams = set()
            for i in range(len(domain_keywords) - 1):
                domain_bigrams.add(f"{domain_keywords[i]} {domain_keywords[i+1]}")

            ngram_score = self._jaccard_similarity(query_bigrams, domain_bigrams)

            # Method 4: Exact phrase matching bonus
            phrase_bonus = 0.0
            query_lower = query.lower()
            for keyword in domain_keywords:
                if len(keyword.split()) > 1 and keyword.lower() in query_lower:
                    phrase_bonus += 0.1  # Bonus for exact phrase matches

            # Combine scores with static weights
            combined_score = (
                0.4 * jaccard_score +      # Primary: Jaccard with synonyms
                0.3 * tfidf_score +        # Secondary: TF-IDF weighting
                0.2 * ngram_score +        # Tertiary: N-gram overlap
                0.1 * phrase_bonus         # Bonus: Exact phrases
            )

            scores[domain] = min(combined_score, 1.0)  # Cap at 1.0

        return scores

    def get_primary_topic_enhanced(self, query: str) -> str:
        """Get the primary topic category using enhanced classification."""
        scores = self.classify_query_enhanced(query)

        if not scores or max(scores.values()) == 0:
            return "general"

        return max(scores, key=scores.get)

    def get_subcategory_analysis(self, query: str, primary_domain: str) -> dict[str, float]:
        """Analyze subcategories within the primary domain."""
        if primary_domain not in self.hierarchical_taxonomy:
            return {}

        domain_data = self.hierarchical_taxonomy[primary_domain]
        if "subcategories" not in domain_data:
            return {}

        expanded_query_terms = self._expand_query_with_synonyms(query)
        subcategory_scores = {}

        for subcat_name, subcat_data in domain_data["subcategories"].items():
            if isinstance(subcat_data, list):
                subcat_keywords = set(subcat_data)
            else:
                subcat_keywords = set(self._flatten_taxonomy(subcat_data))

            score = self._jaccard_similarity(expanded_query_terms, subcat_keywords)
            subcategory_scores[subcat_name] = score

        return subcategory_scores

# Convenience functions for backward compatibility
def classify_query_topic_enhanced(query: str) -> dict[str, float]:
    """Enhanced version of classify_query_topic using statistical methods."""
    classifier = EnhancedTopicClassifier()
    return classifier.classify_query_enhanced(query)


def get_primary_topic_enhanced(query: str) -> str:
    """Enhanced version of get_primary_topic."""
    classifier = EnhancedTopicClassifier()
    return classifier.get_primary_topic_enhanced(query)
