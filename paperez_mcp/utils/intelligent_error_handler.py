"""
Intelligent error handling and suggestion system for content gaps.
Provides helpful suggestions when searches fail to find results.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchSuggestion:
    """A single search suggestion with reasoning"""
    suggestion: str
    reason: str
    suggested_category: str | None = None
    confidence: float = 0.8


class IntelligentErrorHandler:
    """Provides intelligent suggestions when searches fail"""

    def __init__(self) -> None:
        # Domain-specific suggestions based on common failure patterns
        self.domain_suggestions = {
            'medical': {
                'terms': ['medical', 'clinical', 'health', 'disease', 'therapy', 'treatment', 'diagnosis', 'surgery', 'medicine', 'drug', 'vaccine', 'patient', 'hospital'],
                'suggestions': [
                    SearchSuggestion(
                        suggestion="Try broader medical terms like 'treatment' instead of specific drug names",
                        reason="Medical databases may index papers differently",
                        suggested_category="medical"
                    ),
                    SearchSuggestion(
                        suggestion="Search for the condition name + 'management' or 'therapy'",
                        reason="Clinical literature often uses these standard terms",
                        suggested_category="medical"
                    ),
                    SearchSuggestion(
                        suggestion="Try searching for systematic reviews or meta-analyses",
                        reason="These provide comprehensive overviews of medical topics",
                        suggested_category="medical"
                    )
                ],
                'databases': ['PubMed', 'PubMed Central', 'ClinicalTrials.gov', 'Cochrane Library']
            },
            'historical': {
                'terms': ['history', 'historical', 'century', 'war', 'political', 'government', 'president', 'assassination', 'revolution'],
                'suggestions': [
                    SearchSuggestion(
                        suggestion="Try adding 'history' or 'political science' to your search",
                        reason="Historical events may be categorized under different academic disciplines",
                        suggested_category="historical"
                    ),
                    SearchSuggestion(
                        suggestion="Search for the time period (e.g., '1960s') + your topic",
                        reason="Academic papers often index by historical periods",
                        suggested_category="historical"
                    ),
                    SearchSuggestion(
                        suggestion="Look for documentary analysis or archival studies",
                        reason="Historical research often focuses on primary source analysis",
                        suggested_category="historical"
                    )
                ],
                'databases': ['JSTOR', 'Project MUSE', 'Historical Abstracts', 'National Archives']
            },
            'business': {
                'terms': ['business', 'company', 'corporate', 'partnership', 'market', 'industry', 'commercial', 'finance', 'economy'],
                'suggestions': [
                    SearchSuggestion(
                        suggestion="Try academic terms like 'strategic alliance' instead of 'partnership'",
                        reason="Business research uses formal academic terminology",
                        suggested_category="comprehensive"
                    ),
                    SearchSuggestion(
                        suggestion="Search for industry + 'case study' or 'market analysis'",
                        reason="Business literature often appears in case study format",
                        suggested_category="comprehensive"
                    ),
                    SearchSuggestion(
                        suggestion="Add 'economics' or 'management' to your search terms",
                        reason="Business topics are often studied in economics and management journals",
                        suggested_category="comprehensive"
                    )
                ],
                'databases': ['Business Source Premier', 'ABI/INFORM', 'EconLit', 'RePEc']
            },
            'technology': {
                'terms': ['technology', 'software', 'AI', 'artificial intelligence', 'machine learning', 'computer', 'algorithm', 'programming'],
                'suggestions': [
                    SearchSuggestion(
                        suggestion="Try more technical terms or add 'computer science' to your query",
                        reason="Technical literature uses precise academic terminology",
                        suggested_category="preprints"
                    ),
                    SearchSuggestion(
                        suggestion="Search on arXiv preprint server for latest research",
                        reason="Computer science research often appears on arXiv first",
                        suggested_category="preprints"
                    ),
                    SearchSuggestion(
                        suggestion="Include methodology terms like 'algorithm', 'framework', or 'system'",
                        reason="Computer science papers focus on technical methods",
                        suggested_category="preprints"
                    )
                ],
                'databases': ['arXiv', 'IEEE Xplore', 'ACM Digital Library', 'Computer Science Bibliography']
            }
        }

        # Query refinement patterns
        self.refinement_patterns = [
            {
                'pattern': r'\b(very|extremely|highly|quite)\s+',
                'replacement': '',
                'reason': 'Remove intensity modifiers that may not appear in academic titles'
            },
            {
                'pattern': r'\b(the best|top|leading|most popular)\s+',
                'replacement': '',
                'reason': 'Remove subjective qualifiers not found in academic literature'
            },
            {
                'pattern': r'\b(how to|step by step|guide to)\s+',
                'replacement': '',
                'reason': 'Academic papers rarely use instructional language in titles'
            },
            {
                'pattern': r'\b(recent|latest|new|current)\s+',
                'replacement': '',
                'reason': 'Remove temporal modifiers and search by publication date instead'
            }
        ]

    def detect_domain(self, query: str) -> str | None:
        """Detect the likely domain of a search query"""
        query_lower = query.lower()

        domain_scores = {}
        for domain, config in self.domain_suggestions.items():
            score = sum(1 for term in config['terms'] if term in query_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores, key=lambda x: domain_scores[x])
        return None

    def suggest_query_refinements(self, query: str) -> list[str]:
        """Suggest refined versions of the query"""
        refinements = []

        # Apply refinement patterns
        refined_query = query
        for pattern_config in self.refinement_patterns:
            original_query = refined_query
            refined_query = re.sub(pattern_config['pattern'], pattern_config['replacement'], refined_query, flags=re.IGNORECASE)
            if refined_query != original_query and refined_query.strip():
                refinements.append(refined_query.strip())

        # Suggest more academic phrasing
        academic_replacements = {
            'effect of': 'impact of',
            'relationship between': 'correlation between',
            'difference between': 'comparison of',
            'benefits of': 'advantages of',
            'problems with': 'challenges in',
            'caused by': 'associated with'
        }

        for original, replacement in academic_replacements.items():
            if original in query.lower():
                academic_query = re.sub(re.escape(original), replacement, query, flags=re.IGNORECASE)
                if academic_query != query:
                    refinements.append(academic_query)

        return refinements[:3]  # Return top 3 refinements

    def generate_error_message(self,
                              query: str,
                              sources_searched: list[str],
                              fallback_used: bool = False) -> dict[str, Any]:
        """Generate an intelligent error message with suggestions"""

        domain = self.detect_domain(query)
        suggestions: list[SearchSuggestion | str] = []

        # Base message
        if fallback_used:
            base_message = f"No papers found for '{query}' even after searching comprehensive sources."
        else:
            base_message = f"No papers found for '{query}' in the searched databases."

        # Domain-specific suggestions
        if domain and domain in self.domain_suggestions:
            domain_config = self.domain_suggestions[domain]
            suggestions.extend(domain_config['suggestions'])

            # Add database recommendations
            missing_databases = [db for db in domain_config['databases']
                               if not any(db.lower().replace(' ', '_') in src for src in sources_searched)]
            if missing_databases:
                suggestions.append(SearchSuggestion(
                    suggestion=f"Consider searching specialized databases: {', '.join(missing_databases)}",
                    reason=f"These databases have better coverage for {domain} research",
                    confidence=0.9
                ))

        # Query refinement suggestions
        refinements = self.suggest_query_refinements(query)
        if refinements:
            for refinement in refinements:
                suggestions.append(SearchSuggestion(
                    suggestion=f"Try: '{refinement}'",
                    reason="Simplified query may match more academic papers",
                    confidence=0.7
                ))

        # General suggestions if no domain detected
        if not domain:
            suggestions.extend([
                SearchSuggestion(
                    suggestion="Try broader search terms",
                    reason="Academic papers may use different terminology",
                    confidence=0.6
                ),
                SearchSuggestion(
                    suggestion="Check spelling and try alternative terms",
                    reason="Small variations can significantly affect search results",
                    confidence=0.8
                ),
                SearchSuggestion(
                    suggestion="Search for review papers or surveys on your topic",
                    reason="Review papers provide good starting points and references",
                    confidence=0.7
                )
            ])

        # Force category suggestions based on domain
        suggested_categories = []
        if domain == 'medical':
            suggested_categories = ['medical', 'journals']
        elif domain == 'historical':
            suggested_categories = ['historical', 'comprehensive']
        elif domain == 'technology':
            suggested_categories = ['preprints', 'recent']
        elif domain == 'business':
            suggested_categories = ['comprehensive', 'journals']

        return {
            'message': base_message,
            'domain_detected': domain,
            'suggestions': [
                {
                    'text': s.suggestion if isinstance(s, SearchSuggestion) else s,
                    'reason': s.reason if isinstance(s, SearchSuggestion) else "",
                    'confidence': s.confidence if isinstance(s, SearchSuggestion) else 0.0,
                    'suggested_category': s.suggested_category if isinstance(s, SearchSuggestion) else None
                }
                for s in suggestions[:5]  # Limit to top 5 suggestions
            ],
            'suggested_categories': suggested_categories,
            'query_refinements': refinements,
            'help_text': self._generate_help_text(domain)
        }

    def _generate_help_text(self, domain: str | None) -> str:
        """Generate helpful context based on domain"""
        if domain == 'medical':
            return ("Medical research tip: PubMed and PMC contain the most comprehensive "
                   "biomedical literature. Clinical trial data is available through ClinicalTrials.gov.")
        elif domain == 'historical':
            return ("Historical research tip: Academic databases focus on peer-reviewed historical "
                   "research rather than news archives or popular accounts.")
        elif domain == 'business':
            return ("Business research tip: Academic business research often uses formal terminology "
                   "and appears in management, economics, or finance journals.")
        elif domain == 'technology':
            return ("Technology research tip: Latest computer science research often appears on "
                   "arXiv preprint server before formal publication.")
        else:
            return ("Search tip: Academic databases index peer-reviewed research papers. "
                   "Try using the terminology found in academic abstracts and titles.")


# Global instance
error_handler = IntelligentErrorHandler()
