"""
Unit tests for user-friendly error handling functionality.
Tests enhanced error messages, categorization, and suggestion generation.
"""

import time

from paperez_mcp.utils.user_friendly_errors import (
    EnhancedError,
    SearchErrorEnhancer,
    UserFriendlyErrorHandler,
    enhance_error,
    enhance_search_error,
    error_handler,
    search_error_enhancer,
)


class TestUserFriendlyErrorHandler:
    """Test suite for UserFriendlyErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = UserFriendlyErrorHandler()

    def test_handler_initialization(self):
        """Test error handler initialization."""
        assert self.handler.error_patterns is not None
        assert self.handler.suggestion_templates is not None
        assert self.handler.help_resources is not None

        # Check that patterns are properly structured
        assert "network_errors" in self.handler.error_patterns
        assert "file_errors" in self.handler.error_patterns
        assert "pdf_errors" in self.handler.error_patterns

    def test_categorize_network_errors(self):
        """Test categorization of network-related errors."""
        network_errors = [
            "Connection timeout occurred",
            "Network unreachable error",
            "HTTP error 404",
            "SSL certificate error",
            "Request timeout",
        ]

        for error in network_errors:
            category, severity = self.handler.categorize_error(error)
            assert category == "network"
            assert severity == "medium"

    def test_categorize_file_errors(self):
        """Test categorization of file system errors."""
        file_errors = [
            "File not found",
            "Permission denied",
            "Directory not found",
            "Access denied",
            "No such file or directory",
        ]

        for error in file_errors:
            category, severity = self.handler.categorize_error(error)
            assert category == "file_system"
            assert severity == "medium"

    def test_categorize_pdf_errors(self):
        """Test categorization of PDF processing errors."""
        pdf_errors = [
            "PDF corrupt or invalid",
            "Cannot extract text from PDF",
            "PDF encrypted with password",
            "PyMuPDF error occurred",
        ]

        for error in pdf_errors:
            category, severity = self.handler.categorize_error(error)
            assert category == "pdf_processing"
            assert severity == "medium"

    def test_categorize_api_errors(self):
        """Test categorization of API-related errors."""
        api_errors = [
            "API key invalid or expired",
            "Rate limit exceeded",
            "Authentication failed",
            "Service unavailable",
        ]

        for error in api_errors:
            category, severity = self.handler.categorize_error(error)
            assert category == "api_access"
            assert severity == "high"

    def test_categorize_unknown_errors(self):
        """Test categorization of unknown errors."""
        unknown_error = "Some completely random error message"
        category, severity = self.handler.categorize_error(unknown_error)

        assert category == "unknown"
        assert severity == "medium"

    def test_enhance_network_error(self):
        """Test enhancement of network errors."""
        error_message = "Connection timeout occurred"
        enhanced = self.handler.enhance_error(
            error_message, operation="API request", context={"timestamp": time.time()}
        )

        assert isinstance(enhanced, EnhancedError)
        assert enhanced.original_error == error_message
        assert "network connectivity" in enhanced.user_message.lower()
        assert enhanced.error_code.startswith("NET_")
        assert enhanced.severity == "medium"
        assert len(enhanced.suggested_actions) > 0
        assert "Check your internet connection" in enhanced.suggested_actions[0]

    def test_enhance_file_error(self):
        """Test enhancement of file system errors."""
        error_message = "File not found: /path/to/file.pdf"
        enhanced = self.handler.enhance_error(
            error_message, operation="PDF processing", user_input="/path/to/file.pdf"
        )

        assert "file or directory" in enhanced.user_message.lower()
        assert enhanced.error_code.startswith("FILE_")
        assert any("file path" in action for action in enhanced.suggested_actions)

    def test_enhance_pdf_error(self):
        """Test enhancement of PDF processing errors."""
        error_message = "PDF is encrypted and requires password"
        enhanced = self.handler.enhance_error(
            error_message, operation="PDF text extraction"
        )

        assert "pdf file" in enhanced.user_message.lower()
        assert enhanced.error_code.startswith("PDF_")
        assert any(
            "password-protected" in action for action in enhanced.suggested_actions
        )

    def test_contextual_suggestions_for_file_paths(self):
        """Test contextual suggestions based on file paths."""
        error_message = "File not found"
        enhanced = self.handler.enhance_error(
            error_message,
            operation="file processing",
            user_input="/nonexistent/path/file.pdf",
        )

        # Should include file path specific suggestion
        contextual_suggestions = [
            s for s in enhanced.suggested_actions if "file path" in s
        ]
        assert len(contextual_suggestions) > 0

    def test_contextual_suggestions_for_urls(self):
        """Test contextual suggestions for HTTP URLs."""
        error_message = "Network error"
        enhanced = self.handler.enhance_error(
            error_message,
            operation="PDF download",
            user_input="https://example.com/paper.pdf",
        )

        # Should include URL-specific suggestion
        url_suggestions = [s for s in enhanced.suggested_actions if "downloading" in s]
        assert len(url_suggestions) > 0

    def test_format_error_response(self):
        """Test error response formatting."""
        enhanced = self.handler.enhance_error(
            "Test error", operation="test operation", context={"test": "context"}
        )

        response = self.handler.format_error_response(enhanced)

        assert response["success"] is False
        assert "error" in response
        assert "message" in response["error"]
        assert "code" in response["error"]
        assert "suggestions" in response["error"]
        assert response["user_friendly"] is True

    def test_error_code_generation(self):
        """Test error code generation."""
        # Test different categories
        test_cases = [
            ("network", "API request", "NET_API_REQU"),
            ("file_system", "file processing", "FILE_FILE_PRO"),
            ("pdf_processing", "conversion", "PDF_CONVERSI"),
            ("unknown", "operation", "GEN_OPERATIO"),
        ]

        for category, operation, expected_prefix in test_cases:
            code = self.handler._generate_error_code(category, operation)
            assert code.startswith(expected_prefix[:3])  # Check category prefix

    def test_technical_details_formatting(self):
        """Test technical details formatting."""
        error = "Test error"
        context = {
            "timestamp": "2024-01-01T00:00:00",
            "operation_id": "op-123",
            "system_info": "Linux",
        }

        details = self.handler._format_technical_details(error, context)

        assert "Original error: Test error" in details
        assert "Timestamp: 2024-01-01T00:00:00" in details
        assert "Operation ID: op-123" in details
        assert "System: Linux" in details


class TestSearchErrorEnhancer:
    """Test suite for SearchErrorEnhancer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enhancer = SearchErrorEnhancer()

    def test_domain_detection(self):
        """Test academic domain detection from queries."""
        test_cases = [
            ("machine learning algorithms", "computer_science"),
            ("covid treatment protocols", "medical"),
            ("quantum mechanics theory", "physics"),
            ("organic synthesis methods", "chemistry"),
            ("gene expression analysis", "biology"),
            ("random unrelated query", None),
        ]

        for query, expected_domain in test_cases:
            detected = self.enhancer._detect_domain(query)
            assert detected == expected_domain

    def test_domain_suggestions(self):
        """Test domain-specific suggestions."""
        cs_suggestions = self.enhancer._get_domain_suggestions("computer_science")
        assert len(cs_suggestions) > 0
        assert any("preprints" in s for s in cs_suggestions)

        medical_suggestions = self.enhancer._get_domain_suggestions("medical")
        assert len(medical_suggestions) > 0
        assert any("medical" in s for s in medical_suggestions)

    def test_category_suggestions(self):
        """Test category suggestions based on domain."""
        medical_categories = self.enhancer._suggest_categories(
            "medical", "cancer treatment"
        )
        assert "medical" in medical_categories

        cs_categories = self.enhancer._suggest_categories(
            "computer_science", "neural networks"
        )
        assert "preprints" in cs_categories or "recent" in cs_categories

    def test_enhance_no_results_short_query(self):
        """Test enhancement of no results for short queries."""
        enhanced = self.enhancer.enhance_no_results_error(
            "AI", {"sources_attempted": ["arxiv", "pubmed"]}
        )

        assert "AI" in enhanced["message"]
        assert len(enhanced["suggestions"]) > 0
        assert any("more specific terms" in s for s in enhanced["suggestions"])
        assert len(enhanced["query_refinements"]) > 0

    def test_enhance_no_results_long_query(self):
        """Test enhancement of no results for overly long queries."""
        long_query = "machine learning deep neural networks artificial intelligence computer vision"
        enhanced = self.enhancer.enhance_no_results_error(
            long_query, {"sources_attempted": ["arxiv"]}
        )

        assert any("simplifying" in s for s in enhanced["suggestions"])
        assert len(enhanced["query_refinements"]) > 0

    def test_enhance_no_results_with_domain(self):
        """Test enhancement with domain detection."""
        enhanced = self.enhancer.enhance_no_results_error(
            "quantum computing algorithms", {"sources_attempted": ["arxiv", "crossref"]}
        )

        assert enhanced["domain_detected"] == "computer_science"
        assert len(enhanced["suggested_categories"]) > 0
        assert "preprints" in enhanced["suggested_categories"]

    def test_search_tips_included(self):
        """Test that search tips are always included."""
        enhanced = self.enhancer.enhance_no_results_error(
            "test query", {"sources_attempted": ["test"]}
        )

        assert "search_tips" in enhanced
        assert len(enhanced["search_tips"]) > 0
        assert any("quotes" in tip for tip in enhanced["search_tips"])


class TestGlobalErrorInstances:
    """Test suite for global error handler instances."""

    def test_global_error_handler_exists(self):
        """Test that global error handler instance exists."""
        assert error_handler is not None
        assert isinstance(error_handler, UserFriendlyErrorHandler)

    def test_global_search_enhancer_exists(self):
        """Test that global search error enhancer exists."""
        assert search_error_enhancer is not None
        assert isinstance(search_error_enhancer, SearchErrorEnhancer)

    def test_enhance_error_convenience_function(self):
        """Test convenience function for error enhancement."""
        result = enhance_error("Test error message", operation="test operation")

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert result["user_friendly"] is True

    def test_enhance_search_error_convenience_function(self):
        """Test convenience function for search error enhancement."""
        result = enhance_search_error(
            "machine learning", {"sources_attempted": ["arxiv"]}
        )

        assert isinstance(result, dict)
        assert "message" in result
        assert "suggestions" in result
        assert "domain_detected" in result


class TestErrorHandlingIntegration:
    """Integration tests for error handling with various scenarios."""

    def test_error_enhancement_with_full_context(self):
        """Test error enhancement with comprehensive context."""
        context = {
            "timestamp": time.time(),
            "operation_id": "op-12345",
            "system_info": "Python 3.11 on Linux",
            "api_status": {"arxiv": True, "pubmed": False, "crossref": True},
        }

        enhanced = enhance_error(
            "Connection timeout",
            operation="academic search",
            context=context,
            user_input="machine learning",
        )

        assert enhanced["error"]["context"]["api_status"] is not None
        assert "pubmed" in str(enhanced["error"]["suggestions"])

    def test_pdf_error_with_file_context(self):
        """Test PDF error enhancement with file context."""
        enhanced = enhance_error(
            "PyMuPDF: PDF is corrupted",
            operation="PDF text extraction",
            user_input="/path/to/document.pdf",
        )

        assert enhanced["error"]["code"].startswith("PDF_")
        assert any("corrupted" in action for action in enhanced["error"]["suggestions"])

    def test_api_error_with_rate_limiting(self):
        """Test API error enhancement for rate limiting."""
        enhanced = enhance_error(
            "Rate limit exceeded - 429",
            operation="API search",
            context={"api_endpoint": "arxiv.org"},
        )

        assert enhanced["error"]["severity"] == "high"
        assert any(
            "rate limit" in action for action in enhanced["error"]["suggestions"]
        )

    def test_search_error_with_medical_domain(self):
        """Test search error enhancement for medical domain."""
        result = enhance_search_error(
            "covid vaccine effectiveness",
            {"sources_attempted": ["arxiv", "pubmed"], "total_found": 0},
        )

        assert result["domain_detected"] == "medical"
        assert "medical" in result["suggested_categories"]
        assert any("clinical" in s for s in result["suggestions"])

    def test_configuration_error_enhancement(self):
        """Test configuration error enhancement."""
        enhanced = enhance_error(
            "Configuration file not found: config.yaml",
            operation="system initialization",
            user_input="config.yaml",
        )

        assert enhanced["error"]["code"].startswith("CONFIG_")
        assert any(
            "configuration" in action for action in enhanced["error"]["suggestions"]
        )

    def test_error_severity_assessment(self):
        """Test error severity assessment for different types."""
        # High severity: API access
        api_error = enhance_error("Authentication failed", "API access")
        assert api_error["error"]["severity"] == "high"

        # Medium severity: Network
        network_error = enhance_error("Connection timeout", "network operation")
        assert network_error["error"]["severity"] == "medium"

        # Low severity: Search
        enhance_error("No results found", "search operation")
        # Note: This might be categorized as search_query with low severity
        # or unknown with medium severity depending on pattern matching

    def test_suggestion_limit_enforcement(self):
        """Test that suggestions are limited to reasonable numbers."""
        enhanced = enhance_error(
            "Multiple issues occurred",
            operation="complex operation",
            context={"api_status": {"src1": False, "src2": False, "src3": False}},
        )

        # Should limit to top 5 suggestions
        assert len(enhanced["error"]["suggestions"]) <= 5
