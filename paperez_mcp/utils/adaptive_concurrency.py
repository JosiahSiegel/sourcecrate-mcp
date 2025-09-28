"""
Adaptive concurrency control for optimized parallel search.
Dynamically adjusts concurrency levels based on system performance and source behavior.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourcePerformanceMetrics:
    """Performance metrics for a search source."""

    name: str
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    total_requests: int = 0
    consecutive_failures: int = 0
    last_success_time: float | None = None
    circuit_breaker_open: bool = False
    circuit_breaker_open_time: float | None = None


class AdaptiveConcurrencyManager:
    """
    Manages adaptive concurrency for parallel search operations.

    Features:
    - Dynamic concurrency adjustment based on system performance
    - Circuit breaker pattern for failing sources
    - Response time-based timeout adjustment
    - Intelligent batching and load balancing
    """

    def __init__(
        self,
        base_concurrency: int = 5,
        max_concurrency: int = 15,
        min_concurrency: int = 2,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_timeout: float = 60.0,
        performance_window: int = 100,
    ):
        self.base_concurrency = base_concurrency
        self.max_concurrency = max_concurrency
        self.min_concurrency = min_concurrency
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.performance_window = performance_window

        # Track source performance
        self.source_metrics: dict[str, SourcePerformanceMetrics] = {}

        # System-wide metrics
        self.system_load_factor = 1.0
        self.recent_response_times: list[float] = []
        self.active_requests = 0

        # Adaptive parameters
        self.current_concurrency = base_concurrency
        self.last_adjustment_time = time.time()

        logger.info(
            f"🚀 Adaptive concurrency manager initialized: "
            f"base={base_concurrency}, max={max_concurrency}, min={min_concurrency}"
        )

    def get_source_metrics(self, source_name: str) -> SourcePerformanceMetrics:
        """Get or create performance metrics for a source."""
        if source_name not in self.source_metrics:
            self.source_metrics[source_name] = SourcePerformanceMetrics(
                name=source_name
            )
        return self.source_metrics[source_name]

    def is_circuit_breaker_open(self, source_name: str) -> bool:
        """Check if circuit breaker is open for a source."""
        metrics = self.get_source_metrics(source_name)

        if not metrics.circuit_breaker_open:
            return False

        # Check if timeout has expired
        if (
            metrics.circuit_breaker_open_time
            and time.time() - metrics.circuit_breaker_open_time
            > self.circuit_breaker_timeout
        ):
            logger.info(
                f"🔄 Circuit breaker timeout expired for {source_name}, reopening"
            )
            metrics.circuit_breaker_open = False
            metrics.consecutive_failures = 0
            return False

        return True

    def update_source_performance(
        self, source_name: str, response_time: float, success: bool
    ) -> None:
        """Update performance metrics for a source."""
        metrics = self.get_source_metrics(source_name)
        metrics.total_requests += 1

        if success:
            # Update success metrics
            if metrics.avg_response_time == 0:
                metrics.avg_response_time = response_time
            else:
                # Exponential moving average
                alpha = 0.3
                metrics.avg_response_time = (
                    alpha * response_time + (1 - alpha) * metrics.avg_response_time
                )

            metrics.consecutive_failures = 0
            metrics.last_success_time = time.time()
            metrics.circuit_breaker_open = False

            # Update success rate
            metrics.success_rate = metrics.success_rate * 0.9 + 0.1  # Smooth increase

        else:
            # Handle failure
            metrics.error_count += 1
            metrics.consecutive_failures += 1
            metrics.success_rate = metrics.success_rate * 0.8  # Faster decrease

            # Check circuit breaker threshold
            if metrics.consecutive_failures >= self.circuit_breaker_threshold:
                logger.warning(
                    f"🚨 Circuit breaker triggered for {source_name} "
                    f"({metrics.consecutive_failures} consecutive failures)"
                )
                metrics.circuit_breaker_open = True
                metrics.circuit_breaker_open_time = time.time()

        # Update system-wide response times for adaptive adjustment
        self.recent_response_times.append(response_time)
        if len(self.recent_response_times) > self.performance_window:
            self.recent_response_times.pop(0)

    def calculate_optimal_concurrency(self) -> int:
        """Calculate optimal concurrency based on current performance."""
        current_time = time.time()

        # Don't adjust too frequently
        if current_time - self.last_adjustment_time < 10.0:
            return self.current_concurrency

        # Calculate system performance indicators
        active_sources = len(
            [
                m
                for m in self.source_metrics.values()
                if not m.circuit_breaker_open and m.success_rate > 0.5
            ]
        )

        if not self.recent_response_times:
            return self.current_concurrency

        avg_response_time = sum(self.recent_response_times) / len(
            self.recent_response_times
        )

        # Calculate load factor based on response times
        baseline_response_time = 2.0  # 2 seconds baseline
        if avg_response_time < baseline_response_time:
            # System performing well, can increase concurrency
            load_factor = 0.7
        elif avg_response_time < baseline_response_time * 2:
            # Normal performance
            load_factor = 1.0
        else:
            # High response times, reduce concurrency
            load_factor = 1.5

        # Adjust concurrency based on performance
        target_concurrency = int(self.base_concurrency / load_factor)

        # Consider number of healthy sources
        max_useful_concurrency = min(active_sources + 2, self.max_concurrency)
        target_concurrency = min(target_concurrency, max_useful_concurrency)
        target_concurrency = max(target_concurrency, self.min_concurrency)

        # Smooth adjustment
        if target_concurrency != self.current_concurrency:
            if target_concurrency > self.current_concurrency:
                self.current_concurrency = min(
                    self.current_concurrency + 1, target_concurrency
                )
            else:
                self.current_concurrency = max(
                    self.current_concurrency - 1, target_concurrency
                )

            logger.info(
                f"📊 Adjusted concurrency to {self.current_concurrency} "
                f"(target: {target_concurrency}, avg_rt: {avg_response_time:.2f}s, "
                f"active_sources: {active_sources})"
            )

            self.last_adjustment_time = current_time

        return self.current_concurrency

    def calculate_source_timeout(self, source_name: str) -> float:
        """Calculate adaptive timeout for a source based on its performance."""
        metrics = self.get_source_metrics(source_name)

        base_timeout = 30.0

        if metrics.avg_response_time == 0 or metrics.total_requests < 3:
            return base_timeout

        # Adaptive timeout based on average response time
        # Timeout = avg_response_time * multiplier + buffer
        multiplier = 3.0 if metrics.success_rate > 0.8 else 2.0
        buffer = 5.0

        adaptive_timeout = metrics.avg_response_time * multiplier + buffer

        # Clamp to reasonable bounds
        adaptive_timeout = max(10.0, min(60.0, adaptive_timeout))

        return adaptive_timeout

    async def execute_parallel_search(
        self,
        search_tasks: list[tuple[str, Any, Any]],  # (source_name, search_func, args)
        progress_callback: Any | None = None,
    ) -> list[tuple[str, list[Any], bool]]:
        """
        Execute parallel search with adaptive concurrency control.

        Args:
            search_tasks: List of (source_name, search_func, args) tuples
            progress_callback: Optional callback for progress updates

        Returns:
            List of (source_name, results, success) tuples
        """
        optimal_concurrency = self.calculate_optimal_concurrency()

        # Filter out sources with open circuit breakers
        available_tasks = [
            task for task in search_tasks if not self.is_circuit_breaker_open(task[0])
        ]

        if len(available_tasks) < len(search_tasks):
            filtered_count = len(search_tasks) - len(available_tasks)
            logger.info(
                f"🚨 Filtered out {filtered_count} sources due to circuit breakers"
            )

        if not available_tasks:
            logger.warning(
                "❌ No available sources for search (all circuit breakers open)"
            )
            return []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(optimal_concurrency)
        results = []

        async def execute_with_metrics(
            source_name: str, search_func: Any, args: Any
        ) -> tuple[str, list[Any], bool]:
            """Execute search with performance tracking."""
            async with semaphore:
                self.active_requests += 1
                start_time = time.time()

                try:
                    timeout = self.calculate_source_timeout(source_name)

                    logger.debug(
                        f"🔍 Executing {source_name} (timeout: {timeout:.1f}s, "
                        f"active: {self.active_requests})"
                    )

                    # Execute search with timeout
                    try:
                        if isinstance(args, tuple):
                            search_result = await asyncio.wait_for(
                                search_func(*args), timeout=timeout
                            )
                        else:
                            search_result = await asyncio.wait_for(
                                search_func(args), timeout=timeout
                            )
                    except TimeoutError as e:
                        raise Exception(f"Search timeout after {timeout:.1f}s") from e

                    response_time = time.time() - start_time

                    # Update performance metrics
                    self.update_source_performance(source_name, response_time, True)

                    # Call progress callback if provided
                    if progress_callback:
                        await progress_callback(source_name, len(search_result), True)

                    return source_name, search_result, True

                except Exception as e:
                    response_time = time.time() - start_time
                    self.update_source_performance(source_name, response_time, False)

                    logger.warning(f"❌ Search failed for {source_name}: {e}")

                    if progress_callback:
                        await progress_callback(source_name, 0, False)

                    return source_name, [], False

                finally:
                    self.active_requests -= 1

        # Execute all tasks with adaptive concurrency
        logger.info(
            f"🚀 Starting adaptive parallel search: {len(available_tasks)} sources, "
            f"concurrency: {optimal_concurrency}"
        )

        # Create tasks for all available sources
        tasks = [
            execute_with_metrics(source_name, search_func, args)
            for source_name, search_func, args in available_tasks
        ]

        # Execute with error handling
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle exceptions
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"🔥 Parallel search exception: {result}")
                    continue

                if isinstance(result, tuple) and len(result) == 3:
                    processed_results.append(result)
                else:
                    logger.warning(f"⚠️ Invalid result format: {result}")

            successful_count = sum(1 for _, _, success in processed_results if success)
            total_results = sum(len(results) for _, results, _ in processed_results)

            logger.info(
                f"🎯 Adaptive parallel search complete: "
                f"{successful_count}/{len(available_tasks)} sources successful, "
                f"{total_results} total results"
            )

            return processed_results

        except Exception as e:
            logger.error(f"🚨 Critical error in parallel search: {e}")
            return []

    def get_performance_summary(self) -> dict[str, Any]:
        """Get a summary of current performance metrics."""
        active_sources = [
            name
            for name, metrics in self.source_metrics.items()
            if not metrics.circuit_breaker_open
        ]

        circuit_breaker_sources = [
            name
            for name, metrics in self.source_metrics.items()
            if metrics.circuit_breaker_open
        ]

        avg_response_time = (
            sum(self.recent_response_times) / len(self.recent_response_times)
            if self.recent_response_times
            else 0.0
        )

        return {
            "current_concurrency": self.current_concurrency,
            "active_sources": active_sources,
            "circuit_breaker_sources": circuit_breaker_sources,
            "avg_response_time": avg_response_time,
            "active_requests": self.active_requests,
            "source_metrics": {
                name: {
                    "avg_response_time": metrics.avg_response_time,
                    "success_rate": metrics.success_rate,
                    "total_requests": metrics.total_requests,
                    "consecutive_failures": metrics.consecutive_failures,
                }
                for name, metrics in self.source_metrics.items()
            },
        }


# Global instance for reuse across searches
adaptive_concurrency_manager = AdaptiveConcurrencyManager()
