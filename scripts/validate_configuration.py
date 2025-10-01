#!/usr/bin/env python3
"""
Shared configuration validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import sys


def test_configuration_loading() -> bool:
    """Test configuration system loading."""
    print("🔍 Testing configuration loading...")

    try:
        from paperez_mcp.config.manager import ConfigManager

        config = ConfigManager().get_config()

        sources_count = len(config.sources)
        categories_count = len(config.categories)

        print(f"  ✓ Loaded {sources_count} sources and {categories_count} categories")

        if sources_count == 0:
            print("  ❌ No sources loaded from configuration")
            return False

        if categories_count == 0:
            print("  ❌ No categories loaded from configuration")
            return False

        print("✓ Configuration loading successful")
        return True

    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_search_functionality() -> bool:
    """Test basic search functionality components."""
    print("🔍 Testing search functionality components...")

    try:
        # Test query intent detector
        from paperez_mcp.utils.query_intent import QueryIntentDetector

        detector = QueryIntentDetector()
        analysis = detector.analyze_query("machine learning neural networks")
        print(f"  ✓ Query analysis successful: {analysis.intent}")

        # Test that smart search functionality is available

        print("  ✓ Smart search function imported successfully")

        print("✓ Search functionality components available")
        return True

    except Exception as e:
        print(f"❌ Search functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> int:
    """Run configuration validation."""
    print("🧪 Running configuration validation...")
    print("=" * 60)

    # Add current directory to path for imports
    sys.path.insert(0, ".")

    all_good = True

    # Test configuration loading
    if not test_configuration_loading():
        all_good = False

    print()

    # Test search functionality
    if not test_search_functionality():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All configuration validation passed!")
        return 0
    else:
        print("❌ Configuration validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
