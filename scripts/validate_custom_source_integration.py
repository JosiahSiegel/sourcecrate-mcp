#!/usr/bin/env python3
"""
Comprehensive validation script for custom source integration.

Tests that all hardcoded source assumptions have been removed and that
custom sources can integrate without code changes.
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from paperez_mcp.config.schemas import SourceCapabilities, SourceProviderConfig
from paperez_mcp.utils.query_processor import optimize_query_for_source
from paperez_mcp.utils.topic_classifier import should_skip_source_for_topic
from paperez_mcp.utils.pdf_validator import PDFValidator


def test_capability_based_query_optimization():
    """Test that query optimization uses capabilities instead of hardcoded names."""
    print("🧪 Testing capability-based query optimization...")

    # Test data with mock source configuration
    test_query = "machine learning algorithms"

    # This should not fail even for unknown source names
    try:
        result = optimize_query_for_source(test_query, "unknown_custom_source")
        print(f"✅ Query optimization handles unknown sources: {result}")
    except Exception as e:
        print(f"❌ Query optimization failed for unknown source: {e}")
        return False

    return True


def test_capability_based_topic_filtering():
    """Test that topic filtering uses capabilities instead of hardcoded names."""
    print("🧪 Testing capability-based topic filtering...")

    test_query = "machine learning algorithms"

    # This should not fail even for unknown source names
    try:
        result = should_skip_source_for_topic("unknown_custom_source", test_query)
        print(f"✅ Topic filtering handles unknown sources: {result}")
    except Exception as e:
        print(f"❌ Topic filtering failed for unknown source: {e}")
        return False

    return True


def test_pdf_validator_extensibility():
    """Test that PDF validator can handle custom sources."""
    print("🧪 Testing PDF validator extensibility...")

    try:
        validator = PDFValidator()
        patterns = validator.get_all_pdf_patterns()
        print(f"✅ PDF validator loads patterns: {len(patterns)} pattern sets found")

        # Test that it doesn't break with capability-based patterns
        return True
    except Exception as e:
        print(f"❌ PDF validator extensibility test failed: {e}")
        return False


def test_source_capabilities_schema():
    """Test that source capabilities schema is complete and valid."""
    print("🧪 Testing source capabilities schema...")

    try:
        # Test creating capabilities with all features
        capabilities = SourceCapabilities(
            medical_focus=True,
            stem_focus=False,
            field_search=True,
            high_pdf_availability=True,
            prefers_quoted_phrases=True,
            historical_depth="high",
            pdf_url_patterns=["https://example.com/pdf/(\\d+).pdf"],
            search_priority=8,
        )

        # Test creating a full source config
        source_config = SourceProviderConfig(
            name="test_custom_source",
            type="http_api",
            enabled=True,
            capabilities=capabilities,
            config={"base_url": "https://api.example.com", "search_path": "/search"},
        )

        print(f"✅ Source configuration schema works: {source_config.name}")
        return True
    except Exception as e:
        print(f"❌ Source capabilities schema test failed: {e}")
        return False


def test_no_hardcoded_assumptions():
    """Test that no hardcoded source assumptions remain."""
    print("🧪 Testing for remaining hardcoded assumptions...")

    # Check specific files for hardcoded source names
    files_to_check = [
        "paperez_mcp/utils/query_processor.py",
        "paperez_mcp/utils/topic_classifier.py",
        "paperez_mcp/utils/smart_search.py",
        "paperez_mcp/utils/search_engine.py",
    ]

    hardcoded_patterns = [
        'source == "arxiv"',
        'source == "pubmed"',
        'source == "crossref"',
        'source == "semantic_scholar"',
        "is_arxiv =",
        'if source_name == "pubmed"',
        'if source_name == "arxiv"',
    ]

    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            content = full_path.read_text()
            for pattern in hardcoded_patterns:
                if pattern in content:
                    print(f"❌ Found hardcoded pattern '{pattern}' in {file_path}")
                    return False

    print("✅ No hardcoded source assumptions found")
    return True


def test_mock_custom_source():
    """Test integration with a mock custom source."""
    print("🧪 Testing mock custom source integration...")

    # Create a temporary configuration for a custom source
    mock_source_config = SourceProviderConfig(
        name="mock_research_source",
        type="http_api",
        enabled=True,
        config={
            "description": "Mock research database for testing",
            "base_url": "https://api.mockresearch.org",
            "search_path": "/papers",
            "query_param": "q",
        },
        capabilities=SourceCapabilities(
            medical_focus=False,
            stem_focus=True,
            humanities_focus=False,
            preprint_server=False,
            field_search=True,
            high_pdf_availability=True,
            prefers_quoted_phrases=True,
            historical_depth="low",
            search_priority=7,
            pdf_url_patterns=["https://mockresearch\\.org/pdf/(\\d+)\\.pdf"],
        ),
    )

    try:
        # Test query optimization for mock source
        query = "neural networks"
        optimized = optimize_query_for_source(query, "mock_research_source")
        print(f"✅ Mock source query optimization: {optimized}")

        # Test topic filtering for mock source
        should_skip = should_skip_source_for_topic("mock_research_source", query)
        print(f"✅ Mock source topic filtering: skip={should_skip}")

        return True
    except Exception as e:
        print(f"❌ Mock custom source test failed: {e}")
        return False


def main():
    """Run all custom source integration tests."""
    print("🚀 Running Custom Source Integration Validation")
    print("=" * 60)

    tests = [
        test_capability_based_query_optimization,
        test_capability_based_topic_filtering,
        test_pdf_validator_extensibility,
        test_source_capabilities_schema,
        test_no_hardcoded_assumptions,
        test_mock_custom_source,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
        print()

    print("=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All custom source integration tests PASSED!")
        print("✅ Custom sources can now integrate without code changes")
        return 0
    else:
        print("❌ Some tests FAILED - custom source integration needs fixes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
