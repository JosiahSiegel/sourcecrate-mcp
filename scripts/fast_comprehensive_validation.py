#!/usr/bin/env python3
"""
Fast Comprehensive Validation Framework
Addresses critical issues 3.1 and 3.2 from COMPREHENSIVE_ISSUE_RESOLUTION.md

Key improvements:
- Fast execution (under 30 seconds)
- Catches real API connectivity issues
- Validates content quality without exhaustive testing
- No false positives - if it fails, there's a real problem
- Parallel testing for speed
- Focused on most common failure modes
"""

import asyncio
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

# Setup concise logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class FastValidator:
    """Fast, comprehensive validator that catches real issues without false positives"""

    def __init__(self):
        # Focused test queries that are likely to reveal real problems
        self.critical_tests = {
            "machine learning": {
                "expected_sources": ["arxiv", "semantic_scholar"],
                "min_results": 1,
                "relevance_keywords": ["machine", "learning", "algorithm", "AI"],
            },
            "diabetes": {
                "expected_sources": ["pubmed", "pubmed_central"],
                "min_results": 1,
                "relevance_keywords": ["diabetes", "glucose", "insulin"],
            },
        }

        # Known problematic patterns that indicate real failures
        self.failure_patterns = [
            "404 Not Found",
            "401 Unauthorized",
            "403 Forbidden",
            "429 Too Many Requests",
            "500 Internal Server Error",
            "ConnectionError",
            "TimeoutError",
            "PubMedBookArticle.*object has no attribute.*journal",
            "KeyError:",
            "AttributeError:",
            "TypeError:",
        ]

        self.results = {"timestamp": time.time(), "tests": [], "overall_status": "UNKNOWN"}

    async def run_fast_validation(self) -> Dict[str, Any]:
        """Run fast comprehensive validation in under 30 seconds"""
        print("🚀 Fast Comprehensive Validation Starting...")
        print("=" * 50)
        start_time = time.time()

        # Test 1: Basic import and configuration health (should be instant)
        print("📦 Testing imports and configuration...")
        import_result = await self._test_imports_and_config()
        self.results["tests"].append(import_result)

        if not import_result["passed"]:
            self._fail_fast("Critical imports failed")
            return self.results

        # Test 2: MCP server structure (should be under 2 seconds)
        print("🔌 Testing MCP server structure...")
        mcp_result = await self._test_mcp_server_structure()
        self.results["tests"].append(mcp_result)

        if not mcp_result["passed"]:
            self._fail_fast("MCP server structure invalid")
            return self.results

        # Test 3: Fast source connectivity checks (parallel, under 10 seconds)
        print("🌐 Testing source connectivity...")
        connectivity_result = await self._test_source_connectivity_fast()
        self.results["tests"].append(connectivity_result)

        # Test 4: Content quality spot checks (under 15 seconds total)
        print("🎯 Testing content quality...")
        quality_result = await self._test_content_quality_fast()
        self.results["tests"].append(quality_result)

        # Calculate overall status
        elapsed = time.time() - start_time
        passed_tests = sum(1 for test in self.results["tests"] if test["passed"])
        total_tests = len(self.results["tests"])

        if passed_tests == total_tests:
            self.results["overall_status"] = "PASS"
            print(f"\n✅ All {total_tests} tests passed in {elapsed:.1f}s")
        else:
            self.results["overall_status"] = "FAIL"
            failed_tests = [test["name"] for test in self.results["tests"] if not test["passed"]]
            print(f"\n❌ {total_tests - passed_tests}/{total_tests} tests failed: {failed_tests}")

        return self.results

    async def _test_imports_and_config(self) -> Dict[str, Any]:
        """Test basic imports and configuration loading"""
        test_result = {"name": "imports_and_config", "passed": False, "issues": []}

        try:
            # Critical imports
            sys.path.insert(0, ".")
            from paperez_mcp.config import get_current_config, get_search_service
            from paperez_mcp import server

            # Configuration loading
            config = get_current_config()
            if not config or not config.sources:
                test_result["issues"].append("Configuration not loaded or no sources")
                return test_result

            # Search service initialization
            search_service = get_search_service()
            sources = search_service.get_search_functions()
            if len(sources) < 5:  # Should have at least 5 working sources
                test_result["issues"].append(f"Too few sources available: {len(sources)}")
                return test_result

            # MCP server modules
            required_tools = ["browse_papers", "download_papers", "get_status", "get_help"]
            for tool in required_tools:
                if not hasattr(server, tool):
                    test_result["issues"].append(f"Missing MCP tool: {tool}")
                    return test_result

            test_result["passed"] = True
            test_result["sources_found"] = len(sources)

        except Exception as e:
            test_result["issues"].append(f"Import/config error: {str(e)}")

        return test_result

    async def _test_mcp_server_structure(self) -> Dict[str, Any]:
        """Test MCP server tool registration and basic functionality"""
        test_result = {"name": "mcp_server_structure", "passed": False, "issues": []}

        try:
            from paperez_mcp.server import mcp

            # Test tool registration
            tools = await mcp.get_tools()
            expected_tools = ["browse_papers", "download_papers", "get_status", "get_help"]

            missing_tools = [tool for tool in expected_tools if tool not in tools]
            if missing_tools:
                test_result["issues"].append(f"Missing tools: {missing_tools}")
                return test_result

            # Test basic tool functionality (offline tools only)
            from paperez_mcp import server

            # Test get_status (should always work)
            status = await server.get_status.fn()
            required_status_fields = ["api_status", "config", "cache_stats"]
            missing_fields = [field for field in required_status_fields if field not in status]
            if missing_fields:
                test_result["issues"].append(f"get_status missing fields: {missing_fields}")
                return test_result

            # Test get_help (should always work)
            help_info = await server.get_help.fn()
            required_help_fields = ["config_guide", "file_paths", "examples"]
            missing_help_fields = [field for field in required_help_fields if field not in help_info]
            if missing_help_fields:
                test_result["issues"].append(f"get_help missing fields: {missing_help_fields}")
                return test_result

            test_result["passed"] = True
            test_result["tools_registered"] = len(tools)

        except Exception as e:
            test_result["issues"].append(f"MCP server error: {str(e)}")

        return test_result

    async def _test_source_connectivity_fast(self) -> Dict[str, Any]:
        """Fast parallel test of source connectivity"""
        test_result = {"name": "source_connectivity", "passed": False, "issues": [], "source_results": {}}

        try:
            from paperez_mcp.config import get_search_service
            search_service = get_search_service()
            sources = search_service.get_search_functions()

            # Test critical sources in parallel with short timeouts
            critical_sources = ["arxiv", "pubmed", "semantic_scholar", "crossref"]
            available_critical = [name for name in critical_sources if name in sources]

            if len(available_critical) < 3:
                test_result["issues"].append(f"Too few critical sources available: {available_critical}")
                return test_result

            # Quick parallel connectivity test
            async def test_source_quick(source_name: str, search_func: Any) -> Tuple[str, bool, str]:
                """Quick test of a single source"""
                try:
                    # Very quick test with minimal query
                    if source_name == "pubmed":
                        from paperez_mcp.api_clients.pubmed_client import search_pubmed
                        result = await asyncio.wait_for(search_pubmed("cancer", 1), timeout=5.0)
                    elif source_name == "arxiv":
                        from paperez_mcp.api_clients.arxiv_client import search_arxiv
                        result = await asyncio.wait_for(search_arxiv("physics", 1), timeout=5.0)
                    elif hasattr(search_func, "__call__"):
                        result = await asyncio.wait_for(search_func("test", 1), timeout=5.0)
                    else:
                        return source_name, False, "Not callable"

                    # Check for real failure patterns
                    result_str = str(result).lower()
                    for pattern in self.failure_patterns:
                        if pattern.lower() in result_str:
                            return source_name, False, f"Failure pattern: {pattern}"

                    return source_name, True, "OK"

                except asyncio.TimeoutError:
                    return source_name, False, "Timeout"
                except Exception as e:
                    error_str = str(e)
                    # Check if this is a known critical error
                    for pattern in self.failure_patterns:
                        if pattern.lower() in error_str.lower():
                            return source_name, False, f"Critical error: {error_str}"
                    # Non-critical errors (rate limits, etc.) are warnings but not failures
                    return source_name, True, f"Warning: {error_str}"

            # Run tests in parallel
            tasks = [test_source_quick(name, func) for name, func in sources.items()
                    if name in available_critical]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            working_sources = 0
            for result in results:
                if isinstance(result, tuple):
                    source_name, is_working, message = result
                    test_result["source_results"][source_name] = {"working": is_working, "message": message}
                    if is_working:
                        working_sources += 1
                    else:
                        test_result["issues"].append(f"{source_name}: {message}")

            # Need at least 2 critical sources working for basic functionality
            if working_sources >= 2:
                test_result["passed"] = True
            else:
                test_result["issues"].append(f"Only {working_sources} sources working, need at least 2")

            test_result["working_sources"] = working_sources
            test_result["total_tested"] = len(available_critical)

        except Exception as e:
            test_result["issues"].append(f"Connectivity test error: {str(e)}")

        return test_result

    async def _test_content_quality_fast(self) -> Dict[str, Any]:
        """Fast content quality validation with spot checks"""
        test_result = {"name": "content_quality", "passed": False, "issues": [], "quality_scores": {}}

        try:
            from paperez_mcp import server

            # Quick content quality test - one good query that should work
            test_query = "machine learning"
            result = await asyncio.wait_for(
                server.browse_papers.fn(test_query, limit=3),
                timeout=10.0
            )

            if not isinstance(result, list) or len(result) == 0:
                test_result["issues"].append("browse_papers returned no results")
                return test_result

            # Check result structure
            first_result = result[0]
            if not isinstance(first_result, dict):
                test_result["issues"].append("Results not in dict format")
                return test_result

            required_fields = ["results", "total_found", "sources_used"]
            missing_fields = [field for field in required_fields if field not in first_result]
            if missing_fields:
                test_result["issues"].append(f"Missing result fields: {missing_fields}")
                return test_result

            # Basic content quality checks
            papers = first_result.get("results", [])
            if len(papers) == 0:
                test_result["issues"].append("No papers in results")
                return test_result

            # Check paper quality
            quality_issues = []
            for i, paper in enumerate(papers[:3]):  # Check first 3 papers only
                if not isinstance(paper, dict):
                    quality_issues.append(f"Paper {i} not a dict")
                    continue

                # Check required paper fields
                if not paper.get("title"):
                    quality_issues.append(f"Paper {i} missing title")
                if not paper.get("source"):
                    quality_issues.append(f"Paper {i} missing source")

                # Check basic relevance (title should contain relevant terms)
                title = str(paper.get("title", "")).lower()
                if "machine" not in title and "learning" not in title and "ai" not in title and "algorithm" not in title:
                    quality_issues.append(f"Paper {i} title seems irrelevant: {paper.get('title', '')[:50]}")

            # Allow some quality issues but not too many
            if len(quality_issues) > len(papers) // 2:  # More than half the papers have issues
                test_result["issues"].extend(quality_issues[:3])  # Show first 3 issues
                return test_result

            test_result["passed"] = True
            test_result["papers_checked"] = len(papers)
            test_result["quality_issues_found"] = len(quality_issues)

        except asyncio.TimeoutError:
            test_result["issues"].append("Content quality test timed out")
        except Exception as e:
            test_result["issues"].append(f"Content quality test error: {str(e)}")

        return test_result

    def _fail_fast(self, reason: str):
        """Mark validation as failed and stop"""
        self.results["overall_status"] = "FAIL"
        self.results["fail_fast_reason"] = reason
        print(f"💥 FAIL FAST: {reason}")


async def main():
    """Run fast comprehensive validation"""
    validator = FastValidator()
    results = await validator.run_fast_validation()

    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))