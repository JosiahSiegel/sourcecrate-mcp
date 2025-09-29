#!/usr/bin/env python3
"""
Diagnostic tool for PaperezMCP connectivity testing
"""
import asyncio
import sys
import time
from typing import Any, Dict

async def test_api_connectivity() -> Dict[str, Any]:
    """Test actual API connectivity to academic databases"""

    print("🔍 PaperezMCP Connectivity Diagnostic Tool")
    print("=" * 50)

    # Test configuration loading
    try:
        from paperez_mcp.config import get_current_config, get_search_service
        from paperez_mcp.server import get_api_status

        print("📋 Testing Configuration Loading...")
        config = get_current_config()
        print(f"   ✅ Config loaded: {len(getattr(config, 'sources', {}))} sources")

        search_service = get_search_service()
        search_funcs = search_service.get_search_functions()
        print(f"   ✅ Search functions: {len(search_funcs)} registered")

        api_status = get_api_status()
        enabled_count = sum(1 for enabled in api_status.values() if enabled)
        print(f"   ✅ API status: {enabled_count}/{len(api_status)} sources enabled")

        if enabled_count == 0:
            print("   ❌ CRITICAL: No sources enabled!")
            return {"status": "critical", "issue": "no_sources_enabled"}

    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return {"status": "error", "issue": "config_loading", "error": str(e)}

    # Test actual search functionality
    print("\n🔎 Testing Search Functionality...")
    try:
        # Import the wrapped functions directly
        from paperez_mcp import server

        # Test with a simple query
        test_query = "machine learning"
        print(f"   🔍 Testing query: '{test_query}'")

        # We can't call the MCP tools directly, but we can test the underlying functions
        utils = server._lazy_import_utils()
        search_funcs = server._lazy_import_search_functions()

        if not search_funcs:
            print("   ❌ No search functions available")
            return {"status": "error", "issue": "no_search_functions"}

        print(f"   ✅ Search functions available: {list(search_funcs.keys())}")

        # Test smart search functionality
        results, search_log = await utils["smart_downloadable_search"](
            test_query, 2, search_funcs, utils, api_status.copy(), None, True
        )

        if results:
            print(f"   ✅ Search succeeded: {len(results)} results found")
            sources_used = list(set(r.get('source', 'Unknown') for r in results))
            print(f"   ✅ Sources used: {sources_used}")
            return {
                "status": "healthy",
                "results_found": len(results),
                "sources_used": sources_used,
                "test_query": test_query
            }
        else:
            print("   ⚠️  Search returned no results")
            print(f"   📊 Search log: {search_log}")
            return {
                "status": "warning",
                "issue": "no_results",
                "search_log": search_log
            }

    except Exception as e:
        print(f"   ❌ Search test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "issue": "search_failure", "error": str(e)}

async def main():
    """Run connectivity diagnostic"""
    start_time = time.time()
    result = await test_api_connectivity()
    duration = time.time() - start_time

    print(f"\n📊 Diagnostic Complete ({duration:.2f}s)")
    print(f"Status: {result['status'].upper()}")

    if result['status'] == 'healthy':
        print("✅ PaperezMCP is functioning correctly")
    elif result['status'] == 'warning':
        print("⚠️  PaperezMCP has connectivity issues")
    else:
        print("❌ PaperezMCP has critical issues")

    print(f"\nResult details: {result}")

if __name__ == "__main__":
    asyncio.run(main())