"""
User-friendly error handling and messaging utilities.
Provides enhanced error messages with actionable suggestions and context.
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Context information for enhanced error messages."""

    operation: str
    user_input: Any
    system_state: dict[str, Any]
    suggested_actions: list[str]
    help_links: list[str]
    error_category: str
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class EnhancedError:
    """Enhanced error with user-friendly messaging."""

    original_error: str
    user_message: str
    technical_details: str
    suggested_actions: list[str]
    help_links: list[str]
    error_code: str
    severity: str
    context: dict[str, Any]


class UserFriendlyErrorHandler:
    """
    Handles conversion of technical errors to user-friendly messages.

    Features:
    - Context-aware error categorization
    - Actionable suggestion generation
    - Progressive disclosure of technical details
    - Help resource recommendations
    """

    def __init__(self) -> None:
        self.error_patterns = self._initialize_error_patterns()
        self.suggestion_templates = self._initialize_suggestions()
        self.help_resources = self._initialize_help_resources()

    def _initialize_error_patterns(self) -> dict[str, dict[str, Any]]:
        """Initialize error pattern recognition."""
        return {
            "network_errors": {
                "patterns": [
                    r"Connection.*timeout",
                    r"Network.*unreachable",
                    r"DNS.*resolution.*failed",
                    r"HTTP.*error.*[45]\d\d",
                    r"SSL.*certificate.*error",
                    r"Request.*timeout",
                ],
                "category": "network",
                "severity": "medium",
            },
            "configuration_errors": {
                "patterns": [
                    r"Configuration.*error",
                    r"Invalid.*config",
                    r"Missing.*configuration",
                    r"Configuration.*file.*not.*found",
                    r"Config.*file.*not.*found",
                ],
                "category": "configuration",
                "severity": "high",
            },
            "file_errors": {
                "patterns": [
                    r"File.*not.*found",
                    r"Permission.*denied",
                    r"Directory.*not.*found",
                    r"No such file or directory",
                    r"Access.*denied",
                    r"Disk.*full",
                    r"Invalid.*path",
                ],
                "category": "file_system",
                "severity": "medium",
            },
            "pdf_errors": {
                "patterns": [
                    r"PDF.*corrupt",
                    r"Invalid.*PDF",
                    r"Cannot.*extract.*text",
                    r"PDF.*encrypted",
                    r"Password.*protected",
                    r"PyMuPDF.*error",
                ],
                "category": "pdf_processing",
                "severity": "medium",
            },
            "api_errors": {
                "patterns": [
                    r"API.*key.*invalid",
                    r"Rate.*limit.*exceeded",
                    r"API.*quota.*exceeded",
                    r"Authentication.*failed",
                    r"Unauthorized.*access",
                    r"Service.*unavailable",
                ],
                "category": "api_access",
                "severity": "high",
            },
            "search_errors": {
                "patterns": [
                    r"No.*results.*found",
                    r"Search.*failed",
                    r"Query.*too.*broad",
                    r"Query.*too.*specific",
                    r"Invalid.*search.*term",
                ],
                "category": "search_query",
                "severity": "low",
            },
        }

    def _initialize_suggestions(self) -> dict[str, list[str]]:
        """Initialize suggestion templates for different error types."""
        return {
            "network": [
                "Check your internet connection and try again",
                "If using a VPN, try disconnecting and reconnecting",
                "Wait a few minutes and retry - the service may be temporarily down",
                "Check if the API endpoint is accessible from your network",
            ],
            "file_system": [
                "Verify the file path is correct and the file exists",
                "Check file permissions - you may need read/write access",
                "Ensure the directory exists before saving files",
                "Free up disk space if storage is full",
            ],
            "pdf_processing": [
                "Try a different PDF file to test if the issue is file-specific",
                "Ensure the PDF is not password-protected or encrypted",
                "Check if the PDF file is corrupted by opening it in a PDF viewer",
                "For large PDFs, try processing smaller sections first",
            ],
            "api_access": [
                "Verify your API keys are correctly configured",
                "Check if you've exceeded your API rate limits",
                "Ensure your API subscription is active and not expired",
                "Try again later if the service is temporarily unavailable",
            ],
            "search_query": [
                "Try refining your search terms - be more specific",
                "Use different keywords or synonyms for your topic",
                "Check spelling and remove special characters",
                "Try a broader search if your query is too specific",
            ],
            "configuration": [
                "Check the configuration file format and syntax",
                "Ensure all required configuration fields are present",
                "Verify file paths in configuration are correct",
                "Restore default configuration if custom settings cause issues",
            ],
        }

    def _initialize_help_resources(self) -> dict[str, list[str]]:
        """Initialize help resources for different error categories."""
        return {
            "network": [
                "Network troubleshooting guide",
                "API endpoint documentation",
                "Firewall configuration help",
            ],
            "file_system": [
                "File permissions guide",
                "Path specification documentation",
                "Storage management help",
            ],
            "pdf_processing": [
                "PDF processing troubleshooting",
                "Supported PDF formats guide",
                "Alternative conversion methods",
            ],
            "api_access": [
                "API key setup guide",
                "Rate limiting documentation",
                "Authentication troubleshooting",
            ],
            "search_query": [
                "Search optimization tips",
                "Query syntax guide",
                "Academic search best practices",
            ],
            "configuration": [
                "Configuration file reference",
                "Setup and installation guide",
                "Default configuration restore",
            ],
        }

    def categorize_error(self, error_message: str) -> tuple[str, str]:
        """Categorize error based on message content."""
        error_lower = error_message.lower()

        for _error_type, config in self.error_patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, error_lower, re.IGNORECASE):
                    return config["category"], config["severity"]

        return "unknown", "medium"

    def enhance_error(
        self,
        original_error: str,
        operation: str = "operation",
        context: dict[str, Any] | None = None,
        user_input: Any = None,
    ) -> EnhancedError:
        """
        Convert a technical error into a user-friendly enhanced error.

        Args:
            original_error: The original technical error message
            operation: Description of what operation failed
            context: Additional context about the error
            user_input: The user's input that caused the error

        Returns:
            EnhancedError with user-friendly messaging and suggestions
        """
        category, severity = self.categorize_error(original_error)

        # Generate user-friendly message
        user_message = self._generate_user_message(original_error, operation, category)

        # Get suggestions for this error category
        suggestions = self.suggestion_templates.get(
            category,
            [
                "Try the operation again",
                "Check your input parameters",
                "Contact support if the problem persists",
            ],
        )

        # Get help resources
        help_links = self.help_resources.get(
            category, ["General troubleshooting guide"]
        )

        # Generate error code
        error_code = self._generate_error_code(category, operation)

        # Add context-specific suggestions
        contextual_suggestions = self._generate_contextual_suggestions(
            original_error, operation, context, user_input
        )

        all_suggestions = suggestions + contextual_suggestions

        return EnhancedError(
            original_error=original_error,
            user_message=user_message,
            technical_details=self._format_technical_details(original_error, context),
            suggested_actions=all_suggestions[:5],  # Limit to top 5 suggestions
            help_links=help_links,
            error_code=error_code,
            severity=severity,
            context=context or {},
        )

    def _generate_user_message(self, error: str, operation: str, category: str) -> str:
        """Generate a user-friendly error message."""
        category_messages = {
            "network": f"Unable to complete {operation} due to network connectivity issues.",
            "file_system": f"Cannot access the requested file or directory for {operation}.",
            "pdf_processing": f"Unable to process the PDF file during {operation}.",
            "api_access": f"Cannot access the required service API for {operation}.",
            "search_query": f"No results found or search query issue during {operation}.",
            "configuration": f"Configuration problem preventing {operation}.",
            "unknown": f"An unexpected error occurred during {operation}.",
        }

        return category_messages.get(category, category_messages["unknown"])

    def _generate_error_code(self, category: str, operation: str) -> str:
        """Generate a user-friendly error code."""
        category_codes = {
            "network": "NET",
            "file_system": "FILE",
            "pdf_processing": "PDF",
            "api_access": "API",
            "search_query": "SEARCH",
            "configuration": "CONFIG",
            "unknown": "GEN",
        }

        code_prefix = category_codes.get(category, "GEN")
        operation_code = operation.upper().replace(" ", "_")[:8]

        return f"{code_prefix}_{operation_code}"

    def _format_technical_details(
        self, error: str, context: dict[str, Any] | None
    ) -> str:
        """Format technical details for advanced users."""
        details = [f"Original error: {error}"]

        if context:
            if "timestamp" in context:
                details.append(f"Timestamp: {context['timestamp']}")
            if "operation_id" in context:
                details.append(f"Operation ID: {context['operation_id']}")
            if "system_info" in context:
                details.append(f"System: {context['system_info']}")

        return " | ".join(details)

    def _generate_contextual_suggestions(
        self,
        error: str,
        operation: str,
        context: dict[str, Any] | None,
        user_input: Any,
    ) -> list[str]:
        """Generate context-specific suggestions."""
        suggestions = []

        # File path specific suggestions
        if user_input and isinstance(user_input, str):
            if not os.path.exists(user_input) and (
                "file" in operation.lower() or "pdf" in operation.lower()
            ):
                suggestions.append(f"Check if the file path '{user_input}' is correct")

            if user_input.startswith("http") and "network" in error.lower():
                suggestions.append("Try downloading the file manually first")

        # PDF specific suggestions
        if "pdf" in operation.lower():
            suggestions.append("Ensure the PDF is not corrupted or password-protected")

        # Search specific suggestions
        if "search" in operation.lower() and user_input:
            if isinstance(user_input, str) and len(user_input) < 3:
                suggestions.append(
                    "Try using longer search terms (at least 3 characters)"
                )

        # API specific suggestions
        if context and context.get("api_status"):
            failed_apis = [k for k, v in context["api_status"].items() if not v]
            if failed_apis:
                suggestions.append(
                    f"The following APIs are currently unavailable: {', '.join(failed_apis)}"
                )

        return suggestions

    def format_error_response(self, enhanced_error: EnhancedError) -> dict[str, Any]:
        """Format enhanced error for API response."""
        return {
            "success": False,
            "error": {
                "message": enhanced_error.user_message,
                "code": enhanced_error.error_code,
                "severity": enhanced_error.severity,
                "suggestions": enhanced_error.suggested_actions,
                "help_resources": enhanced_error.help_links,
                "technical_details": enhanced_error.technical_details,
                "context": enhanced_error.context,
            },
            "user_friendly": True,
            "timestamp": enhanced_error.context.get("timestamp"),
            "operation": enhanced_error.context.get("operation"),
        }


class SearchErrorEnhancer:
    """Specialized error enhancer for search operations."""

    def __init__(self) -> None:
        self.domain_keywords = {
            "medical": [
                "covid",
                "cancer",
                "treatment",
                "clinical",
                "patient",
                "diagnosis",
            ],
            "computer_science": [
                "algorithm",
                "machine learning",
                "neural",
                "computing",
                "software",
                "artificial intelligence",
                "programming",
                "data science",
                "algorithms",
            ],
            "physics": [
                "quantum",
                "particle",
                "relativity",
                "thermodynamics",
                "mechanics",
            ],
            "chemistry": ["molecular", "synthesis", "catalyst", "reaction", "compound"],
            "biology": [
                "genome",
                "protein",
                "evolution",
                "cell",
                "organism",
                "genetic",
                "gene",
                "expression",
                "dna",
                "rna",
                "molecular biology",
                "biochemistry",
            ],
        }

    def enhance_no_results_error(
        self, query: str, search_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Enhance 'no results found' errors with intelligent suggestions."""

        # Detect domain
        detected_domain = self._detect_domain(query)

        # Generate suggestions based on query analysis
        suggestions = []
        query_refinements = []

        # Query length analysis
        if len(query.split()) == 1:
            suggestions.append("Try adding more specific terms to narrow your search")
            query_refinements.append(f'"{query}" + "review"')
            query_refinements.append(f'"{query}" + "analysis"')
        elif len(query.split()) > 8:
            suggestions.append("Try simplifying your search with fewer keywords")
            key_terms = query.split()[:3]
            query_refinements.append(" ".join(key_terms))

        # Domain-specific suggestions
        if detected_domain:
            domain_suggestions = self._get_domain_suggestions(detected_domain)
            suggestions.extend(domain_suggestions)

        # Search strategy suggestions
        if not any(char in query for char in ['"', "AND", "OR"]):
            suggestions.append('Try using quotes for exact phrases: "machine learning"')

        # Category suggestions based on domain
        suggested_categories = self._suggest_categories(detected_domain, query)

        return {
            "message": f"No papers found for '{query}'. Try refining your search.",
            "domain_detected": detected_domain,
            "suggestions": suggestions,
            "query_refinements": query_refinements,
            "suggested_categories": suggested_categories,
            "help_text": "Use more specific terms, try synonyms, or check spelling",
            "search_tips": [
                "Use quotes for exact phrases",
                "Try synonyms or alternative terms",
                "Check spelling and remove special characters",
                "Use broader terms if search is too specific",
            ],
        }

    def _detect_domain(self, query: str) -> str | None:
        """Detect academic domain from query terms."""
        query_lower = query.lower()

        for domain, keywords in self.domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return str(domain)

        return None

    def _get_domain_suggestions(self, domain: str) -> list[str]:
        """Get domain-specific search suggestions."""
        domain_suggestions = {
            "medical": [
                "Try searching in medical databases using the 'medical' category",
                "Include terms like 'clinical trial', 'study', or 'research'",
                "Search for specific medical conditions or treatments",
            ],
            "computer_science": [
                "Try the 'preprints' category for latest CS research",
                "Include algorithm names or specific technologies",
                "Search for conference proceedings or journal articles",
            ],
            "physics": [
                "Try 'recent' category for latest physics research",
                "Include specific physics subfields in your search",
                "Search for experimental or theoretical work specifically",
            ],
            "chemistry": [
                "Include chemical compound names or reaction types",
                "Search for synthesis methods or analysis techniques",
                "Try including journal names like 'chemistry' or 'chemical'",
            ],
            "biology": [
                "Include species names or biological processes",
                "Try 'medical' category for biomedical research",
                "Search for specific genes, proteins, or pathways",
            ],
        }

        return domain_suggestions.get(domain, [])

    def _suggest_categories(self, domain: str | None, query: str) -> list[str]:
        """Suggest search categories based on domain and query."""
        if not domain:
            return ["journals", "preprints"]

        category_mapping = {
            "medical": ["medical", "journals"],
            "computer_science": ["preprints", "recent"],
            "physics": ["preprints", "recent"],
            "chemistry": ["journals", "open_access"],
            "biology": ["medical", "journals"],
        }

        return category_mapping.get(domain, ["journals", "preprints"])


# Global instances for easy reuse
error_handler = UserFriendlyErrorHandler()
search_error_enhancer = SearchErrorEnhancer()


def enhance_error(
    error: str,
    operation: str = "operation",
    context: dict[str, Any] | None = None,
    user_input: Any = None,
) -> dict[str, Any]:
    """
    Convenience function to enhance any error with user-friendly messaging.

    Args:
        error: Original error message
        operation: Description of the operation that failed
        context: Additional context information
        user_input: The user input that caused the error

    Returns:
        Dictionary with enhanced error information
    """
    enhanced = error_handler.enhance_error(error, operation, context, user_input)
    return error_handler.format_error_response(enhanced)


def enhance_search_error(query: str, search_context: dict[str, Any]) -> dict[str, Any]:
    """
    Enhance search-specific errors with intelligent suggestions.

    Args:
        query: The search query that produced no results
        search_context: Context about the search operation

    Returns:
        Dictionary with enhanced search error information
    """
    return search_error_enhancer.enhance_no_results_error(query, search_context)
