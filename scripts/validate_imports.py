#!/usr/bin/env python3
"""
Shared import validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import sys


def test_core_imports():
    """Test all core module imports."""
    print("🔍 Testing core module imports...")

    try:
        # Add current directory to path for imports
        sys.path.insert(0, ".")

        # Test server imports
        from source_crate.server import (
            browse_papers,
            download_papers,
            get_help,
            get_status,
        )

        print("  ✓ Server tools imported successfully")

        # Test service imports
        from source_crate.services.search_service import SearchOrchestrationService

        print("  ✓ Search service imported successfully")

        # Test utility imports
        from source_crate.utils.pdf_processor import extract_pdf_text_from_local_file
        from source_crate.utils.query_intent import QueryIntentDetector
        from source_crate.utils.smart_search import smart_downloadable_search

        print("  ✓ Utility modules imported successfully")

        # Test config imports
        from source_crate.config.manager import ConfigManager

        print("  ✓ Configuration manager imported successfully")

        print("✓ All core imports successful")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False


def test_mcp_server_structure():
    """Test that MCP server structure is correct."""
    print("🔍 Testing MCP server structure...")

    try:
        # Import the MCP server object
        from source_crate.server import mcp

        # Check that MCP server is properly initialized
        assert hasattr(mcp, "tool"), "MCP server should have tool decorator"
        assert hasattr(mcp, "run"), "MCP server should have run method"
        print("  ✓ MCP server object properly structured")

        # Check that tool functions exist in the server module
        from source_crate import server

        tool_functions = [
            "browse_papers",
            "download_papers",
            "get_status",
            "get_help",
            "convert_pdf_to_text",
            "convert_pdf_to_markdown",
            "batch_convert_pdfs",
        ]

        for func_name in tool_functions:
            assert hasattr(
                server, func_name
            ), f"Server should have {func_name} function"
            # Don't check callable since MCP tools are wrapped
            print(f"  ✓ {func_name} function available")

        print("✓ All MCP server structure validated")
        return True

    except Exception as e:
        print(f"❌ MCP server structure error: {e}")
        return False


def test_configuration_loading():
    """Test configuration system."""
    print("🔍 Testing configuration loading...")

    try:
        from source_crate.config.manager import ConfigManager

        config = ConfigManager().get_config()
        assert len(config.sources) > 0, "No sources loaded from configuration"
        assert len(config.categories) > 0, "No categories loaded from configuration"

        print(
            f"  ✓ Loaded {len(config.sources)} sources and {len(config.categories)} categories"
        )
        print("✓ Configuration loading successful")
        return True

    except Exception as e:
        print(f"❌ Configuration loading error: {e}")
        return False


def main():
    """Run import and structure validation."""
    print("🧪 Running comprehensive import and structure validation...")
    print("=" * 60)

    all_good = True

    # Test core imports
    if not test_core_imports():
        all_good = False

    print()

    # Test configuration loading
    if not test_configuration_loading():
        all_good = False

    print()

    # Test MCP server structure
    if not test_mcp_server_structure():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All imports and structure validated successfully!")
        return 0
    else:
        print("❌ Import/structure validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
