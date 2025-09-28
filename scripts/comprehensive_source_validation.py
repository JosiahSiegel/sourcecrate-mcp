#!/usr/bin/env python3
"""
Comprehensive source validation that actually tests each source individually
and validates the quality of returned data based on queries.
"""

import asyncio
import logging
import sys
import time
from typing import Any, Dict, List, Optional

# Setup logging to capture detailed information
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SourceValidator:
    """Comprehensive validator for academic sources"""

    def __init__(self):
        self.test_queries = {
            # Query -> Expected characteristics
            "machine learning": {
                "keywords": [
                    "machine",
                    "learning",
                    "neural",
                    "algorithm",
                    "AI",
                    "artificial",
                ],
                "min_results": 1,
                "relevant_sources": ["arxiv", "semantic_scholar", "crossref"],
                "domains": ["computer science", "artificial intelligence"],
            },
            "diabetes treatment": {
                "keywords": ["diabetes", "treatment", "insulin", "glucose", "therapy"],
                "min_results": 1,
                "relevant_sources": [
                    "pubmed",
                    "pubmed_central",
                    "europe_pmc",
                    "clinicaltrials",
                ],
                "domains": ["medicine", "health", "biomedical"],
            },
            "climate change": {
                "keywords": ["climate", "change", "warming", "environmental", "carbon"],
                "min_results": 1,
                "relevant_sources": ["crossref", "semantic_scholar", "core_repository"],
                "domains": ["environmental science", "climatology"],
            },
            "economic growth": {
                "keywords": ["economic", "growth", "GDP", "development", "economy"],
                "min_results": 1,
                "relevant_sources": ["repec", "crossref", "semantic_scholar"],
                "domains": ["economics", "finance"],
            },
        }

        self.source_requirements = {
            # Required fields that each source should return
            "common_fields": ["title", "source"],
            "optional_fields": ["authors", "year", "abstract", "url", "doi"],
            "pdf_fields": ["pdf_url", "open_access_pdf"],
        }

        self.validation_results = {}

    async def validate_all_sources(self) -> Dict[str, Any]:
        """Run comprehensive validation on all configured sources"""
        print("🧪 Starting Comprehensive Source Validation...")
        print("=" * 80)

        # Get all configured sources
        sources = await self._get_configured_sources()
        print(f"📋 Found {len(sources)} configured sources: {list(sources.keys())}")

        # Test each source individually
        source_results = {}
        for source_name, search_func in sources.items():
            print(f"\n🔍 Testing source: {source_name}")
            source_results[source_name] = await self._test_source_comprehensively(
                source_name, search_func
            )

        # Test query relevance across all sources
        print(f"\n🎯 Testing Query Relevance Across All Sources")
        relevance_results = await self._test_query_relevance()

        # Test fallback behavior
        print(f"\n🔄 Testing Fallback Behavior")
        fallback_results = await self._test_fallback_behavior()

        # Compile comprehensive report
        return {
            "timestamp": time.time(),
            "total_sources": len(sources),
            "source_results": source_results,
            "relevance_results": relevance_results,
            "fallback_results": fallback_results,
            "overall_health": self._calculate_overall_health(source_results),
            "recommendations": self._generate_recommendations(source_results),
        }

    async def _get_configured_sources(self) -> Dict[str, Any]:
        """Get all configured sources and their search functions"""
        try:
            sys.path.insert(0, ".")
            from paperez_mcp.config import get_search_service

            search_service = get_search_service()
            return search_service.get_search_functions()
        except Exception as e:
            logger.error(f"Failed to get configured sources: {e}")
            return {}

    async def _test_source_comprehensively(
        self, source_name: str, search_func: Any
    ) -> Dict[str, Any]:
        """Test a single source with multiple queries and validation criteria"""
        results = {
            "source_name": source_name,
            "is_functional": False,
            "response_times": [],
            "query_results": {},
            "data_quality": {},
            "errors": [],
            "warnings": [],
        }

        # Test each query type
        for query, expectations in self.test_queries.items():
            print(f"  📝 Testing query: '{query}'")

            try:
                start_time = time.time()

                # Execute search with appropriate limit
                if source_name in ["pubmed", "pubmed_central"]:
                    from paperez_mcp.api_clients.pubmed_client import (
                        search_pubmed,
                        search_pubmed_central,
                    )

                    if source_name == "pubmed":
                        query_results = await search_pubmed(query, 5)
                    else:
                        query_results = await search_pubmed_central(query, 5)
                elif source_name == "arxiv":
                    from paperez_mcp.api_clients.arxiv_client import search_arxiv

                    query_results = await search_arxiv(query, 5)
                elif hasattr(search_func, "__call__"):
                    query_results = await search_func(query, 5)
                else:
                    results["errors"].append(
                        f"Search function not callable for {source_name}"
                    )
                    continue

                response_time = time.time() - start_time
                results["response_times"].append(response_time)

                # Validate results
                query_validation = self._validate_query_results(
                    query, query_results, expectations, source_name
                )
                results["query_results"][query] = query_validation

                # Check if this source should be relevant for this query
                if source_name in expectations["relevant_sources"]:
                    if not query_results or len(query_results) == 0:
                        results["warnings"].append(
                            f"Expected results for '{query}' but got none"
                        )
                    else:
                        results["is_functional"] = True
                        print(
                            f"    ✅ Found {len(query_results)} results ({response_time:.2f}s)"
                        )
                else:
                    if query_results and len(query_results) > 0:
                        print(
                            f"    ℹ️ Unexpected results: {len(query_results)} results ({response_time:.2f}s)"
                        )
                    else:
                        print(f"    ⚪ No results as expected ({response_time:.2f}s)")

            except Exception as e:
                results["errors"].append(f"Query '{query}' failed: {str(e)}")
                print(f"    ❌ Query failed: {e}")

        # Calculate data quality metrics
        results["data_quality"] = self._calculate_data_quality(results["query_results"])

        return results

    def _validate_query_results(
        self, query: str, results: List[Dict], expectations: Dict, source_name: str
    ) -> Dict[str, Any]:
        """Validate the quality and relevance of query results"""
        validation = {
            "result_count": len(results) if results else 0,
            "has_required_fields": False,
            "relevance_score": 0.0,
            "data_completeness": 0.0,
            "pdf_availability": 0.0,
            "issues": [],
        }

        if not results or len(results) == 0:
            validation["issues"].append("No results returned")
            return validation

        # Check data structure and required fields
        valid_results = 0
        total_fields = 0
        pdf_count = 0
        relevance_scores = []

        for result in results:
            if not isinstance(result, dict):
                validation["issues"].append("Result is not a dictionary")
                continue

            # Check required fields
            has_required = all(
                field in result for field in self.source_requirements["common_fields"]
            )
            if has_required:
                valid_results += 1

            # Count available fields
            available_fields = sum(
                1
                for field in self.source_requirements["optional_fields"]
                if result.get(field)
            )
            total_fields += available_fields

            # Check PDF availability
            if result.get("pdf_url") or result.get("open_access_pdf"):
                pdf_count += 1

            # Check relevance to query
            relevance = self._calculate_relevance_score(query, result, expectations)
            relevance_scores.append(relevance)

        # Calculate metrics
        validation["has_required_fields"] = valid_results > 0
        validation["data_completeness"] = total_fields / (
            len(results) * len(self.source_requirements["optional_fields"])
        )
        validation["pdf_availability"] = pdf_count / len(results)
        validation["relevance_score"] = (
            sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        )

        return validation

    def _calculate_relevance_score(
        self, query: str, result: Dict, expectations: Dict
    ) -> float:
        """Calculate how relevant a result is to the original query"""
        score = 0.0
        query_words = set(query.lower().split())
        expected_keywords = set(word.lower() for word in expectations["keywords"])

        # Check title relevance
        title = result.get("title", "").lower()
        title_words = set(title.split())

        # Query word matches in title
        query_matches = (
            len(query_words.intersection(title_words)) / len(query_words)
            if query_words
            else 0
        )
        score += query_matches * 0.5

        # Expected keyword matches in title
        keyword_matches = (
            len(expected_keywords.intersection(title_words)) / len(expected_keywords)
            if expected_keywords
            else 0
        )
        score += keyword_matches * 0.3

        # Check abstract relevance if available
        abstract = result.get("abstract", "").lower()
        if abstract:
            abstract_words = set(abstract.split())
            abstract_query_matches = (
                len(query_words.intersection(abstract_words)) / len(query_words)
                if query_words
                else 0
            )
            score += abstract_query_matches * 0.2

        return min(score, 1.0)  # Cap at 1.0

    async def _test_query_relevance(self) -> Dict[str, Any]:
        """Test that query routing and relevance works correctly across sources"""
        relevance_results = {}

        try:
            from paperez_mcp.utils.smart_search import smart_downloadable_search

            for query, expectations in self.test_queries.items():
                print(f"  🎯 Testing relevance for: '{query}'")

                try:
                    results, search_log = await smart_downloadable_search(
                        query, limit=10
                    )

                    # Analyze if the right sources were prioritized
                    sources_used = search_log.get("sources_searched", [])
                    expected_sources = expectations["relevant_sources"]

                    relevance_analysis = {
                        "query": query,
                        "results_found": len(results),
                        "sources_used": sources_used,
                        "expected_sources": expected_sources,
                        "source_match_score": len(
                            set(sources_used).intersection(set(expected_sources))
                        )
                        / len(expected_sources),
                        "routing_correct": any(
                            source in sources_used for source in expected_sources
                        ),
                        "search_log": search_log,
                    }

                    relevance_results[query] = relevance_analysis

                    if relevance_analysis["routing_correct"]:
                        print(
                            f"    ✅ Correct routing: used {len(set(sources_used).intersection(set(expected_sources)))} expected sources"
                        )
                    else:
                        print(
                            f"    ❌ Poor routing: expected {expected_sources}, used {sources_used}"
                        )

                except Exception as e:
                    print(f"    ❌ Relevance test failed: {e}")
                    relevance_results[query] = {"error": str(e)}

        except Exception as e:
            logger.error(f"Failed to import smart_search: {e}")
            return {"error": "Smart search not available"}

        return relevance_results

    async def _test_fallback_behavior(self) -> Dict[str, Any]:
        """Test that fallback behavior works when primary sources fail"""
        fallback_results = {
            "cascade_testing": {},
            "limit_testing": {},
            "error_handling": {},
        }

        # Test cascading through sources until limit is reached
        print("  🔄 Testing source cascading...")
        try:
            from paperez_mcp.utils.smart_search import smart_downloadable_search

            # Test with different limits to see cascading behavior
            for limit in [1, 5, 20]:
                results, search_log = await smart_downloadable_search(
                    "machine learning", limit=limit
                )

                fallback_results["limit_testing"][f"limit_{limit}"] = {
                    "results_found": len(results),
                    "sources_used": search_log.get("sources_searched", []),
                    "expected_cascading": limit
                    > 5,  # Should use multiple sources for higher limits
                    "cascading_occurred": len(search_log.get("sources_searched", []))
                    > 1,
                }

                print(
                    f"    Limit {limit}: {len(results)} results from {len(search_log.get('sources_searched', []))} sources"
                )

        except Exception as e:
            fallback_results["error"] = str(e)
            print(f"    ❌ Fallback testing failed: {e}")

        return fallback_results

    def _calculate_data_quality(self, query_results: Dict) -> Dict[str, float]:
        """Calculate overall data quality metrics for a source"""
        if not query_results:
            return {"overall_score": 0.0}

        scores = []
        for query_result in query_results.values():
            if not isinstance(query_result, dict):
                continue

            # Weight different aspects of quality
            relevance = query_result.get("relevance_score", 0.0) * 0.4
            completeness = query_result.get("data_completeness", 0.0) * 0.3
            pdf_availability = query_result.get("pdf_availability", 0.0) * 0.2
            has_required = (
                0.1 if query_result.get("has_required_fields", False) else 0.0
            )

            total_score = relevance + completeness + pdf_availability + has_required
            scores.append(total_score)

        return {
            "overall_score": sum(scores) / len(scores) if scores else 0.0,
            "relevance_avg": sum(
                qr.get("relevance_score", 0) for qr in query_results.values()
            )
            / len(query_results),
            "completeness_avg": sum(
                qr.get("data_completeness", 0) for qr in query_results.values()
            )
            / len(query_results),
            "pdf_availability_avg": sum(
                qr.get("pdf_availability", 0) for qr in query_results.values()
            )
            / len(query_results),
        }

    def _calculate_overall_health(self, source_results: Dict) -> Dict[str, Any]:
        """Calculate overall system health based on all source results"""
        total_sources = len(source_results)
        functional_sources = sum(
            1
            for result in source_results.values()
            if result.get("is_functional", False)
        )

        # Calculate average response time
        all_response_times = []
        for result in source_results.values():
            all_response_times.extend(result.get("response_times", []))

        avg_response_time = (
            sum(all_response_times) / len(all_response_times)
            if all_response_times
            else 0
        )

        # Calculate average data quality
        quality_scores = []
        for result in source_results.values():
            data_quality = result.get("data_quality", {})
            if isinstance(data_quality, dict):
                overall_score = data_quality.get("overall_score", 0.0)
                quality_scores.append(overall_score)

        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        )

        # Determine overall health status
        functional_ratio = (
            functional_sources / total_sources if total_sources > 0 else 0
        )
        if functional_ratio >= 0.8 and avg_quality >= 0.7:
            status = "healthy"
        elif functional_ratio >= 0.5 and avg_quality >= 0.5:
            status = "degraded"
        else:
            status = "critical"

        return {
            "status": status,
            "functional_sources": functional_sources,
            "total_sources": total_sources,
            "functional_ratio": functional_ratio,
            "average_response_time": avg_response_time,
            "average_quality_score": avg_quality,
        }

    def _generate_recommendations(self, source_results: Dict) -> List[Dict[str, str]]:
        """Generate specific recommendations based on test results"""
        recommendations = []

        for source_name, result in source_results.items():
            if not result.get("is_functional", False):
                # Check specific error types
                errors = result.get("errors", [])
                if any("404" in error for error in errors):
                    recommendations.append(
                        {
                            "source": source_name,
                            "severity": "high",
                            "issue": "API endpoint not found (404)",
                            "recommendation": "Update API endpoint URL or remove source",
                        }
                    )
                elif any("401" in error or "403" in error for error in errors):
                    recommendations.append(
                        {
                            "source": source_name,
                            "severity": "high",
                            "issue": "Authentication/authorization failure",
                            "recommendation": "Check API credentials and permissions",
                        }
                    )
                elif any("429" in error for error in errors):
                    recommendations.append(
                        {
                            "source": source_name,
                            "severity": "medium",
                            "issue": "Rate limiting",
                            "recommendation": "Implement backoff strategy or get API key",
                        }
                    )

            # Check data quality issues
            data_quality = result.get("data_quality", {})
            if isinstance(data_quality, dict):
                if data_quality.get("relevance_avg", 0) < 0.3:
                    recommendations.append(
                        {
                            "source": source_name,
                            "severity": "medium",
                            "issue": "Low query relevance",
                            "recommendation": "Review query optimization for this source",
                        }
                    )

                if data_quality.get("pdf_availability_avg", 0) < 0.1:
                    recommendations.append(
                        {
                            "source": source_name,
                            "severity": "low",
                            "issue": "Low PDF availability",
                            "recommendation": "Consider alternative sources for downloadable content",
                        }
                    )

        return recommendations

    def print_comprehensive_report(self, results: Dict[str, Any]) -> None:
        """Print a detailed validation report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE SOURCE VALIDATION REPORT")
        print("=" * 80)

        overall_health = results["overall_health"]
        print(f"\n🏥 Overall System Health: {overall_health['status'].upper()}")
        print(
            f"   Functional Sources: {overall_health['functional_sources']}/{overall_health['total_sources']} ({overall_health['functional_ratio']:.1%})"
        )
        print(
            f"   Average Response Time: {overall_health['average_response_time']:.2f}s"
        )
        print(
            f"   Average Quality Score: {overall_health['average_quality_score']:.2f}/1.0"
        )

        # Source-by-source breakdown
        print(f"\n📋 Individual Source Results:")
        for source_name, result in results["source_results"].items():
            status = "✅ FUNCTIONAL" if result["is_functional"] else "❌ NON-FUNCTIONAL"
            print(f"   {source_name}: {status}")

            if result.get("errors"):
                for error in result["errors"][:2]:  # Show first 2 errors
                    print(f"      ⚠️ {error}")

            data_quality = result.get("data_quality", {})
            if isinstance(data_quality, dict) and data_quality.get("overall_score"):
                print(
                    f"      📊 Quality Score: {data_quality['overall_score']:.2f}/1.0"
                )

        # Query relevance results
        relevance_results = results.get("relevance_results", {})
        if relevance_results and not relevance_results.get("error"):
            print(f"\n🎯 Query Relevance Analysis:")
            for query, analysis in relevance_results.items():
                if isinstance(analysis, dict) and not analysis.get("error"):
                    routing_status = (
                        "✅ CORRECT" if analysis["routing_correct"] else "❌ POOR"
                    )
                    print(f"   '{query}': {routing_status} routing")
                    print(f"      Sources used: {analysis['sources_used']}")
                    print(f"      Expected: {analysis['expected_sources']}")

        # Recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    rec["severity"], "ℹ️"
                )
                print(f"   {severity_icon} {rec['source']}: {rec['issue']}")
                print(f"      → {rec['recommendation']}")

        print("\n" + "=" * 80)


async def main():
    """Run comprehensive source validation"""
    validator = SourceValidator()
    results = await validator.validate_all_sources()
    validator.print_comprehensive_report(results)

    # Return appropriate exit code
    overall_health = results["overall_health"]["status"]
    if overall_health == "healthy":
        print("🎉 All sources validation PASSED!")
        return 0
    elif overall_health == "degraded":
        print("⚠️ Sources validation PASSED with warnings")
        return 0  # Still pass but with warnings
    else:
        print("❌ Sources validation FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
