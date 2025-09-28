#!/usr/bin/env python3
"""
Shared MCP server validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import asyncio
import sys


async def test_mcp_server_startup():
    """Test MCP server startup and tool registration."""
    print("🔍 Testing MCP server startup...")

    try:
        # Import and test basic MCP server setup
        from paperez_mcp.server import mcp

        print("  ✓ MCP server module loaded successfully")

        # Test that tools are properly registered
        tools = await mcp.get_tools()
        expected_tools = [
            "browse_papers",
            "download_papers",
            "convert_pdf_to_text",
            "convert_pdf_to_markdown",
            "batch_convert_pdfs",
            "get_status",
            "get_help",
        ]

        tool_names = list(tools.keys())
        for expected in expected_tools:
            if expected not in tool_names:
                print(f"  ❌ Missing tool: {expected}")
                return False
            print(f"  ✓ {expected} tool registered")

        print(f"✓ All {len(expected_tools)} MCP tools registered correctly")
        return True

    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_mcp_tools_functionality():
    """Test basic MCP tool functionality."""
    print("🔍 Testing MCP tools functionality...")

    try:
        from paperez_mcp import server

        # Test get_status (should work offline)
        print("  📊 Testing get_status...")
        status = await server.get_status.fn()
        if "api_status" not in status:
            print("  ❌ get_status missing api_status")
            return False
        if "config" not in status:
            print("  ❌ get_status missing config")
            return False
        if "cache_stats" not in status:
            print("  ❌ get_status missing cache_stats")
            return False
        print("  ✓ get_status returned all required fields")

        # Test get_help (should always work)
        print("  📖 Testing get_help...")
        help_info = await server.get_help.fn()
        if "config_guide" not in help_info:
            print("  ❌ get_help missing config_guide")
            return False
        if "file_paths" not in help_info:
            print("  ❌ get_help missing file_paths")
            return False
        if "examples" not in help_info:
            print("  ❌ get_help missing examples")
            return False
        print("  ✓ get_help returned all required fields")

        # Test browse_papers with basic queries
        print("  📚 Testing browse_papers...")

        # Test with basic query
        result = await server.browse_papers.fn("test query", limit=2)
        if not isinstance(result, list):
            print("  ❌ browse_papers should return a list")
            return False
        print(f"  ✓ browse_papers basic query returned {len(result)} results")

        # Test with empty query (should handle gracefully)
        result = await server.browse_papers.fn("", limit=1)
        if not isinstance(result, list):
            print("  ❌ browse_papers empty query should return a list")
            return False
        print(
            f"  ✓ browse_papers empty query handled correctly ({len(result)} results)"
        )

        # Test with special characters (should handle gracefully)
        result = await server.browse_papers.fn("test & special <chars>", limit=1)
        if not isinstance(result, list):
            print("  ❌ browse_papers special chars should return a list")
            return False
        print(
            f"  ✓ browse_papers special chars handled correctly ({len(result)} results)"
        )

        print("✓ MCP tools functionality tests passed")
        return True

    except Exception as e:
        print(f"❌ MCP tools functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run MCP server validation."""
    print("🧪 Running MCP server validation...")
    print("=" * 60)

    # Add current directory to path for imports
    sys.path.insert(0, ".")

    all_good = True

    # Test MCP server startup
    if not await test_mcp_server_startup():
        all_good = False

    print()

    # Test MCP tools functionality
    if not await test_mcp_tools_functionality():
        all_good = False

    print()
    print("=" * 60)

    if all_good:
        print("🎉 All MCP server validation passed!")
        return 0
    else:
        print("❌ MCP server validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
