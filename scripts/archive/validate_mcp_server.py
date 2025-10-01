#!/usr/bin/env python3
"""
Shared MCP server validation script for both precommit and CI workflow.
This ensures identical validation across environments.
"""

import asyncio
import logging
import sys
from io import StringIO


def setup_log_capture():
    """Set up log capture to detect real errors"""
    log_capture = StringIO()
    log_handler = logging.StreamHandler(log_capture)
    log_handler.setLevel(logging.WARNING)  # Capture warnings and errors

    # Add to relevant loggers
    loggers_to_monitor = [
        "paperez_mcp.api_clients.pubmed_client",
        "paperez_mcp.utils.smart_search",
        "paperez_mcp.config.manager",
    ]

    for logger_name in loggers_to_monitor:
        logger = logging.getLogger(logger_name)
        logger.addHandler(log_handler)

    return log_capture, log_handler, loggers_to_monitor


def analyze_captured_logs(log_capture, operation_name):
    """Analyze captured logs for real errors that should fail validation"""
    log_content = log_capture.getvalue()

    # Patterns that indicate real errors (not just informational warnings)
    error_patterns = [
        "'PubMedBookArticle' object has no attribute 'journal'",
        "'str' object has no attribute 'year'",
        "Unknown category",
        "AttributeError:",
        "KeyError:",
        "TypeError:",
        "ImportError:",
    ]

    # Patterns that are warnings but not commit-blocking errors
    warning_patterns = [
        "All proxy methods failed",  # External dependency, not code bug
    ]

    # Find real errors and warnings
    real_errors = []
    warnings = []

    for line in log_content.split("\n"):
        for pattern in error_patterns:
            if pattern in line:
                real_errors.append(line.strip())
                break
        else:  # No error pattern matched, check for warnings
            for pattern in warning_patterns:
                if pattern in line:
                    warnings.append(line.strip())
                    break

    return real_errors, warnings


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
    """Test basic MCP tool functionality with rigorous error detection."""
    print("🔍 Testing MCP tools functionality...")

    # Set up log capture to detect hidden errors
    log_capture, log_handler, monitored_loggers = setup_log_capture()

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

        # Test browse_papers with rigorous functional testing
        print("  📚 Testing browse_papers...")

        # Test with basic query - must actually work
        result = await server.browse_papers.fn("machine learning", limit=2)
        if not isinstance(result, list):
            print("  ❌ browse_papers should return a list")
            return False

        # Check for actual errors in result
        if len(result) > 0:
            # Verify result structure
            first_result = result[0]
            if not isinstance(first_result, dict):
                print("  ❌ browse_papers results should be dictionaries")
                return False

            required_fields = ["results", "total_found", "sources_used"]
            for field in required_fields:
                if field not in first_result:
                    print(f"  ❌ browse_papers missing required field: {field}")
                    return False

            # Check for API errors hidden in results - but allow empty results for bad queries
            result_str = str(first_result).lower()
            if "error" in result_str and "no papers found" not in result_str:
                print(f"  ❌ browse_papers contains hidden errors: {first_result}")
                return False

        print(f"  ✓ browse_papers basic query returned {len(result)} results")

        # Test with empty query - should handle gracefully but not hide errors
        try:
            result = await server.browse_papers.fn("", limit=1)
            if not isinstance(result, list):
                print("  ❌ browse_papers empty query should return a list")
                return False
            print(
                f"  ✓ browse_papers empty query handled correctly ({len(result)} results)"
            )
        except Exception as e:
            if "PubMedBookArticle" in str(e) or "journal" in str(e):
                print(f"  ❌ browse_papers has real API error: {e}")
                return False
            # Other exceptions might be acceptable for empty queries
            print(
                f"  ✓ browse_papers empty query handled with controlled error: {type(e).__name__}"
            )

        # Test with special characters - should not crash
        try:
            result = await server.browse_papers.fn("test & special <chars>", limit=1)
            if not isinstance(result, list):
                print("  ❌ browse_papers special chars should return a list")
                return False
            print(
                f"  ✓ browse_papers special chars handled correctly ({len(result)} results)"
            )
        except Exception as e:
            if "PubMedBookArticle" in str(e) or "journal" in str(e):
                print(f"  ❌ browse_papers has real API error with special chars: {e}")
                return False
            # Other exceptions might be acceptable for special characters
            print(
                f"  ✓ browse_papers special chars handled with controlled error: {type(e).__name__}"
            )

        # Analyze captured logs for real errors and warnings
        real_errors, warnings = analyze_captured_logs(
            log_capture, "MCP tools functionality"
        )

        if warnings:
            print("  ⚠️ Warnings detected (non-blocking):")
            for warning in warnings:
                print(f"    - {warning}")

        if real_errors:
            print("  ❌ Real errors detected in logs during testing:")
            for error in real_errors:
                print(f"    - {error}")
            return False

        print("✓ MCP tools functionality tests passed")
        return True

    except Exception as e:
        print(f"❌ MCP tools functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # Clean up log handlers
        for logger_name in monitored_loggers:
            logger = logging.getLogger(logger_name)
            logger.removeHandler(log_handler)


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
