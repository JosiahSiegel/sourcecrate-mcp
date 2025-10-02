"""
Result streaming system for faster search responses.
Provides incremental results as they become available from different sources.
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StreamedResult:
    """A single result with streaming metadata."""

    source: str
    data: dict[str, Any]
    timestamp: float
    confidence_score: float = 0.0
    is_final: bool = False


@dataclass
class StreamingUpdate:
    """An update in the streaming process."""

    type: str  # 'result', 'source_complete', 'error', 'final'
    source: str | None = None
    result: StreamedResult | None = None
    results: list[StreamedResult] | None = None
    error: str | None = None
    progress: dict[str, Any] | None = None
    total_sources: int = 0
    completed_sources: int = 0


class ResultStreamer:
    """
    Manages streaming of search results from multiple sources.

    Features:
    - Incremental result delivery as sources complete
    - Real-time progress updates
    - Early result availability before all sources complete
    - Intelligent result ordering and filtering
    """

    def __init__(
        self,
        enable_early_results: bool = True,
        min_results_for_early_delivery: int = 3,
        max_wait_time: float = 30.0,
        result_buffer_size: int = 50,
    ):
        self.enable_early_results = enable_early_results
        self.min_results_for_early_delivery = min_results_for_early_delivery
        self.max_wait_time = max_wait_time
        self.result_buffer_size = result_buffer_size

        # Streaming state
        self.result_queue: asyncio.Queue = asyncio.Queue(maxsize=result_buffer_size)
        self.completed_sources: set = set()
        self.error_sources: set = set()
        self.source_results: dict[str, list[StreamedResult]] = {}

        # Performance tracking
        self.start_time = 0.0
        self.first_result_time: float | None = None
        self.streaming_stats = {
            "total_results": 0,
            "sources_completed": 0,
            "sources_failed": 0,
            "average_latency": 0.0,
        }

        logger.info(
            f"🌊 Result streamer initialized: early_results={enable_early_results}, "
            f"min_early={min_results_for_early_delivery}, max_wait={max_wait_time}s"
        )

    async def stream_search_results(
        self,
        search_tasks: list[Any],  # List of search coroutines
        source_names: list[str],
        result_processor: Any | None = None,
    ) -> AsyncIterator[StreamingUpdate]:
        """
        Stream search results from multiple sources as they become available.

        Args:
            search_tasks: List of async search functions
            source_names: Names of the sources being searched
            result_processor: Optional function to process/filter results

        Yields:
            StreamingUpdate objects with incremental results and progress
        """
        # CRITICAL: Reset state to prevent cache pollution between searches
        # Without this, results from previous searches leak into new searches
        self.completed_sources.clear()
        self.error_sources.clear()
        self.source_results.clear()
        self.first_result_time = None
        self.streaming_stats = {
            "total_results": 0,
            "sources_completed": 0,
            "sources_failed": 0,
            "average_latency": 0.0,
        }

        self.start_time = time.time()
        total_sources = len(search_tasks)

        logger.info(f"🌊 Starting streaming search across {total_sources} sources")

        # Create a queue for source completion notifications
        completion_queue: asyncio.Queue = asyncio.Queue()

        # Launch all search tasks concurrently
        async def search_wrapper(task: Any, source_name: str) -> None:
            """Wrapper that handles individual source search and queuing results."""
            try:
                logger.debug(f"🔍 Starting search for {source_name}")
                search_start = time.time()

                # Execute the search task
                if callable(task):
                    results = await task()
                else:
                    results = await task

                search_duration = time.time() - search_start

                # Process and queue results
                if results:
                    processed_results = []
                    for _i, result in enumerate(results):
                        streamed_result = StreamedResult(
                            source=source_name,
                            data=result,
                            timestamp=time.time(),
                            confidence_score=self._calculate_confidence(result),
                        )

                        # Apply result processor if provided
                        if result_processor:
                            try:
                                processed_result = await result_processor(
                                    streamed_result
                                )
                                if processed_result:
                                    processed_results.append(processed_result)
                            except Exception as e:
                                logger.warning(
                                    f"Result processor failed for {source_name}: {e}"
                                )
                                processed_results.append(streamed_result)
                        else:
                            processed_results.append(streamed_result)

                    # Store results for this source
                    self.source_results[source_name] = processed_results

                    # Record first result timing
                    if self.first_result_time is None and processed_results:
                        self.first_result_time = time.time()

                    self.streaming_stats["total_results"] += len(processed_results)

                    logger.info(
                        f"✅ {source_name}: {len(processed_results)} results "
                        f"({search_duration:.2f}s)"
                    )
                else:
                    self.source_results[source_name] = []
                    logger.info(
                        f"⚪ {source_name}: No results ({search_duration:.2f}s)"
                    )

                # Mark source as completed
                self.completed_sources.add(source_name)
                self.streaming_stats["sources_completed"] += 1

                # Notify completion
                await completion_queue.put(("completed", source_name, None))

            except Exception as e:
                logger.warning(f"❌ Search failed for {source_name}: {e}")
                self.error_sources.add(source_name)
                self.streaming_stats["sources_failed"] += 1
                await completion_queue.put(("error", source_name, str(e)))

        # Start all search tasks
        search_coroutines = [
            search_wrapper(task, source_name)
            for task, source_name in zip(search_tasks, source_names, strict=False)
        ]

        # Launch all searches concurrently as individual tasks
        individual_tasks = [asyncio.create_task(coro) for coro in search_coroutines]

        # Create a task that gathers all individual tasks
        async def gather_all() -> list[Any]:
            return await asyncio.gather(*individual_tasks, return_exceptions=True)

        search_task: Any = asyncio.create_task(gather_all())

        # Stream results as they become available
        try:
            delivered_results: set[tuple[str, int]] = set()

            while len(self.completed_sources) + len(self.error_sources) < total_sources:
                try:
                    # Wait for source completion with timeout
                    completion_type, source_name, error = await asyncio.wait_for(
                        completion_queue.get(), timeout=1.0
                    )

                    if completion_type == "completed":
                        # Yield source completion update
                        yield StreamingUpdate(
                            type="source_complete",
                            source=source_name,
                            progress={
                                "completed_sources": len(self.completed_sources),
                                "total_sources": total_sources,
                                "elapsed_time": time.time() - self.start_time,
                            },
                            completed_sources=len(self.completed_sources),
                            total_sources=total_sources,
                        )

                        # Progressive delivery: send new results after each source completes
                        if self.enable_early_results and self._should_deliver_early_results():
                            new_results = self._get_best_results_so_far(
                                delivered_results
                            )
                            if new_results:
                                yield StreamingUpdate(
                                    type="result",
                                    results=new_results,
                                    progress={
                                        "type": "progressive_delivery",
                                        "total_results": len(new_results),
                                        "completed_sources": len(
                                            self.completed_sources
                                        ),
                                        "total_sources": total_sources,
                                    },
                                )

                                # Track delivered results to avoid duplicates
                                for result in new_results:
                                    delivered_results.add(
                                        (result.source, id(result.data))
                                    )

                                logger.info(
                                    f"📤 Progressive delivery: {len(new_results)} new results after "
                                    f"{len(self.completed_sources)} sources completed"
                                )

                    elif completion_type == "error":
                        yield StreamingUpdate(
                            type="error",
                            source=source_name,
                            error=error,
                            progress={
                                "completed_sources": len(self.completed_sources),
                                "error_sources": len(self.error_sources),
                                "total_sources": total_sources,
                            },
                        )

                except TimeoutError:
                    # Periodic progress update even if no sources complete
                    if len(self.completed_sources) > 0:
                        yield StreamingUpdate(
                            type="progress",
                            progress={
                                "completed_sources": len(self.completed_sources),
                                "error_sources": len(self.error_sources),
                                "total_sources": total_sources,
                                "elapsed_time": time.time() - self.start_time,
                                "total_results": self.streaming_stats["total_results"],
                            },
                        )

            # Drain any remaining items from completion queue
            # (handles race condition where multiple errors arrive simultaneously)
            try:
                while True:
                    completion_type, source_name, error = completion_queue.get_nowait()

                    if completion_type == "error":
                        yield StreamingUpdate(
                            type="error",
                            source=source_name,
                            error=error,
                            progress={
                                "completed_sources": len(self.completed_sources),
                                "error_sources": len(self.error_sources),
                                "total_sources": total_sources,
                            },
                        )
                    elif completion_type == "completed":
                        yield StreamingUpdate(
                            type="source_complete",
                            source=source_name,
                            progress={
                                "completed_sources": len(self.completed_sources),
                                "total_sources": total_sources,
                                "elapsed_time": time.time() - self.start_time,
                            },
                            completed_sources=len(self.completed_sources),
                            total_sources=total_sources,
                        )
            except asyncio.QueueEmpty:
                # No more items in queue, continue to final results
                pass

            # All sources completed - deliver final results
            final_results = self._get_final_results(delivered_results)

            # Calculate final statistics
            total_time = time.time() - self.start_time
            self.streaming_stats["average_latency"] = total_time / max(
                1, len(self.completed_sources)
            )

            yield StreamingUpdate(
                type="final",
                results=final_results,
                progress={
                    "type": "final",
                    "total_results": len(final_results),
                    "completed_sources": len(self.completed_sources),
                    "error_sources": len(self.error_sources),
                    "total_sources": total_sources,
                    "total_time": total_time,
                    "first_result_time": (
                        self.first_result_time - self.start_time
                        if self.first_result_time
                        else None
                    ),
                    "streaming_stats": self.streaming_stats,
                },
            )

            logger.info(
                f"🎯 Streaming complete: {len(final_results)} final results, "
                f"{len(self.completed_sources)} sources successful, "
                f"{len(self.error_sources)} sources failed, "
                f"total time: {total_time:.2f}s"
            )

        finally:
            # Ensure search task is cleaned up
            if not search_task.done():
                search_task.cancel()
                try:
                    await search_task
                except asyncio.CancelledError:
                    pass

    def _calculate_confidence(self, result: dict[str, Any]) -> float:
        """Calculate confidence score for a result."""
        score = 0.5  # Base score

        # Boost for papers with PDFs
        if result.get("pdf_url") or result.get("open_access_pdf"):
            score += 0.2

        # Boost for papers with DOI
        if result.get("doi"):
            score += 0.1

        # Boost based on citation count
        citations = result.get("citation_count", 0)
        try:
            citations = int(citations) if citations else 0
            if citations > 100:
                score += 0.2
            elif citations > 10:
                score += 0.1
        except (ValueError, TypeError):
            pass

        # Boost for recent papers
        year = result.get("year")
        if year:
            try:
                year = int(year)
                current_year = 2025  # Update based on current year
                if year >= current_year - 2:
                    score += 0.1
            except (ValueError, TypeError):
                pass

        return min(1.0, score)

    def _should_deliver_early_results(self) -> bool:
        """Determine if early results should be delivered."""
        # Check if we have enough results from fast sources
        total_results = sum(len(results) for results in self.source_results.values())

        # Check time-based delivery
        elapsed = time.time() - self.start_time
        time_threshold = min(self.max_wait_time * 0.3, 10.0)  # Max 10 seconds

        return (
            total_results >= self.min_results_for_early_delivery
            or elapsed >= time_threshold
            or len(self.completed_sources) >= 2  # At least 2 sources completed
        )

    def _get_best_results_so_far(self, delivered_results: set) -> list[StreamedResult]:
        """Get the best results available so far, excluding already delivered ones."""
        all_results = []

        for source_name, results in self.source_results.items():
            for result in results:
                result_id = (source_name, id(result.data))
                if result_id not in delivered_results:
                    all_results.append(result)

        # Sort by confidence score and return top results
        all_results.sort(key=lambda x: x.confidence_score, reverse=True)

        # Return up to 10 best results for early delivery
        return all_results[:10]

    def _get_final_results(self, delivered_results: set) -> list[StreamedResult]:
        """Get all final results, removing duplicates with early delivered results."""
        all_results = []

        for _source_name, results in self.source_results.items():
            for result in results:
                result.is_final = True
                all_results.append(result)

        # Sort by confidence score
        all_results.sort(key=lambda x: x.confidence_score, reverse=True)

        # Remove duplicates by DOI/title
        seen_identifiers = set()
        unique_results = []

        for result in all_results:
            # Create identifier from DOI or title
            identifier = (
                result.data.get("doi") or result.data.get("title", "").lower().strip()
            )

            if identifier and identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_results.append(result)

        return unique_results

    def get_streaming_stats(self) -> dict[str, Any]:
        """Get current streaming statistics."""
        elapsed = time.time() - self.start_time if self.start_time > 0 else 0

        return {
            **self.streaming_stats,
            "elapsed_time": elapsed,
            "first_result_latency": (
                self.first_result_time - self.start_time
                if self.first_result_time and self.start_time > 0
                else None
            ),
            "results_per_second": (
                self.streaming_stats["total_results"] / max(0.1, elapsed)
                if elapsed > 0
                else 0
            ),
        }

    def reset_streaming_state(self) -> None:
        """Reset streaming state for test isolation."""
        # Clear streaming state
        self.completed_sources.clear()
        self.error_sources.clear()
        self.source_results.clear()

        # Reset timing
        self.start_time = 0.0
        self.first_result_time = None

        # Reset statistics
        self.streaming_stats = {
            "total_results": 0,
            "sources_completed": 0,
            "sources_failed": 0,
            "average_latency": 0.0,
        }

        # Create new queue to avoid any lingering tasks
        self.result_queue = asyncio.Queue(maxsize=self.result_buffer_size)


# Global streaming instance
result_streamer = ResultStreamer()


async def create_streaming_search(
    search_functions: dict[str, Any],
    query: str,
    limit: int,
    api_status: dict[str, bool],
) -> AsyncIterator[StreamingUpdate]:
    """
    Create a streaming search across multiple sources.

    Args:
        search_functions: Dictionary of search functions by source name
        query: Search query
        limit: Maximum results per source
        api_status: API availability status

    Yields:
        StreamingUpdate objects with incremental results
    """
    # Initialize relevance scorer for query-based ranking
    from ..utils.relevance_scorer import RelevanceScorer

    relevance_scorer = RelevanceScorer()
    logger.info(f"🎯 Relevance scorer initialized for query: '{query}'")

    # Prepare search tasks for available sources
    search_tasks = []
    source_names = []

    for source_name, search_func in search_functions.items():
        if api_status.get(source_name, True) and callable(search_func):
            # Create search task
            async def source_search(
                func: Any = search_func, q: str = query, lim: int = limit
            ) -> Any:
                return await func(q, lim)

            search_tasks.append(source_search)
            source_names.append(source_name)

    logger.info(f"🌊 Created streaming search for {len(search_tasks)} sources")

    # Result processor for filtering and enhancement
    async def process_result(
        streamed_result: StreamedResult,
    ) -> StreamedResult | None:
        """Process individual results for streaming."""
        result = streamed_result.data

        # Calculate relevance score based on query
        relevance_score = relevance_scorer.score_paper_relevance(query, result)

        # Add both streaming metadata and relevance score
        result["_streaming_metadata"] = {
            "source": streamed_result.source,
            "timestamp": streamed_result.timestamp,
            "confidence": streamed_result.confidence_score,
        }
        result["relevance_score"] = relevance_score

        # Update the streamed result's confidence with relevance score
        # This allows sorting by relevance in early results
        streamed_result.confidence_score = relevance_score

        return streamed_result

    # Stream results
    async for update in result_streamer.stream_search_results(
        search_tasks, source_names, process_result
    ):
        yield update
