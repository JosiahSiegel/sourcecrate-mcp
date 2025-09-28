"""
Health monitoring service - tracks API status and system health metrics.
Provides comprehensive monitoring and diagnostic capabilities.
"""

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class HealthMonitoringService:
    """
    Monitors system health, API status, and provides diagnostic information.

    Tracks:
    - API response times and success rates
    - Source availability and performance
    - Error patterns and failure analysis
    - Health recommendations and alerts
    """

    def __init__(self, search_funcs: dict[str, Any], api_status: dict[str, bool]):
        """
        Initialize health monitoring service.

        Args:
            search_funcs: Dictionary of search functions
            api_status: API status tracking dictionary
        """
        self.search_funcs = search_funcs
        self.api_status = api_status
        self.health_metrics: dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.HealthMonitoring")

    async def get_comprehensive_status(self) -> dict[str, Any]:
        """
        Get comprehensive system status including API health and cache statistics.

        Returns:
            Dictionary with API status, cache stats, and configuration
        """
        from ..config import cache, config

        # Perform active health checks
        health_check_results = await self._perform_health_checks()

        return {
            "api_status": dict(self.api_status),
            "cache_stats": {
                "size": len(cache._cache) if hasattr(cache, "_cache") else 0,
                "cache_dir": getattr(cache, "cache_dir", "memory"),
                "size_limit": getattr(
                    cache, "size_limit", 1024 * 1024 * 1024
                ),  # 1GB default
            },
            "config": {
                "has_semantic_scholar_key": bool(
                    getattr(config, "semantic_scholar_api_key", None)
                ),
                "has_scraperapi_key": bool(getattr(config, "scraperapi_key", None)),
                "crossref_email": getattr(config, "crossref_email", ""),
                "max_retries": 3,
            },
            "health_checks": health_check_results,
        }

    async def get_source_health_report(self) -> dict[str, Any]:
        """
        Generate comprehensive health monitoring report with recommendations.

        Returns:
            Detailed health report with metrics and recommendations
        """
        # Perform health checks for all sources
        health_results = await self._perform_health_checks()

        # Analyze health metrics
        healthy_count = sum(
            1 for status in health_results.values() if status.get("healthy", False)
        )
        total_sources = len(health_results)

        # Determine overall status
        if healthy_count == total_sources:
            overall_status = "healthy"
        elif healthy_count >= total_sources * 0.7:
            overall_status = "degraded"
        else:
            overall_status = "critical"

        # Generate recommendations
        recommendations = self._generate_health_recommendations(health_results)

        return {
            "health_report": {
                "overall_status": overall_status,
                "sources": health_results,
                "summary": {
                    "healthy": healthy_count,
                    "unhealthy": total_sources - healthy_count,
                    "total": total_sources,
                },
            },
            "recommendations": recommendations,
            "health_check_results": health_results,
            "monitoring_enabled": True,
        }

    async def _perform_health_checks(self) -> dict[str, dict[str, Any]]:
        """
        Perform active health checks on all available sources.

        Returns:
            Dictionary mapping source names to health check results
        """
        health_results: dict[str, dict[str, Any]] = {}

        # Test each available source
        test_query = "test"
        check_tasks = []

        for source_name, search_func in self.search_funcs.items():
            if source_name.startswith("search_"):
                source_key = source_name.replace("search_", "")
                check_tasks.append(
                    self._check_source_health(source_key, search_func, test_query)
                )

        # Execute health checks concurrently
        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Process results
        source_keys = [
            name.replace("search_", "")
            for name in self.search_funcs.keys()
            if name.startswith("search_")
        ]
        for i, result in enumerate(results):
            if i < len(source_keys):
                source_key = source_keys[i]
                if isinstance(result, Exception):
                    health_results[source_key] = {
                        "healthy": False,
                        "error": str(result),
                        "response_time": None,
                        "last_check": time.time(),
                    }
                else:
                    health_results[source_key] = result  # type: ignore[assignment]

        return health_results

    async def _check_source_health(
        self, source_name: str, search_func: Any, test_query: str
    ) -> dict[str, Any]:
        """
        Check health of a specific source.

        Args:
            source_name: Name of the source
            search_func: Search function to test
            test_query: Query to use for testing

        Returns:
            Health check result dictionary
        """
        start_time = time.time()

        try:
            # Perform a minimal test search
            results = await search_func(test_query, 1)
            response_time = time.time() - start_time

            # Determine if source is healthy
            healthy = isinstance(results, list) and response_time < 10.0

            return {
                "healthy": healthy,
                "response_time": response_time,
                "results_returned": len(results) if isinstance(results, list) else 0,
                "last_check": time.time(),
                "status": "operational" if healthy else "slow_response",
            }

        except Exception as e:
            response_time = time.time() - start_time
            return {
                "healthy": False,
                "response_time": response_time,
                "error": str(e),
                "last_check": time.time(),
                "status": "error",
            }

    def _generate_health_recommendations(
        self, health_results: dict[str, dict[str, Any]]
    ) -> list[dict[str, str]]:
        """
        Generate actionable health recommendations based on health check results.

        Args:
            health_results: Results from health checks

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Check for unhealthy sources
        unhealthy_sources = [
            name
            for name, result in health_results.items()
            if not result.get("healthy", False)
        ]

        if unhealthy_sources:
            recommendations.append(
                {
                    "severity": "high",
                    "issue": f"Sources unavailable: {', '.join(unhealthy_sources)}",
                    "recommendation": "Check API keys and network connectivity",
                    "action": "Verify configuration and test individual sources",
                }
            )

        # Check for slow sources
        slow_sources = [
            name
            for name, result in health_results.items()
            if result.get("response_time", 0) > 5.0 and result.get("healthy", False)
        ]

        if slow_sources:
            recommendations.append(
                {
                    "severity": "medium",
                    "issue": f"Slow response times: {', '.join(slow_sources)}",
                    "recommendation": "Monitor performance and consider timeout adjustments",
                    "action": "Review rate limiting and server load",
                }
            )

        # Check overall system health
        healthy_count = sum(
            1 for result in health_results.values() if result.get("healthy", False)
        )
        total_count = len(health_results)

        if healthy_count < total_count * 0.5:
            recommendations.append(
                {
                    "severity": "high",
                    "issue": "Majority of sources are unavailable",
                    "recommendation": "System requires immediate attention",
                    "action": "Check network connectivity and API configurations",
                }
            )

        # If everything is healthy, provide optimization suggestions
        if not recommendations:
            recommendations.append(
                {
                    "severity": "low",
                    "issue": "System operating normally",
                    "recommendation": "Consider enabling caching optimizations",
                    "action": "Monitor usage patterns for performance improvements",
                }
            )

        return recommendations

    def update_api_status(self, source_name: str, status: bool) -> None:
        """
        Update API status for a specific source.

        Args:
            source_name: Name of the API source
            status: True if healthy, False if unhealthy
        """
        self.api_status[source_name] = status
        self.logger.info(
            f"API status updated: {source_name} = {'healthy' if status else 'unhealthy'}"
        )

    def get_source_availability_summary(self) -> dict[str, Any]:
        """
        Get summary of source availability.

        Returns:
            Summary of available vs unavailable sources
        """
        available = sum(1 for status in self.api_status.values() if status)
        total = len(self.api_status)

        return {
            "available_sources": available,
            "total_sources": total,
            "availability_percentage": (available / total * 100) if total > 0 else 0,
            "status_detail": dict(self.api_status),
        }
