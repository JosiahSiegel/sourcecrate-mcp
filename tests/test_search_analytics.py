"""
Unit tests for search analytics functionality.
Tests performance monitoring, analytics collection, and reporting.
"""

import time
from unittest.mock import patch

from source_crate.utils.search_analytics import (
    SearchAnalyticsCollector,
    SearchSession,
    SourcePerformanceSnapshot,
    SystemPerformanceSnapshot,
    get_performance_dashboard,
    record_search_performance,
    search_analytics,
)


class TestSearchSession:
    """Test suite for SearchSession dataclass."""

    def test_search_session_creation(self) -> None:
        """Test creation of SearchSession."""
        session = SearchSession(
            session_id="test-123",
            query="machine learning",
            timestamp=time.time(),
            total_time=2.5,
            sources_used=["arxiv", "pubmed"],
            results_found=10,
            cache_hit=True,
            user_satisfaction=0.8,
        )

        assert session.session_id == "test-123"
        assert session.query == "machine learning"
        assert session.total_time == 2.5
        assert len(session.sources_used) == 2
        assert session.results_found == 10
        assert session.cache_hit is True
        assert session.user_satisfaction == 0.8


class TestSourcePerformanceSnapshot:
    """Test suite for SourcePerformanceSnapshot dataclass."""

    def test_source_snapshot_creation(self) -> None:
        """Test creation of SourcePerformanceSnapshot."""
        snapshot = SourcePerformanceSnapshot(
            source_name="arxiv",
            avg_response_time=1.5,
            success_rate=0.95,
            total_requests=100,
            error_rate=0.05,
            uptime_percentage=99.5,
            last_24h_requests=50,
        )

        assert snapshot.source_name == "arxiv"
        assert snapshot.avg_response_time == 1.5
        assert snapshot.success_rate == 0.95
        assert snapshot.total_requests == 100
        assert snapshot.error_rate == 0.05
        assert snapshot.uptime_percentage == 99.5
        assert snapshot.last_24h_requests == 50


class TestSystemPerformanceSnapshot:
    """Test suite for SystemPerformanceSnapshot dataclass."""

    def test_system_snapshot_creation(self) -> None:
        """Test creation of SystemPerformanceSnapshot."""
        snapshot = SystemPerformanceSnapshot(
            timestamp=time.time(),
            total_searches=1000,
            avg_search_time=2.3,
            cache_hit_rate=0.4,
            concurrent_searches_peak=15,
            memory_usage_mb=512.0,
            top_performing_sources=["arxiv", "semantic_scholar"],
            bottleneck_sources=["slow_source"],
        )

        assert snapshot.total_searches == 1000
        assert snapshot.avg_search_time == 2.3
        assert snapshot.cache_hit_rate == 0.4
        assert snapshot.concurrent_searches_peak == 15
        assert len(snapshot.top_performing_sources) == 2
        assert len(snapshot.bottleneck_sources) == 1


class TestSearchAnalyticsCollector:
    """Test suite for SearchAnalyticsCollector class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.collector = SearchAnalyticsCollector(max_history_size=1000)

    def test_collector_initialization(self) -> None:
        """Test analytics collector initialization."""
        assert self.collector.max_history_size == 1000
        assert len(self.collector.search_history) == 0
        assert len(self.collector.source_metrics) == 0
        assert len(self.collector.query_patterns) == 0
        assert self.collector.concurrent_searches == 0
        assert self.collector.peak_concurrent_searches == 0

    def test_record_search(self) -> None:
        """Test recording search sessions."""
        self.collector.record_search(
            session_id="test-1",
            query="machine learning",
            total_time=2.0,
            sources_used=["arxiv", "pubmed"],
            results_found=5,
            cache_hit=False,
            quality_score=0.8,
        )

        assert len(self.collector.search_history) == 1
        session = self.collector.search_history[0]
        assert session.query == "machine learning"
        assert session.total_time == 2.0
        assert len(session.sources_used) == 2
        assert session.results_found == 5

        # Check query patterns update
        assert "machine learning" in self.collector.query_patterns
        assert self.collector.query_patterns["machine learning"] == 1

        # Check quality scores
        assert len(self.collector.result_quality_scores) == 1
        assert self.collector.result_quality_scores[0] == 0.8

    def test_record_source_performance(self) -> None:
        """Test recording source performance data."""
        source = "arxiv"

        # Record successful operation
        self.collector.record_source_performance(source, 1.5, True)

        metrics = self.collector.source_metrics[source]
        assert metrics["total_requests"] == 1
        assert metrics["success_count"] == 1
        assert metrics["failure_count"] == 0
        assert len(metrics["response_times"]) == 1
        assert metrics["response_times"][0] == 1.5

        # Record failed operation
        self.collector.record_source_performance(source, 3.0, False, "timeout")

        assert metrics["total_requests"] == 2
        assert metrics["success_count"] == 1
        assert metrics["failure_count"] == 1
        assert len(metrics["response_times"]) == 2

    def test_cache_event_recording(self) -> None:
        """Test recording cache events."""
        self.collector.record_cache_event("hits")
        self.collector.record_cache_event("hits")
        self.collector.record_cache_event("misses")

        assert self.collector.cache_statistics["hits"] == 2
        assert self.collector.cache_statistics["misses"] == 1

    def test_concurrent_search_tracking(self) -> None:
        """Test concurrent search tracking."""
        # Start concurrent searches
        self.collector.start_concurrent_search()
        self.collector.start_concurrent_search()
        self.collector.start_concurrent_search()

        assert self.collector.concurrent_searches == 3
        assert self.collector.peak_concurrent_searches == 3

        # End some searches
        self.collector.end_concurrent_search()
        self.collector.end_concurrent_search()

        assert self.collector.concurrent_searches == 1
        assert self.collector.peak_concurrent_searches == 3  # Peak should remain

    def test_source_performance_snapshot(self) -> None:
        """Test source performance snapshot generation."""
        source = "test_source"

        # Add performance data
        self.collector.record_source_performance(source, 1.0, True)
        self.collector.record_source_performance(source, 2.0, True)
        self.collector.record_source_performance(source, 3.0, False)

        snapshot = self.collector.get_source_performance_snapshot(source)

        assert snapshot.source_name == source
        assert snapshot.avg_response_time == 2.0  # (1+2+3)/3
        assert snapshot.total_requests == 3
        assert snapshot.success_rate == 2 / 3  # 2 successes out of 3
        assert snapshot.error_rate == 1 / 3  # 1 failure out of 3

    def test_source_performance_snapshot_empty(self) -> None:
        """Test source performance snapshot with no data."""
        snapshot = self.collector.get_source_performance_snapshot("nonexistent")

        assert snapshot.source_name == "nonexistent"
        assert snapshot.avg_response_time == 0.0
        assert snapshot.success_rate == 0.0
        assert snapshot.total_requests == 0

    def test_system_performance_snapshot(self) -> None:
        """Test system performance snapshot generation."""
        # Add some search history
        for i in range(5):
            self.collector.record_search(
                session_id=f"test-{i}",
                query=f"query {i}",
                total_time=1.0 + i * 0.5,
                sources_used=["arxiv"],
                results_found=10,
                cache_hit=i % 2 == 0,
            )

        # Add cache statistics
        self.collector.record_cache_event("hits")
        self.collector.record_cache_event("hits")
        self.collector.record_cache_event("misses")

        snapshot = self.collector.get_system_performance_snapshot()

        assert snapshot.total_searches == 5
        assert snapshot.avg_search_time > 0
        assert snapshot.cache_hit_rate == 2 / 3  # 2 hits, 1 miss

    def test_system_performance_snapshot_empty(self) -> None:
        """Test system performance snapshot with no data."""
        snapshot = self.collector.get_system_performance_snapshot()

        assert snapshot.total_searches == 0
        assert snapshot.avg_search_time == 0.0
        assert snapshot.cache_hit_rate == 0.0
        assert snapshot.concurrent_searches_peak == 0

    def test_performance_alerts_slow_search(self) -> None:
        """Test performance alerts for slow searches."""
        # Add slow searches
        for i in range(10):
            self.collector.record_search(
                session_id=f"slow-{i}",
                query="test",
                total_time=15.0,  # Above threshold
                sources_used=["slow_source"],
                results_found=5,
            )

        alerts = self.collector.get_performance_alerts()

        # Should have slow search alert
        slow_alerts = [a for a in alerts if a["type"] == "slow_search_performance"]
        assert len(slow_alerts) > 0
        assert slow_alerts[0]["severity"] == "warning"

    def test_performance_alerts_low_cache_hit_rate(self) -> None:
        """Test performance alerts for low cache hit rate."""
        # Add cache misses
        for _ in range(10):
            self.collector.record_cache_event("misses")

        # Add few hits
        self.collector.record_cache_event("hits")

        alerts = self.collector.get_performance_alerts()

        # Should have low cache hit rate alert
        cache_alerts = [a for a in alerts if a["type"] == "low_cache_hit_rate"]
        assert len(cache_alerts) > 0

    def test_performance_alerts_low_source_success_rate(self) -> None:
        """Test performance alerts for low source success rate."""
        source = "unreliable_source"

        # Add mostly failed requests
        for _ in range(8):
            self.collector.record_source_performance(source, 2.0, False)

        # Add few successes
        for _ in range(2):
            self.collector.record_source_performance(source, 1.0, True)

        alerts = self.collector.get_performance_alerts()

        # Should have low success rate alert
        success_alerts = [a for a in alerts if a["type"] == "low_source_success_rate"]
        assert len(success_alerts) > 0
        assert success_alerts[0]["source"] == source

    def test_query_analytics(self) -> None:
        """Test query analytics generation."""
        # Add various queries
        queries = [
            "machine learning",
            "neural networks",
            "machine learning",
            "deep learning",
        ]
        for i, query in enumerate(queries):
            self.collector.record_search(
                session_id=f"query-{i}",
                query=query,
                total_time=2.0,
                sources_used=["arxiv"],
                results_found=5 + i,
            )

        analytics = self.collector.get_query_analytics()

        assert analytics["total_unique_queries"] == 3  # unique queries
        assert len(analytics["top_queries"]) > 0
        assert analytics["top_queries"][0][0] == "machine learning"  # Most frequent
        assert analytics["top_queries"][0][1] == 2  # Frequency
        assert analytics["avg_results_per_query"] > 0

    def test_query_analytics_empty(self) -> None:
        """Test query analytics with no data."""
        analytics = self.collector.get_query_analytics()

        assert analytics["total_unique_queries"] == 0
        assert len(analytics["top_queries"]) == 0
        assert analytics["avg_results_per_query"] == 0.0

    def test_domain_detection(self) -> None:
        """Test academic domain detection."""
        # Test medical domain
        medical_domain = self.collector._detect_domain("covid treatment protocols")
        assert medical_domain == "medical"

        # Test computer science domain
        cs_domain = self.collector._detect_domain("machine learning algorithms")
        assert cs_domain == "computer_science"

        # Test physics domain
        physics_domain = self.collector._detect_domain("quantum mechanics")
        assert physics_domain == "physics"

        # Test unknown domain
        unknown_domain = self.collector._detect_domain("random unrelated topic")
        assert unknown_domain is None

    def test_performance_recommendations(self) -> None:
        """Test performance recommendations generation."""
        # Create scenario with low cache hit rate
        for _ in range(20):
            self.collector.record_cache_event("misses")
        self.collector.record_cache_event("hits")

        # Create scenario with slow sources
        slow_source = "very_slow_source"
        for _ in range(15):
            self.collector.record_source_performance(slow_source, 8.0, True)

        # Create scenario with high concurrency
        self.collector.peak_concurrent_searches = 25

        recommendations = self.collector.get_performance_recommendations()

        # Should have multiple recommendations
        assert len(recommendations) > 0

        # Check for caching recommendation
        cache_recs = [r for r in recommendations if r["type"] == "caching"]
        assert len(cache_recs) > 0

        # Check for source performance recommendation
        source_recs = [r for r in recommendations if r["type"] == "source_performance"]
        assert len(source_recs) > 0

        # Check for concurrency recommendation
        concurrency_recs = [r for r in recommendations if r["type"] == "concurrency"]
        assert len(concurrency_recs) > 0

    def test_temporal_patterns(self) -> None:
        """Test temporal pattern tracking."""
        # Mock datetime to control hour
        with patch("source_crate.utils.search_analytics.datetime") as mock_datetime:
            # Set to specific hour
            mock_datetime.now.return_value.hour = 14  # 2 PM

            self.collector.record_search(
                session_id="temporal-1",
                query="test",
                total_time=1.0,
                sources_used=["arxiv"],
                results_found=5,
            )

            # Check temporal patterns
            assert 14 in self.collector.temporal_patterns
            assert self.collector.temporal_patterns[14] == 1

    def test_count_recent_requests(self) -> None:
        """Test counting recent requests to a source."""
        current_time = time.time()

        # Add recent search
        self.collector.search_history.append(
            SearchSession(
                session_id="recent",
                query="test",
                timestamp=current_time - 30,  # 30 seconds ago
                total_time=1.0,
                sources_used=["test_source"],
                results_found=5,
                cache_hit=False,
            )
        )

        # Add old search
        self.collector.search_history.append(
            SearchSession(
                session_id="old",
                query="test",
                timestamp=current_time - 7200,  # 2 hours ago
                total_time=1.0,
                sources_used=["test_source"],
                results_found=5,
                cache_hit=False,
            )
        )

        # Count requests in last hour (3600 seconds)
        recent_count = self.collector._count_recent_requests("test_source", 3600)
        assert recent_count == 1  # Only the recent one

    def test_source_performance_tiers(self) -> None:
        """Test identification of top performing and bottleneck sources."""
        # Add good performing source
        good_source = "fast_reliable"
        for _ in range(10):
            self.collector.record_source_performance(good_source, 0.5, True)

        # Add poor performing source
        poor_source = "slow_unreliable"
        for _ in range(10):
            self.collector.record_source_performance(poor_source, 5.0, False)

        # Add medium performing source
        medium_source = "average_source"
        for _ in range(10):
            self.collector.record_source_performance(medium_source, 2.0, True)

        top_sources, bottleneck_sources = (
            self.collector._identify_source_performance_tiers()
        )

        # Good source should be in top performers
        assert good_source in top_sources

        # Poor source should be in bottlenecks
        assert poor_source in bottleneck_sources

    def test_export_analytics(self) -> None:
        """Test analytics data export."""
        # Add some data
        self.collector.record_search(
            session_id="export-test",
            query="test export",
            total_time=1.5,
            sources_used=["arxiv"],
            results_found=3,
        )

        self.collector.record_source_performance("arxiv", 1.0, True)
        self.collector.record_cache_event("hits")

        # Export without raw data
        export_data = self.collector.export_analytics(include_raw_data=False)

        assert "timestamp" in export_data
        assert "system_performance" in export_data
        assert "query_analytics" in export_data
        assert "performance_alerts" in export_data
        assert "recommendations" in export_data
        assert "cache_statistics" in export_data
        assert "source_summaries" in export_data
        assert "raw_data" not in export_data

        # Export with raw data
        export_data_with_raw = self.collector.export_analytics(include_raw_data=True)

        assert "raw_data" in export_data_with_raw
        assert "search_history" in export_data_with_raw["raw_data"]

    def test_history_size_limit(self) -> None:
        """Test that search history respects size limit."""
        small_collector = SearchAnalyticsCollector(max_history_size=5)

        # Add more searches than the limit
        for i in range(10):
            small_collector.record_search(
                session_id=f"test-{i}",
                query=f"query {i}",
                total_time=1.0,
                sources_used=["arxiv"],
                results_found=5,
            )

        # Should only keep the last 5
        assert len(small_collector.search_history) == 5

        # Check that it's the latest ones
        latest_session = small_collector.search_history[-1]
        assert latest_session.query == "query 9"


class TestGlobalAnalyticsInstance:
    """Test suite for global analytics instance."""

    def test_global_analytics_exists(self) -> None:
        """Test that global analytics instance exists."""
        assert search_analytics is not None
        assert isinstance(search_analytics, SearchAnalyticsCollector)

    def test_record_search_performance_function(self) -> None:
        """Test convenience function for recording performance."""
        # Clear any existing data
        search_analytics.search_history.clear()

        record_search_performance(
            session_id="global-test",
            query="global test query",
            total_time=2.0,
            sources_used=["arxiv", "pubmed"],
            results_found=8,
            cache_hit=True,
            quality_score=0.9,
        )

        # Should be recorded in global instance
        assert len(search_analytics.search_history) >= 1

        # Find our session
        our_session = None
        for session in search_analytics.search_history:
            if session.session_id == "global-test":
                our_session = session
                break

        assert our_session is not None
        assert our_session.query == "global test query"
        assert our_session.total_time == 2.0
        assert our_session.cache_hit is True

    def test_get_performance_dashboard_function(self) -> None:
        """Test performance dashboard function."""
        dashboard = get_performance_dashboard()

        assert isinstance(dashboard, dict)
        assert "system_overview" in dashboard
        assert "alerts" in dashboard
        assert "recommendations" in dashboard
        assert "query_insights" in dashboard
        assert "source_performance" in dashboard


class TestSearchAnalyticsIntegration:
    """Integration tests for search analytics with realistic scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.collector = SearchAnalyticsCollector()

    def test_realistic_search_pattern(self) -> None:
        """Test analytics with realistic search patterns."""
        # Simulate a day of searches with various patterns
        search_patterns = [
            ("machine learning", 2.1, ["arxiv", "semantic_scholar"], 8, True),
            ("neural networks", 1.8, ["arxiv"], 5, False),
            ("covid treatment", 3.2, ["pubmed", "europe_pmc"], 12, False),
            ("quantum computing", 1.5, ["arxiv"], 3, True),
            ("machine learning", 0.5, ["cache"], 8, True),  # Cache hit
        ]

        for i, (query, time_taken, sources, results, cache_hit) in enumerate(
            search_patterns
        ):
            self.collector.record_search(
                session_id=f"realistic-{i}",
                query=query,
                total_time=time_taken,
                sources_used=sources,
                results_found=results,
                cache_hit=cache_hit,
                quality_score=0.7 + (i * 0.05),
            )

            # Record source performance
            for source in sources:
                if source != "cache":
                    self.collector.record_source_performance(
                        source, time_taken / len(sources), True
                    )

        # Analyze results
        analytics = self.collector.get_query_analytics()
        assert analytics["total_unique_queries"] == 4
        assert analytics["top_queries"][0][0] == "machine learning"  # Most frequent

        # Check domain distribution
        assert "computer_science" in self.collector.domain_distribution
        assert "medical" in self.collector.domain_distribution

        # Check performance metrics
        arxiv_snapshot = self.collector.get_source_performance_snapshot("arxiv")
        assert arxiv_snapshot.total_requests > 0
        assert arxiv_snapshot.success_rate > 0

    def test_performance_degradation_detection(self) -> None:
        """Test detection of performance degradation over time."""
        source = "degrading_source"

        # Initial good performance
        for _ in range(30):
            self.collector.record_source_performance(source, 1.0, True)

        # Performance starts degrading significantly
        for _ in range(50):
            self.collector.record_source_performance(source, 8.0, False)

        alerts = self.collector.get_performance_alerts()
        source_alerts = [a for a in alerts if a.get("source") == source]
        assert len(source_alerts) > 0

        recommendations = self.collector.get_performance_recommendations()
        source_recs = [
            r for r in recommendations if "slow sources" in r.get("recommendation", "")
        ]
        assert len(source_recs) > 0

    def test_cache_effectiveness_analysis(self) -> None:
        """Test analysis of cache effectiveness."""
        # Simulate searches with varying cache performance
        cache_scenarios = [
            (True, "Popular Query A"),  # Cache hit
            (False, "Unique Query 1"),  # Cache miss
            (True, "Popular Query A"),  # Cache hit
            (False, "Unique Query 2"),  # Cache miss
            (True, "Popular Query B"),  # Cache hit after warming
        ]

        for cache_hit, query in cache_scenarios:
            if cache_hit:
                self.collector.record_cache_event("hits")
            else:
                self.collector.record_cache_event("misses")

            self.collector.record_search(
                session_id=f"cache-{len(self.collector.search_history)}",
                query=query,
                total_time=0.5 if cache_hit else 2.0,
                sources_used=["cache"] if cache_hit else ["arxiv"],
                results_found=5,
                cache_hit=cache_hit,
            )

        # Analyze cache performance
        system_snapshot = self.collector.get_system_performance_snapshot()
        assert system_snapshot.cache_hit_rate == 0.6  # 3 hits out of 5

        # Check if cache recommendations are appropriate
        if system_snapshot.cache_hit_rate < 0.3:
            recommendations = self.collector.get_performance_recommendations()
            cache_recs = [r for r in recommendations if r["type"] == "caching"]
            assert len(cache_recs) > 0
