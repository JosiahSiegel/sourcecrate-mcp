"""
Search analytics and performance monitoring utilities.
Provides real-time insights into search performance and user patterns.
"""

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchSession:
    """Represents a search session with performance data."""

    session_id: str
    query: str
    timestamp: float
    total_time: float
    sources_used: list[str]
    results_found: int
    cache_hit: bool
    user_satisfaction: float | None = None  # 0-1 score if available


@dataclass
class SourcePerformanceSnapshot:
    """Performance snapshot for a search source."""

    source_name: str
    avg_response_time: float
    success_rate: float
    total_requests: int
    error_rate: float
    uptime_percentage: float
    last_24h_requests: int


@dataclass
class SystemPerformanceSnapshot:
    """Overall system performance snapshot."""

    timestamp: float
    total_searches: int
    avg_search_time: float
    cache_hit_rate: float
    concurrent_searches_peak: int
    memory_usage_mb: float
    top_performing_sources: list[str]
    bottleneck_sources: list[str]


class SearchAnalyticsCollector:
    """
    Collects and analyzes search performance data.

    Features:
    - Real-time performance monitoring
    - Query pattern analysis
    - Source reliability tracking
    - User behavior insights
    """

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size

        # Performance tracking
        self.search_history: deque = deque(maxlen=max_history_size)
        self.source_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "response_times": deque(maxlen=1000),
                "success_count": 0,
                "failure_count": 0,
                "total_requests": 0,
                "last_success": None,
                "last_failure": None,
                "circuit_breaker_trips": 0,
            }
        )

        # Query analytics
        self.query_patterns: dict[str, int] = defaultdict(int)
        self.domain_distribution: dict[str, int] = defaultdict(int)
        self.temporal_patterns: dict[int, int] = defaultdict(int)  # Hour of day
        self.result_quality_scores: deque = deque(maxlen=1000)

        # System metrics
        self.concurrent_searches = 0
        self.peak_concurrent_searches = 0
        self.cache_statistics = {"hits": 0, "misses": 0, "evictions": 0}

        # Performance thresholds
        self.performance_thresholds = {
            "slow_search_time": 10.0,  # seconds
            "low_success_rate": 0.7,
            "high_error_rate": 0.3,
            "cache_hit_rate_target": 0.3,
        }

        logger.info("📊 Search analytics collector initialized")

    def record_search(
        self,
        session_id: str,
        query: str,
        total_time: float,
        sources_used: list[str],
        results_found: int,
        cache_hit: bool = False,
        quality_score: float | None = None,
    ) -> None:
        """Record a completed search session."""
        session = SearchSession(
            session_id=session_id,
            query=query,
            timestamp=time.time(),
            total_time=total_time,
            sources_used=sources_used,
            results_found=results_found,
            cache_hit=cache_hit,
        )

        self.search_history.append(session)

        # Update query patterns
        normalized_query = self._normalize_query(query)
        self.query_patterns[normalized_query] += 1

        # Update domain distribution
        domain = self._detect_domain(query)
        if domain:
            self.domain_distribution[domain] += 1

        # Update temporal patterns
        hour = datetime.now().hour
        self.temporal_patterns[hour] += 1

        # Record quality score
        if quality_score is not None:
            self.result_quality_scores.append(quality_score)

        logger.debug(f"📝 Recorded search session: {query[:50]}... ({total_time:.2f}s)")

    def record_source_performance(
        self,
        source_name: str,
        response_time: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        """Record performance data for a specific source."""
        metrics = self.source_metrics[source_name]

        metrics["response_times"].append(response_time)
        metrics["total_requests"] += 1

        if success:
            metrics["success_count"] += 1
            metrics["last_success"] = time.time()
        else:
            metrics["failure_count"] += 1
            metrics["last_failure"] = time.time()
            if error_type:
                error_key = "error_types"
                if error_key not in metrics:
                    metrics[error_key] = defaultdict(int)
                metrics[error_key][error_type] += 1

    def record_cache_event(self, event_type: str) -> None:
        """Record cache-related events."""
        if event_type in self.cache_statistics:
            self.cache_statistics[event_type] += 1

    def start_concurrent_search(self) -> None:
        """Mark the start of a concurrent search."""
        self.concurrent_searches += 1
        if self.concurrent_searches > self.peak_concurrent_searches:
            self.peak_concurrent_searches = self.concurrent_searches

    def end_concurrent_search(self) -> None:
        """Mark the end of a concurrent search."""
        self.concurrent_searches = max(0, self.concurrent_searches - 1)

    def get_source_performance_snapshot(
        self, source_name: str
    ) -> SourcePerformanceSnapshot:
        """Get current performance snapshot for a source."""
        metrics = self.source_metrics[source_name]

        if not metrics["response_times"]:
            return SourcePerformanceSnapshot(
                source_name=source_name,
                avg_response_time=0.0,
                success_rate=0.0,
                total_requests=0,
                error_rate=0.0,
                uptime_percentage=0.0,
                last_24h_requests=0,
            )

        avg_response_time = statistics.mean(metrics["response_times"])
        total_requests = metrics["total_requests"]
        success_count = metrics["success_count"]
        failure_count = metrics["failure_count"]

        success_rate = success_count / total_requests if total_requests > 0 else 0.0
        error_rate = failure_count / total_requests if total_requests > 0 else 0.0

        # Calculate uptime percentage (simplified)
        uptime_percentage = success_rate * 100

        # Count last 24h requests (simplified)
        last_24h_requests = self._count_recent_requests(source_name, 24 * 3600)

        return SourcePerformanceSnapshot(
            source_name=source_name,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            total_requests=total_requests,
            error_rate=error_rate,
            uptime_percentage=uptime_percentage,
            last_24h_requests=last_24h_requests,
        )

    def get_system_performance_snapshot(self) -> SystemPerformanceSnapshot:
        """Get overall system performance snapshot."""
        total_searches = len(self.search_history)

        if total_searches == 0:
            return SystemPerformanceSnapshot(
                timestamp=time.time(),
                total_searches=0,
                avg_search_time=0.0,
                cache_hit_rate=0.0,
                concurrent_searches_peak=0,
                memory_usage_mb=0.0,
                top_performing_sources=[],
                bottleneck_sources=[],
            )

        # Calculate average search time
        recent_searches = list(self.search_history)[-1000:]  # Last 1000 searches
        avg_search_time = statistics.mean(s.total_time for s in recent_searches)

        # Calculate cache hit rate
        cache_hits = self.cache_statistics["hits"]
        cache_misses = self.cache_statistics["misses"]
        total_cache_requests = cache_hits + cache_misses
        cache_hit_rate = (
            cache_hits / total_cache_requests if total_cache_requests > 0 else 0.0
        )

        # Identify top performing and bottleneck sources
        top_sources, bottleneck_sources = self._identify_source_performance_tiers()

        return SystemPerformanceSnapshot(
            timestamp=time.time(),
            total_searches=total_searches,
            avg_search_time=avg_search_time,
            cache_hit_rate=cache_hit_rate,
            concurrent_searches_peak=self.peak_concurrent_searches,
            memory_usage_mb=0.0,  # Would need actual memory monitoring
            top_performing_sources=top_sources,
            bottleneck_sources=bottleneck_sources,
        )

    def get_performance_alerts(self) -> list[dict[str, Any]]:
        """Get performance alerts based on thresholds."""
        alerts = []

        # Check overall search performance
        if len(self.search_history) > 0:
            recent_searches = list(self.search_history)[-100:]  # Last 100 searches
            avg_time = statistics.mean(s.total_time for s in recent_searches)

            if avg_time > self.performance_thresholds["slow_search_time"]:
                alerts.append(
                    {
                        "type": "slow_search_performance",
                        "severity": "warning",
                        "message": f"Average search time is {avg_time:.1f}s (threshold: {self.performance_thresholds['slow_search_time']}s)",
                        "value": avg_time,
                        "threshold": self.performance_thresholds["slow_search_time"],
                    }
                )

        # Check cache performance
        cache_hits = self.cache_statistics["hits"]
        cache_misses = self.cache_statistics["misses"]
        if cache_hits + cache_misses > 0:
            cache_hit_rate = cache_hits / (cache_hits + cache_misses)
            if cache_hit_rate < self.performance_thresholds["cache_hit_rate_target"]:
                alerts.append(
                    {
                        "type": "low_cache_hit_rate",
                        "severity": "info",
                        "message": f"Cache hit rate is {cache_hit_rate:.1%} (target: {self.performance_thresholds['cache_hit_rate_target']:.1%})",
                        "value": cache_hit_rate,
                        "threshold": self.performance_thresholds[
                            "cache_hit_rate_target"
                        ],
                    }
                )

        # Check source performance
        for source_name, metrics in self.source_metrics.items():
            if metrics["total_requests"] < 10:
                continue  # Skip sources with insufficient data

            success_rate = metrics["success_count"] / metrics["total_requests"]
            if success_rate < self.performance_thresholds["low_success_rate"]:
                alerts.append(
                    {
                        "type": "low_source_success_rate",
                        "severity": "warning",
                        "message": f"Source {source_name} has low success rate: {success_rate:.1%}",
                        "source": source_name,
                        "value": success_rate,
                        "threshold": self.performance_thresholds["low_success_rate"],
                    }
                )

        return alerts

    def get_query_analytics(self) -> dict[str, Any]:
        """Get query pattern analytics."""
        if not self.query_patterns:
            return {
                "total_unique_queries": 0,
                "top_queries": [],
                "domain_distribution": {},
                "temporal_distribution": {},
                "avg_results_per_query": 0.0,
            }

        # Top queries
        top_queries = sorted(
            self.query_patterns.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Average results per query
        recent_searches = list(self.search_history)[-1000:]
        avg_results = (
            statistics.mean(s.results_found for s in recent_searches)
            if recent_searches
            else 0.0
        )

        return {
            "total_unique_queries": len(self.query_patterns),
            "top_queries": top_queries,
            "domain_distribution": dict(self.domain_distribution),
            "temporal_distribution": dict(self.temporal_patterns),
            "avg_results_per_query": avg_results,
        }

    def get_performance_recommendations(self) -> list[dict[str, str]]:
        """Get performance optimization recommendations."""
        recommendations = []

        # Analyze cache performance
        cache_hits = self.cache_statistics["hits"]
        cache_misses = self.cache_statistics["misses"]
        if cache_hits + cache_misses > 0:
            cache_hit_rate = cache_hits / (cache_hits + cache_misses)
            if cache_hit_rate < 0.2:
                recommendations.append(
                    {
                        "type": "caching",
                        "priority": "high",
                        "recommendation": "Consider increasing cache size or TTL - current hit rate is very low",
                        "current_value": f"{cache_hit_rate:.1%}",
                        "action": "Increase cache size or adjust TTL settings",
                    }
                )

        # Analyze source performance
        slow_sources = []
        for source_name, metrics in self.source_metrics.items():
            if metrics["response_times"] and len(metrics["response_times"]) > 10:
                avg_time = statistics.mean(metrics["response_times"])
                if avg_time > 5.0:  # Slow source threshold
                    slow_sources.append((source_name, avg_time))

        if slow_sources:
            slow_sources.sort(key=lambda x: x[1], reverse=True)
            recommendations.append(
                {
                    "type": "source_performance",
                    "priority": "medium",
                    "recommendation": f"Consider optimizing or deprioritizing slow sources: {', '.join(s[0] for s in slow_sources[:3])}",
                    "current_value": f"Slowest: {slow_sources[0][0]} ({slow_sources[0][1]:.1f}s avg)",
                    "action": "Implement circuit breakers or reduce timeout for slow sources",
                }
            )

        # Analyze concurrency
        if self.peak_concurrent_searches > 20:
            recommendations.append(
                {
                    "type": "concurrency",
                    "priority": "medium",
                    "recommendation": "High concurrency detected - consider implementing request throttling",
                    "current_value": f"Peak: {self.peak_concurrent_searches} concurrent searches",
                    "action": "Implement rate limiting or increase resource allocation",
                }
            )

        return recommendations

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern analysis."""
        return query.lower().strip()

    def _detect_domain(self, query: str) -> str | None:
        """Detect academic domain from query."""
        domain_keywords = {
            "medical": [
                "covid",
                "cancer",
                "treatment",
                "clinical",
                "patient",
                "diagnosis",
            ],
            "computer_science": [
                "algorithm",
                "machine learning",
                "neural",
                "computing",
                "software",
            ],
            "physics": ["quantum", "particle", "relativity", "thermodynamics"],
            "chemistry": ["molecular", "synthesis", "catalyst", "reaction"],
            "biology": ["genome", "protein", "evolution", "cell", "organism"],
        }

        query_lower = query.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return domain
        return None

    def _count_recent_requests(self, source_name: str, seconds: int) -> int:
        """Count requests to a source in the last N seconds."""
        current_time = time.time()
        cutoff_time = current_time - seconds

        count = 0
        for session in self.search_history:
            if session.timestamp >= cutoff_time and source_name in session.sources_used:
                count += 1

        return count

    def _identify_source_performance_tiers(self) -> tuple[list[str], list[str]]:
        """Identify top performing and bottleneck sources."""
        source_scores = []

        for source_name, metrics in self.source_metrics.items():
            if metrics["total_requests"] < 5:
                continue

            # Calculate composite performance score
            success_rate = metrics["success_count"] / metrics["total_requests"]
            avg_response_time = (
                statistics.mean(metrics["response_times"])
                if metrics["response_times"]
                else 10.0
            )

            # Higher score is better (high success rate, low response time)
            score = success_rate * (10.0 / max(1.0, avg_response_time))
            source_scores.append((source_name, score))

        if not source_scores:
            return [], []

        # Sort by score
        source_scores.sort(key=lambda x: x[1], reverse=True)

        # Top 30% are top performers, bottom 30% are bottlenecks
        num_sources = len(source_scores)
        top_count = max(1, num_sources // 3)
        bottom_count = max(1, num_sources // 3)

        top_sources = [s[0] for s in source_scores[:top_count]]
        bottleneck_sources = [s[0] for s in source_scores[-bottom_count:]]

        return top_sources, bottleneck_sources

    def export_analytics(self, include_raw_data: bool = False) -> dict[str, Any]:
        """Export comprehensive analytics data."""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "system_performance": self.get_system_performance_snapshot().__dict__,
            "query_analytics": self.get_query_analytics(),
            "performance_alerts": self.get_performance_alerts(),
            "recommendations": self.get_performance_recommendations(),
            "cache_statistics": self.cache_statistics.copy(),
            "source_summaries": {},
        }

        # Add source performance summaries
        for source_name in self.source_metrics.keys():
            source_summaries = export_data["source_summaries"]
            if isinstance(source_summaries, dict):
                source_summaries[source_name] = self.get_source_performance_snapshot(
                    source_name
                ).__dict__

        # Include raw data if requested
        if include_raw_data:
            export_data["raw_data"] = {
                "search_history": [
                    {
                        "query": s.query,
                        "timestamp": s.timestamp,
                        "total_time": s.total_time,
                        "sources_used": s.sources_used,
                        "results_found": s.results_found,
                        "cache_hit": s.cache_hit,
                    }
                    for s in list(self.search_history)[-1000:]  # Last 1000 searches
                ]
            }

        return export_data

    def reset_analytics_state(self) -> None:
        """Reset all analytics state for testing isolation."""
        self.search_history.clear()
        self.source_metrics.clear()
        self.query_patterns.clear()
        self.domain_distribution.clear()
        self.temporal_patterns.clear()
        self.result_quality_scores.clear()
        self.concurrent_searches = 0
        self.peak_concurrent_searches = 0
        self.cache_statistics = {"hits": 0, "misses": 0, "evictions": 0}


# Global analytics collector instance
search_analytics = SearchAnalyticsCollector()


def record_search_performance(
    session_id: str,
    query: str,
    total_time: float,
    sources_used: list[str],
    results_found: int,
    cache_hit: bool = False,
    quality_score: float | None = None,
) -> None:
    """Convenience function to record search performance."""
    search_analytics.record_search(
        session_id,
        query,
        total_time,
        sources_used,
        results_found,
        cache_hit,
        quality_score,
    )


def get_performance_dashboard() -> dict[str, Any]:
    """Get comprehensive performance dashboard data."""
    return {
        "system_overview": search_analytics.get_system_performance_snapshot().__dict__,
        "alerts": search_analytics.get_performance_alerts(),
        "recommendations": search_analytics.get_performance_recommendations(),
        "query_insights": search_analytics.get_query_analytics(),
        "source_performance": {
            source_name: search_analytics.get_source_performance_snapshot(
                source_name
            ).__dict__
            for source_name in search_analytics.source_metrics.keys()
        },
    }
