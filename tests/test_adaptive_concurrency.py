"""
Unit tests for adaptive concurrency management functionality.
Tests concurrency control, circuit breakers, and performance-based adjustments.
"""

import asyncio
import time

import pytest

from paperez_mcp.utils.adaptive_concurrency import (
    AdaptiveConcurrencyManager,
    SourcePerformanceMetrics,
    adaptive_concurrency_manager,
)


class TestSourcePerformanceMetrics:
    """Test suite for SourcePerformanceMetrics class."""

    def test_metrics_initialization(self):
        """Test metrics creation with default values."""
        metrics = SourcePerformanceMetrics("test_source")

        assert metrics.name == "test_source"
        assert metrics.avg_response_time == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.error_count == 0
        assert metrics.total_requests == 0
        assert metrics.consecutive_failures == 0
        assert metrics.last_success_time is None
        assert metrics.circuit_breaker_open is False
        assert metrics.circuit_breaker_open_time is None

    def test_metrics_with_custom_values(self):
        """Test metrics creation with custom values."""
        metrics = SourcePerformanceMetrics(
            name="custom_source",
            avg_response_time=2.5,
            success_rate=0.8,
            error_count=5,
            total_requests=100,
        )

        assert metrics.name == "custom_source"
        assert metrics.avg_response_time == 2.5
        assert metrics.success_rate == 0.8
        assert metrics.error_count == 5
        assert metrics.total_requests == 100


class TestAdaptiveConcurrencyManager:
    """Test suite for AdaptiveConcurrencyManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = AdaptiveConcurrencyManager(
            base_concurrency=3,
            max_concurrency=10,
            min_concurrency=1,
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=5.0,  # Short timeout for testing
        )

    def test_manager_initialization(self):
        """Test manager initialization with parameters."""
        assert self.manager.base_concurrency == 3
        assert self.manager.max_concurrency == 10
        assert self.manager.min_concurrency == 1
        assert self.manager.circuit_breaker_threshold == 2
        assert self.manager.circuit_breaker_timeout == 5.0
        assert self.manager.current_concurrency == 3
        assert len(self.manager.source_metrics) == 0

    def test_get_source_metrics(self):
        """Test source metrics retrieval and creation."""
        # Get metrics for new source
        metrics = self.manager.get_source_metrics("new_source")

        assert metrics.name == "new_source"
        assert "new_source" in self.manager.source_metrics

        # Get same metrics again should return same instance
        metrics2 = self.manager.get_source_metrics("new_source")
        assert metrics is metrics2

    def test_circuit_breaker_closed_initially(self):
        """Test that circuit breaker is closed for new sources."""
        assert self.manager.is_circuit_breaker_open("test_source") is False

    def test_circuit_breaker_threshold(self):
        """Test circuit breaker opening after threshold failures."""
        source_name = "failing_source"

        # Record failures up to threshold
        for i in range(self.manager.circuit_breaker_threshold):
            self.manager.update_source_performance(source_name, 1.0, False)

            if i < self.manager.circuit_breaker_threshold - 1:
                assert self.manager.is_circuit_breaker_open(source_name) is False

        # Should be open after threshold
        assert self.manager.is_circuit_breaker_open(source_name) is True

        metrics = self.manager.get_source_metrics(source_name)
        assert metrics.circuit_breaker_open is True
        assert metrics.consecutive_failures == self.manager.circuit_breaker_threshold

    def test_circuit_breaker_recovery_after_timeout(self):
        """Test circuit breaker recovery after timeout."""
        source_name = "recovery_source"

        # Open circuit breaker
        for _ in range(self.manager.circuit_breaker_threshold):
            self.manager.update_source_performance(source_name, 1.0, False)

        assert self.manager.is_circuit_breaker_open(source_name) is True

        # Manually set open time to past for timeout test
        metrics = self.manager.get_source_metrics(source_name)
        metrics.circuit_breaker_open_time = time.time() - (
            self.manager.circuit_breaker_timeout + 1
        )

        # Should be recovered now
        assert self.manager.is_circuit_breaker_open(source_name) is False
        assert metrics.circuit_breaker_open is False
        assert metrics.consecutive_failures == 0

    def test_update_source_performance_success(self):
        """Test updating performance metrics for successful operations."""
        source_name = "success_source"

        # First success
        self.manager.update_source_performance(source_name, 2.0, True)

        metrics = self.manager.get_source_metrics(source_name)
        assert metrics.avg_response_time == 2.0
        assert metrics.total_requests == 1
        assert metrics.consecutive_failures == 0
        assert metrics.last_success_time is not None
        assert metrics.circuit_breaker_open is False

        # Second success (test exponential moving average)
        self.manager.update_source_performance(source_name, 4.0, True)

        # avg = 0.3 * 4.0 + 0.7 * 2.0 = 1.2 + 1.4 = 2.6
        assert metrics.avg_response_time == pytest.approx(2.6, rel=1e-2)
        assert metrics.total_requests == 2

    def test_update_source_performance_failure(self):
        """Test updating performance metrics for failed operations."""
        source_name = "fail_source"

        # Record failure
        self.manager.update_source_performance(source_name, 1.0, False)

        metrics = self.manager.get_source_metrics(source_name)
        assert metrics.error_count == 1
        assert metrics.consecutive_failures == 1
        assert metrics.success_rate < 1.0  # Should decrease
        assert metrics.total_requests == 1

    def test_update_source_performance_recovery(self):
        """Test performance metrics recovery after failures."""
        source_name = "recover_source"

        # Record failure then success
        self.manager.update_source_performance(source_name, 1.0, False)
        self.manager.update_source_performance(source_name, 2.0, True)

        metrics = self.manager.get_source_metrics(source_name)
        assert metrics.consecutive_failures == 0  # Reset on success
        assert metrics.avg_response_time == 2.0
        assert metrics.circuit_breaker_open is False

    def test_calculate_optimal_concurrency_no_data(self):
        """Test concurrency calculation with no performance data."""
        # Should return current concurrency when no data
        optimal = self.manager.calculate_optimal_concurrency()
        assert optimal == self.manager.current_concurrency

    def test_calculate_optimal_concurrency_good_performance(self):
        """Test concurrency increase with good performance."""
        # Add good response times
        self.manager.recent_response_times = [0.5, 0.8, 1.0, 1.2]  # Under 2s baseline

        # Set adjustment time to past to allow adjustment
        self.manager.last_adjustment_time = time.time() - 15.0

        original_concurrency = self.manager.current_concurrency
        optimal = self.manager.calculate_optimal_concurrency()

        # Should potentially increase concurrency with good performance
        assert optimal >= original_concurrency

    def test_calculate_optimal_concurrency_poor_performance(self):
        """Test concurrency decrease with poor performance."""
        # Add poor response times
        self.manager.recent_response_times = [
            5.0,
            6.0,
            7.0,
            8.0,
        ]  # Over 4s (2x baseline)

        # Set adjustment time to past
        self.manager.last_adjustment_time = time.time() - 15.0

        original_concurrency = self.manager.current_concurrency
        optimal = self.manager.calculate_optimal_concurrency()

        # Should decrease concurrency with poor performance
        assert optimal <= original_concurrency

    def test_calculate_source_timeout_default(self):
        """Test timeout calculation for new sources."""
        timeout = self.manager.calculate_source_timeout("new_source")
        assert timeout == 30.0  # Default base timeout

    def test_calculate_source_timeout_adaptive(self):
        """Test adaptive timeout calculation based on performance."""
        source_name = "adaptive_source"

        # Update with some performance data
        self.manager.update_source_performance(source_name, 3.0, True)
        self.manager.update_source_performance(source_name, 4.0, True)
        self.manager.update_source_performance(source_name, 5.0, True)

        timeout = self.manager.calculate_source_timeout(source_name)

        # Should be adaptive: avg_response_time * multiplier + buffer
        # Expect around 4.0 * 3.0 + 5.0 = 17.0 (for high success rate)
        assert 15.0 < timeout < 25.0

    def test_calculate_source_timeout_bounds(self):
        """Test timeout calculation stays within bounds."""
        source_name = "bounds_source"

        # Set very high response time
        metrics = self.manager.get_source_metrics(source_name)
        metrics.avg_response_time = 100.0
        metrics.total_requests = 5
        metrics.success_rate = 0.9

        timeout = self.manager.calculate_source_timeout(source_name)

        # Should be clamped to max 60.0
        assert timeout <= 60.0

    @pytest.mark.asyncio
    async def test_execute_parallel_search_success(self):
        """Test successful parallel search execution."""

        # Create mock search functions
        async def mock_search_1(query):
            await asyncio.sleep(0.1)
            return [{"title": f"Result 1 for {query}"}]

        async def mock_search_2(query):
            await asyncio.sleep(0.1)
            return [{"title": f"Result 2 for {query}"}]

        search_tasks = [
            ("source1", mock_search_1, "test query"),
            ("source2", mock_search_2, "test query"),
        ]

        results = await self.manager.execute_parallel_search(search_tasks)

        assert len(results) == 2
        for source_name, result_list, success in results:
            assert success is True
            assert len(result_list) == 1
            assert source_name in ["source1", "source2"]

    @pytest.mark.asyncio
    async def test_execute_parallel_search_with_failure(self):
        """Test parallel search with some failures."""

        async def mock_search_success(query):
            await asyncio.sleep(0.05)
            return [{"title": f"Success result for {query}"}]

        async def mock_search_failure(query):
            raise Exception("Search failed")

        search_tasks = [
            ("success_source", mock_search_success, "test query"),
            ("failure_source", mock_search_failure, "test query"),
        ]

        results = await self.manager.execute_parallel_search(search_tasks)

        assert len(results) == 2

        # Check that we have one success and one failure
        success_count = sum(1 for _, _, success in results if success)
        failure_count = sum(1 for _, _, success in results if not success)

        assert success_count == 1
        assert failure_count == 1

    @pytest.mark.asyncio
    async def test_execute_parallel_search_circuit_breaker_filtering(self):
        """Test that sources with open circuit breakers are filtered out."""
        # Open circuit breaker for one source
        for _ in range(self.manager.circuit_breaker_threshold):
            self.manager.update_source_performance("blocked_source", 1.0, False)

        async def mock_search(query):
            return [{"title": f"Result for {query}"}]

        search_tasks = [
            ("active_source", mock_search, "test query"),
            ("blocked_source", mock_search, "test query"),
        ]

        results = await self.manager.execute_parallel_search(search_tasks)

        # Should only get results from active_source
        assert len(results) == 1
        assert results[0][0] == "active_source"

    @pytest.mark.asyncio
    async def test_execute_parallel_search_timeout(self):
        """Test search timeout handling."""

        async def slow_search(query):
            await asyncio.sleep(100)  # Very slow search
            return [{"title": "Should not reach here"}]

        # Set very short timeout for testing
        source_name = "slow_source"
        metrics = self.manager.get_source_metrics(source_name)
        metrics.avg_response_time = 0.1  # This will result in low timeout
        metrics.total_requests = 5

        search_tasks = [(source_name, slow_search, "test query")]

        results = await self.manager.execute_parallel_search(search_tasks)

        # Should get failure result due to timeout
        assert len(results) == 1
        assert results[0][2] is False  # success = False

    @pytest.mark.asyncio
    async def test_execute_parallel_search_progress_callback(self):
        """Test progress callback functionality."""
        callback_calls = []

        async def progress_callback(source_name, result_count, success):
            callback_calls.append((source_name, result_count, success))

        async def mock_search(query):
            return [{"title": f"Result for {query}"}]

        search_tasks = [("test_source", mock_search, "test query")]

        results = await self.manager.execute_parallel_search(
            search_tasks, progress_callback
        )

        assert len(results) == 1
        assert len(callback_calls) == 1
        assert callback_calls[0] == ("test_source", 1, True)

    def test_get_performance_summary(self):
        """Test performance summary generation."""
        # Add some test data
        self.manager.update_source_performance("source1", 2.0, True)
        self.manager.update_source_performance("source2", 1.0, False)
        self.manager.update_source_performance(
            "source2", 1.0, False
        )  # Open circuit breaker

        summary = self.manager.get_performance_summary()

        assert "current_concurrency" in summary
        assert "active_sources" in summary
        assert "circuit_breaker_sources" in summary
        assert "source_metrics" in summary

        assert "source1" in summary["active_sources"]
        assert "source2" in summary["circuit_breaker_sources"]

        assert summary["current_concurrency"] == self.manager.current_concurrency
        assert len(summary["source_metrics"]) == 2

    def test_performance_window_limit(self):
        """Test that recent response times are limited by performance window."""
        # Add more response times than the window allows
        window_size = self.manager.performance_window
        for i in range(window_size + 10):
            self.manager.update_source_performance("test_source", float(i), True)

        # Should not exceed window size
        assert len(self.manager.recent_response_times) == window_size

    def test_smooth_concurrency_adjustment(self):
        """Test that concurrency adjustments are smooth (incremental)."""
        # Setup for adjustment
        self.manager.recent_response_times = [0.5] * 50  # Good performance
        self.manager.last_adjustment_time = time.time() - 15.0
        original = self.manager.current_concurrency

        # Should only adjust by 1 step at a time
        optimal = self.manager.calculate_optimal_concurrency()
        assert abs(optimal - original) <= 1


class TestGlobalAdaptiveConcurrencyManager:
    """Test suite for global adaptive concurrency manager instance."""

    def test_global_instance_exists(self):
        """Test that global instance exists and is properly configured."""
        assert adaptive_concurrency_manager is not None
        assert isinstance(adaptive_concurrency_manager, AdaptiveConcurrencyManager)

        # Check default configuration
        assert adaptive_concurrency_manager.base_concurrency == 5
        assert adaptive_concurrency_manager.max_concurrency == 15
        assert adaptive_concurrency_manager.min_concurrency == 2

    @pytest.mark.asyncio
    async def test_global_instance_usage(self):
        """Test using the global instance for searches."""

        async def mock_search(query):
            await asyncio.sleep(0.01)
            return [{"title": f"Global result for {query}"}]

        search_tasks = [("global_source", mock_search, "test query")]

        results = await adaptive_concurrency_manager.execute_parallel_search(
            search_tasks
        )

        assert len(results) == 1
        assert results[0][2] is True  # success = True


class TestAdaptiveConcurrencyEdgeCases:
    """Test suite for edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = AdaptiveConcurrencyManager(
            base_concurrency=2, circuit_breaker_threshold=1  # Low threshold for testing
        )

    @pytest.mark.asyncio
    async def test_empty_search_tasks(self):
        """Test handling of empty search task list."""
        results = await self.manager.execute_parallel_search([])
        assert results == []

    @pytest.mark.asyncio
    async def test_all_sources_circuit_breaker_open(self):
        """Test behavior when all sources have open circuit breakers."""
        # Open circuit breakers for both sources
        self.manager.update_source_performance("source1", 1.0, False)
        self.manager.update_source_performance("source2", 1.0, False)

        async def mock_search(query):
            return [{"title": "Should not be called"}]

        search_tasks = [
            ("source1", mock_search, "test query"),
            ("source2", mock_search, "test query"),
        ]

        results = await self.manager.execute_parallel_search(search_tasks)
        assert results == []

    def test_concurrent_metrics_updates(self):
        """Test handling of concurrent metrics updates."""
        source_name = "concurrent_source"

        # Simulate rapid concurrent updates
        for i in range(100):
            success = i % 2 == 0  # Alternate success/failure
            self.manager.update_source_performance(source_name, 1.0 + i * 0.01, success)

        metrics = self.manager.get_source_metrics(source_name)
        assert metrics.total_requests == 100
        assert 0 <= metrics.success_rate <= 1.0
        assert metrics.avg_response_time > 0

    def test_extreme_response_times(self):
        """Test handling of extreme response times."""
        source_name = "extreme_source"

        # Test very small response time
        self.manager.update_source_performance(source_name, 0.001, True)
        timeout = self.manager.calculate_source_timeout(source_name)
        assert timeout >= 10.0  # Should be at least minimum

        # Test very large response time
        metrics = self.manager.get_source_metrics(source_name)
        metrics.avg_response_time = 1000.0
        metrics.total_requests = 5

        timeout = self.manager.calculate_source_timeout(source_name)
        assert timeout <= 60.0  # Should be at most maximum
