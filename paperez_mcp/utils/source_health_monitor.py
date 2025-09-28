"""
Source health monitoring system for proactive detection of source degradation.
Tracks API response times, success rates, and content quality.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..config import api_status, cache

logger = logging.getLogger(__name__)


@dataclass
class SourceMetrics:
    """Health metrics for a single source"""
    source_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_success_time: datetime | None = None
    last_failure_time: datetime | None = None
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=10))
    recent_result_counts: deque = field(default_factory=lambda: deque(maxlen=10))
    consecutive_failures: int = 0
    health_score: float = 1.0  # 0.0 to 1.0

    def update_success(self, response_time: float, result_count: int):
        """Update metrics after a successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()

        self.recent_response_times.append(response_time)
        self.recent_result_counts.append(result_count)

        # Update average response time
        if self.recent_response_times:
            self.average_response_time = sum(self.recent_response_times) / len(self.recent_response_times)

        self._calculate_health_score()

    def update_failure(self, error_type: str = "unknown"):
        """Update metrics after a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_failure_time = datetime.now()

        self._calculate_health_score()

    def _calculate_health_score(self):
        """Calculate overall health score based on multiple factors"""
        if self.total_requests == 0:
            self.health_score = 1.0
            return

        # Base success rate (0-1)
        success_rate = self.successful_requests / self.total_requests

        # Penalty for consecutive failures
        consecutive_penalty = min(0.1 * self.consecutive_failures, 0.5)

        # Penalty for slow response times (>5 seconds)
        response_penalty = 0.0
        if self.average_response_time > 5.0:
            response_penalty = min(0.2, (self.average_response_time - 5.0) / 10.0)

        # Penalty for low result counts
        result_penalty = 0.0
        if self.recent_result_counts:
            avg_results = sum(self.recent_result_counts) / len(self.recent_result_counts)
            if avg_results < 1.0:  # Very few results consistently
                result_penalty = 0.1

        # Calculate final score
        self.health_score = max(0.0, success_rate - consecutive_penalty - response_penalty - result_penalty)

    def is_healthy(self) -> bool:
        """Check if source is considered healthy"""
        return (self.health_score > 0.5 and
                self.consecutive_failures < 3 and
                (self.last_success_time is None or
                 (datetime.now() - self.last_success_time).total_seconds() < 3600))  # Success within last hour

    def get_status_summary(self) -> dict[str, Any]:
        """Get a summary of source status"""
        return {
            "source": self.source_name,
            "health_score": round(self.health_score, 3),
            "is_healthy": self.is_healthy(),
            "success_rate": round(self.successful_requests / max(1, self.total_requests), 3),
            "average_response_time": round(self.average_response_time, 2),
            "consecutive_failures": self.consecutive_failures,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "total_requests": self.total_requests
        }


class SourceHealthMonitor:
    """Monitors health of all academic database sources"""

    def __init__(self):
        self.metrics: dict[str, SourceMetrics] = {}
        self.monitoring_enabled = True

        # Initialize metrics for all known sources
        source_names = [
            'crossref', 'semantic_scholar', 'arxiv', 'pubmed', 'pubmed_central',
            'clinicaltrials', 'google_scholar', 'core', 'doaj', 'socarxiv', 'osf_preprints'
        ]

        for source in source_names:
            self.metrics[source] = SourceMetrics(source_name=source)

    async def monitor_request(self, source_name: str, search_func, *args, **kwargs):
        """Monitor a request to a source and update metrics"""
        if not self.monitoring_enabled or source_name not in self.metrics:
            # If monitoring disabled or unknown source, just call the function
            return await search_func(*args, **kwargs)

        start_time = time.time()
        metrics = self.metrics[source_name]

        try:
            # Execute the search function
            results = await search_func(*args, **kwargs)
            response_time = time.time() - start_time

            # Update success metrics
            result_count = len(results) if isinstance(results, list) else 0
            metrics.update_success(response_time, result_count)

            # Update global API status
            api_status[source_name] = True

            logger.debug(f"✅ {source_name}: {result_count} results in {response_time:.2f}s (health: {metrics.health_score:.3f})")

            return results

        except Exception as e:
            response_time = time.time() - start_time

            # Update failure metrics
            error_type = type(e).__name__
            metrics.update_failure(error_type)

            # Update global API status if too many consecutive failures
            if metrics.consecutive_failures >= 3:
                api_status[source_name] = False
                logger.warning(f"❌ {source_name}: Marked as unhealthy after {metrics.consecutive_failures} consecutive failures")

            logger.warning(f"❌ {source_name}: {error_type} in {response_time:.2f}s (health: {metrics.health_score:.3f})")

            # Re-raise the exception to maintain normal error handling
            raise

    def get_health_report(self) -> dict[str, Any]:
        """Generate comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "sources": {},
            "summary": {
                "total_sources": len(self.metrics),
                "healthy_sources": 0,
                "unhealthy_sources": 0,
                "disabled_sources": 0
            }
        }

        for source_name, metrics in self.metrics.items():
            source_status = metrics.get_status_summary()
            report["sources"][source_name] = source_status

            if api_status.get(source_name, False):
                if metrics.is_healthy():
                    report["summary"]["healthy_sources"] += 1
                else:
                    report["summary"]["unhealthy_sources"] += 1
            else:
                report["summary"]["disabled_sources"] += 1

        # Determine overall status
        if report["summary"]["unhealthy_sources"] > 0 or report["summary"]["disabled_sources"] > 3:
            report["overall_status"] = "degraded"
        if report["summary"]["healthy_sources"] < 3:
            report["overall_status"] = "critical"

        return report

    def get_source_recommendations(self) -> list[dict[str, Any]]:
        """Get recommendations for improving source health"""
        recommendations = []

        for source_name, metrics in self.metrics.items():
            if not metrics.is_healthy():
                if metrics.consecutive_failures >= 3:
                    recommendations.append({
                        "source": source_name,
                        "severity": "high",
                        "issue": "Multiple consecutive failures",
                        "recommendation": "Check API credentials and network connectivity",
                        "action": f"Investigate {source_name} API issues"
                    })
                elif metrics.average_response_time > 10.0:
                    recommendations.append({
                        "source": source_name,
                        "severity": "medium",
                        "issue": f"Slow response times ({metrics.average_response_time:.1f}s)",
                        "recommendation": "Consider implementing request caching or rate limiting",
                        "action": f"Optimize {source_name} request patterns"
                    })
                elif metrics.health_score < 0.7:
                    recommendations.append({
                        "source": source_name,
                        "severity": "low",
                        "issue": f"Low health score ({metrics.health_score:.3f})",
                        "recommendation": "Monitor for patterns and consider backup sources",
                        "action": f"Keep monitoring {source_name} performance"
                    })

        return recommendations

    async def perform_health_check(self) -> dict[str, Any]:
        """Perform active health check on all sources"""
        logger.info("🔍 Performing active health check on all sources...")

        # Simple test queries for each source type
        test_queries = {
            'crossref': 'machine learning',
            'semantic_scholar': 'artificial intelligence',
            'arxiv': 'neural networks',
            'pubmed': 'diabetes treatment',
            'pubmed_central': 'cancer therapy',
            'clinicaltrials': 'diabetes',
            'google_scholar': 'computer science',
            'core': 'climate change',
            'doaj': 'open access',
            'socarxiv': 'social science',
            'osf_preprints': 'psychology'
        }

        # Use unified config system
        from ..config import get_search_service

        search_service = get_search_service()
        search_functions = search_service.get_search_functions()

        health_results = {}

        for source_name in test_queries:
            if source_name in search_functions:
                try:
                    query = test_queries[source_name]
                    search_func = search_functions[source_name]

                    # Monitor the health check request
                    results = await self.monitor_request(source_name, search_func, query, 3)

                    health_results[source_name] = {
                        "status": "healthy",
                        "test_query": query,
                        "results_found": len(results) if results else 0,
                        "response_time": self.metrics[source_name].recent_response_times[-1] if self.metrics[source_name].recent_response_times else 0
                    }

                except Exception as e:
                    health_results[source_name] = {
                        "status": "unhealthy",
                        "test_query": test_queries[source_name],
                        "error": str(e),
                        "error_type": type(e).__name__
                    }

        return {
            "health_check_results": health_results,
            "overall_report": self.get_health_report(),
            "recommendations": self.get_source_recommendations()
        }

    def save_metrics_to_cache(self):
        """Save current metrics to cache for persistence"""
        cache_data = {}
        for source_name, metrics in self.metrics.items():
            cache_data[source_name] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "consecutive_failures": metrics.consecutive_failures,
                "health_score": metrics.health_score,
                "last_success_time": metrics.last_success_time.isoformat() if metrics.last_success_time else None,
                "last_failure_time": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None
            }

        cache.set("source_health_metrics", cache_data, expire=86400)  # 24 hours

    def load_metrics_from_cache(self):
        """Load saved metrics from cache"""
        cache_data = cache.get("source_health_metrics")
        if cache_data:
            for source_name, data in cache_data.items():
                if source_name in self.metrics:
                    metrics = self.metrics[source_name]
                    metrics.total_requests = data.get("total_requests", 0)
                    metrics.successful_requests = data.get("successful_requests", 0)
                    metrics.failed_requests = data.get("failed_requests", 0)
                    metrics.consecutive_failures = data.get("consecutive_failures", 0)
                    metrics.health_score = data.get("health_score", 1.0)

                    if data.get("last_success_time"):
                        metrics.last_success_time = datetime.fromisoformat(data["last_success_time"])
                    if data.get("last_failure_time"):
                        metrics.last_failure_time = datetime.fromisoformat(data["last_failure_time"])


# Global instance
health_monitor = SourceHealthMonitor()

# Load any existing metrics on import
health_monitor.load_metrics_from_cache()
