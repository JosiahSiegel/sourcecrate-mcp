#!/usr/bin/env python3
"""
CI-friendly configuration validation test.
Tests configuration loading without external API calls.
"""

import sys
from pathlib import Path

# Add the project root to Python path for local imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_configuration_loading():
    """Test that all configuration files load successfully."""
    try:
        from source_crate.config.manager import ConfigManager

        print("🔧 Testing configuration loading...")

        # Initialize config manager
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # Basic validation
        assert config is not None, "Configuration is None"
        assert hasattr(config, "sources"), "Configuration missing sources"
        assert hasattr(config, "categories"), "Configuration missing categories"

        sources_count = len(config.sources)
        categories_count = len(config.categories)

        print(f"✓ Loaded {sources_count} sources")
        print(f"✓ Loaded {categories_count} categories")

        # Validate minimum expected counts
        assert sources_count >= 10, f"Expected at least 10 sources, got {sources_count}"
        assert (
            categories_count >= 8
        ), f"Expected at least 8 categories, got {categories_count}"

        # Validate that all categories have at least one enabled source
        for category_name, category in config.categories.items():
            category_sources = getattr(category, "sources", [])
            assert (
                len(category_sources) > 0
            ), f"Category '{category_name}' has no sources"

            # Count enabled sources for this category
            enabled_sources_for_category = 0
            for source_name in category_sources:
                assert (
                    source_name in config.sources
                ), f"Category '{category_name}' references unknown source '{source_name}'"

                source = config.sources[source_name]
                if getattr(source, "enabled", True):
                    enabled_sources_for_category += 1

            # Warn if category has no enabled sources but don't fail (some may be intentionally disabled)
            if enabled_sources_for_category == 0:
                print(f"⚠️  Category '{category_name}' has no enabled sources")
            else:
                print(
                    f"✓ Category '{category_name}' has {enabled_sources_for_category} enabled sources"
                )

        print(f"✓ All {categories_count} categories have valid source references")

        # Validate source configurations
        enabled_sources = 0
        for source_name, source in config.sources.items():
            if getattr(source, "enabled", True):
                enabled_sources += 1

                # Validate required fields for enabled sources
                assert hasattr(source, "type"), f"Source '{source_name}' missing type"
                source_type = source.type

                if source_type == "http_api":
                    config_obj = getattr(source, "config", None)
                    assert (
                        config_obj is not None
                    ), f"HTTP API source '{source_name}' missing config"

                    # Check for required HTTP API fields
                    required_fields = ["base_url", "search_path"]
                    for field in required_fields:
                        # Handle both dict and object access patterns
                        if hasattr(config_obj, field):
                            field_value = getattr(config_obj, field, None)
                        elif hasattr(config_obj, "__getitem__"):
                            field_value = config_obj.get(field)
                        else:
                            field_value = None

                        if field_value is None or field_value == "":
                            print(
                                f"⚠️  Source '{source_name}' missing or empty field '{field}' - skipping validation"
                            )
                        else:
                            print(
                                f"✓ Source '{source_name}' has valid '{field}': {field_value[:50]}..."
                            )

        print(f"✓ Validated {enabled_sources} enabled sources")

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        import traceback

        traceback.print_exc()
        raise AssertionError(f"Configuration validation failed: {e}") from e


def test_yaml_file_discovery():
    """Test that YAML files are discovered correctly."""
    try:
        from source_crate.config.manager import ConfigManager

        print("📁 Testing YAML file discovery...")

        # Check that config directory exists
        ConfigManager()
        config_dirs = [Path(".paperez/config"), Path.home() / ".paperez/config"]

        found_files = False
        for config_dir in config_dirs:
            if config_dir.exists():
                yaml_files = list(config_dir.glob("*.yaml")) + list(
                    config_dir.glob("*.yml")
                )
                excluded_files = {"config.yaml", "minimal_config.yaml"}
                valid_files = [f for f in yaml_files if f.name not in excluded_files]

                if valid_files:
                    print(
                        f"✓ Found {len(valid_files)} YAML config files in {config_dir}"
                    )
                    for file in valid_files:
                        print(f"  - {file.name}")
                    found_files = True
                    break

        assert found_files, "No YAML configuration files found"

    except Exception as e:
        print(f"❌ YAML file discovery failed: {e}")
        raise AssertionError(f"YAML file discovery failed: {e}") from e


def test_search_analyzer():
    """Test search analysis functionality."""
    try:
        from source_crate.utils.enhanced_classifier import EnhancedTopicClassifier
        from source_crate.utils.query_intent import QueryIntentDetector

        print("🔍 Testing search analysis tools...")

        # Test query intent detector
        intent_detector = QueryIntentDetector()
        classifier = EnhancedTopicClassifier()

        # Test various query types
        test_queries = [
            "machine learning neural networks",
            "diabetes treatment clinical trial",
            "quantum computing algorithms",
            "federal regulation policy",
            "shakespeare literature analysis",
        ]

        for query in test_queries:
            # Test intent detection
            analysis = intent_detector.analyze_query(query)
            print(f"✓ Query '{query}' → Intent: {analysis.intent}")

            # Validate analysis structure
            assert hasattr(analysis, "intent"), "Analysis missing intent"
            assert hasattr(analysis, "confidence"), "Analysis missing confidence"

            # Confidence should be reasonable
            assert (
                0 <= analysis.confidence <= 1
            ), f"Invalid confidence score: {analysis.confidence}"

            # Test topic classification
            classification_scores = classifier.classify_query_enhanced(query)
            primary_topic = classifier.get_primary_topic_enhanced(query)
            print(f"✓ Query '{query}' → Primary Topic: {primary_topic}")
            print(
                f"  Classification scores: {list(classification_scores.keys())[:3]}"
            )  # Show top 3

        print("✓ Search analysis tools working correctly")

    except Exception as e:
        print(f"❌ Search analysis test failed: {e}")
        import traceback

        traceback.print_exc()
        raise AssertionError(f"Search analysis test failed: {e}") from e


def main():
    """Run all CI configuration tests."""
    print("=" * 60)
    print("SourceCrate CI Configuration Validation")
    print("=" * 60)

    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("YAML File Discovery", test_yaml_file_discovery),
        ("Search Analyzer", test_search_analyzer),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)

        try:
            test_func()  # Test functions now use assertions instead of returns
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n💥 {failed} TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
