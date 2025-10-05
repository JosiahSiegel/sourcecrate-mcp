"""
Unit tests for result streaming functionality.
Tests streaming search results, progress updates, and early delivery.
"""

import asyncio
import time
from typing import Any

import pytest

from source_crate.utils.result_streaming import (
    ResultStreamer,
    StreamedResult,
    StreamingUpdate,
    create_streaming_search,
    result_streamer,
)


class TestStreamedResult:
    """Test suite for StreamedResult class."""

    def test_streamed_result_creation(self) -> None:
        """Test creation of StreamedResult with required fields."""
        timestamp = time.time()
        result = StreamedResult(
            source="test_source", data={"title": "Test Paper"}, timestamp=timestamp
        )

        assert result.source == "test_source"
        assert result.data == {"title": "Test Paper"}
        assert result.timestamp == timestamp
        assert result.confidence_score == 0.0  # Default value
        assert result.is_final is False  # Default value

    def test_streamed_result_with_confidence(self) -> None:
        """Test StreamedResult with custom confidence score."""
        result = StreamedResult(
            source="test_source",
            data={"title": "Test Paper"},
            timestamp=time.time(),
            confidence_score=0.8,
            is_final=True,
        )

        assert result.confidence_score == 0.8
        assert result.is_final is True


class TestStreamingUpdate:
    """Test suite for StreamingUpdate class."""

    def test_streaming_update_creation(self) -> None:
        """Test creation of StreamingUpdate with different types."""
        # Result update
        result_update = StreamingUpdate(
            type="result",
            source="test_source",
            results=[StreamedResult("test", {"title": "Test"}, time.time())],
        )

        assert result_update.type == "result"
        assert result_update.source == "test_source"
        assert result_update.results is not None
        assert len(result_update.results) == 1

        # Progress update
        progress_update = StreamingUpdate(
            type="progress",
            progress={"completed": 2, "total": 5},
            completed_sources=2,
            total_sources=5,
        )

        assert progress_update.type == "progress"
        assert progress_update.progress is not None
        assert progress_update.progress["completed"] == 2
        assert progress_update.completed_sources == 2

    def test_streaming_update_defaults(self) -> None:
        """Test StreamingUpdate default values."""
        update = StreamingUpdate(type="test")

        assert update.type == "test"
        assert update.source is None
        assert update.result is None
        assert update.results is None
        assert update.error is None
        assert update.progress is None
        assert update.total_sources == 0
        assert update.completed_sources == 0


class TestResultStreamer:
    """Test suite for ResultStreamer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset global state for test isolation
        result_streamer.reset_streaming_state()

        self.streamer = ResultStreamer(
            enable_early_results=True,
            min_results_for_early_delivery=2,
            max_wait_time=10.0,
            result_buffer_size=10,
        )

    def test_streamer_initialization(self) -> None:
        """Test ResultStreamer initialization."""
        assert self.streamer.enable_early_results is True
        assert self.streamer.min_results_for_early_delivery == 2
        assert self.streamer.max_wait_time == 10.0
        assert self.streamer.result_buffer_size == 10

        assert len(self.streamer.completed_sources) == 0
        assert len(self.streamer.error_sources) == 0
        assert len(self.streamer.source_results) == 0

    def test_calculate_confidence_basic(self) -> None:
        """Test basic confidence calculation."""
        # Basic result
        result = {"title": "Test Paper"}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.5  # Base score

    def test_calculate_confidence_with_pdf(self) -> None:
        """Test confidence boost for papers with PDFs."""
        result = {"title": "Test Paper", "pdf_url": "https://example.com/paper.pdf"}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.7  # Base + PDF boost

    def test_calculate_confidence_with_doi(self) -> None:
        """Test confidence boost for papers with DOI."""
        result = {"title": "Test Paper", "doi": "10.1234/example.doi"}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.6  # Base + DOI boost

    def test_calculate_confidence_with_citations(self) -> None:
        """Test confidence boost based on citation count."""
        # High citations
        result = {"title": "Test Paper", "citation_count": 150}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.7  # Base + high citation boost

        # Medium citations
        result["citation_count"] = 25
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.6  # Base + medium citation boost

    def test_calculate_confidence_with_recent_year(self) -> None:
        """Test confidence boost for recent papers."""
        result = {"title": "Test Paper", "year": 2024}  # Recent year
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.6  # Base + recent year boost

    def test_calculate_confidence_max_score(self) -> None:
        """Test that confidence score is capped at 1.0."""
        result = {
            "title": "Test Paper",
            "pdf_url": "https://example.com/paper.pdf",
            "open_access_pdf": "https://example.com/oa.pdf",
            "doi": "10.1234/example.doi",
            "citation_count": 200,
            "year": 2024,
        }
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 1.0  # Should be capped

    def test_should_deliver_early_results_by_count(self) -> None:
        """Test early delivery trigger by result count."""
        # Add enough results to trigger early delivery
        self.streamer.source_results = {
            "source1": [
                StreamedResult("source1", {"title": "Paper 1"}, time.time()),
                StreamedResult("source1", {"title": "Paper 2"}, time.time()),
            ]
        }

        assert self.streamer._should_deliver_early_results() is True

    def test_should_deliver_early_results_by_time(self) -> None:
        """Test early delivery trigger by elapsed time."""
        # Set start time to past to simulate elapsed time
        self.streamer.start_time = time.time() - 5.0  # 5 seconds ago

        assert self.streamer._should_deliver_early_results() is True

    def test_should_deliver_early_results_by_sources(self) -> None:
        """Test early delivery trigger by completed sources."""
        # Add completed sources
        self.streamer.completed_sources.add("source1")
        self.streamer.completed_sources.add("source2")

        assert self.streamer._should_deliver_early_results() is True

    def test_get_best_results_so_far(self) -> None:
        """Test getting best results for early delivery."""
        # Add results with different confidence scores
        high_conf_result = StreamedResult(
            "source1", {"title": "High Confidence", "citation_count": 100}, time.time()
        )
        high_conf_result.confidence_score = 0.8

        low_conf_result = StreamedResult(
            "source2", {"title": "Low Confidence"}, time.time()
        )
        low_conf_result.confidence_score = 0.3

        self.streamer.source_results = {
            "source1": [high_conf_result],
            "source2": [low_conf_result],
        }

        delivered_results: set[tuple[str, int]] = set()
        best_results = self.streamer._get_best_results_so_far(delivered_results)

        assert len(best_results) == 2
        assert best_results[0].confidence_score >= best_results[1].confidence_score

    def test_get_final_results_deduplication(self) -> None:
        """Test final results with deduplication."""
        # Add duplicate results by DOI
        result1 = StreamedResult(
            "source1", {"title": "Paper A", "doi": "10.1234/same.doi"}, time.time()
        )
        result2 = StreamedResult(
            "source2",
            {"title": "Paper A (duplicate)", "doi": "10.1234/same.doi"},
            time.time(),
        )

        self.streamer.source_results = {"source1": [result1], "source2": [result2]}

        delivered_results: set[tuple[str, int]] = set()
        final_results = self.streamer._get_final_results(delivered_results)

        # Should only have one result after deduplication
        assert len(final_results) == 1
        assert final_results[0].is_final is True

    def test_get_final_results_by_title(self) -> None:
        """Test deduplication by title when no DOI."""
        result1 = StreamedResult(
            "source1", {"title": "Unique Paper Title"}, time.time()
        )
        result2 = StreamedResult(
            "source2",
            {"title": "unique paper title"},  # Same title, different case
            time.time(),
        )

        self.streamer.source_results = {"source1": [result1], "source2": [result2]}

        delivered_results: set[tuple[str, int]] = set()
        final_results = self.streamer._get_final_results(delivered_results)

        # Should only have one result after title-based deduplication
        assert len(final_results) == 1

    def test_get_streaming_stats(self) -> None:
        """Test streaming statistics generation."""
        self.streamer.start_time = time.time() - 5.0  # 5 seconds ago
        self.streamer.first_result_time = self.streamer.start_time + 2.0
        self.streamer.streaming_stats["total_results"] = 10

        stats = self.streamer.get_streaming_stats()

        assert "elapsed_time" in stats
        assert "first_result_latency" in stats
        assert "results_per_second" in stats
        assert stats["total_results"] == 10
        assert stats["elapsed_time"] >= 5.0
        assert stats["first_result_latency"] == pytest.approx(2.0, rel=1e-1)

    @pytest.mark.asyncio
    async def test_stream_search_results_basic(self) -> None:
        """Test basic streaming functionality."""

        async def mock_search_1() -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return [{"title": "Result 1"}]

        async def mock_search_2() -> list[dict[str, Any]]:
            await asyncio.sleep(0.2)
            return [{"title": "Result 2"}]

        search_tasks = [mock_search_1, mock_search_2]
        source_names = ["source1", "source2"]

        updates = []
        async for update in self.streamer.stream_search_results(
            search_tasks, source_names
        ):
            updates.append(update)

        # Should have source completion updates and final update
        assert len(updates) >= 3  # At least 2 completions + 1 final

        # Check for final update
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1

        final_update = final_updates[0]
        assert final_update.results is not None
        assert len(final_update.results) == 2

    @pytest.mark.asyncio
    async def test_stream_search_results_with_failure(self) -> None:
        """Test streaming with some source failures."""

        async def mock_search_success() -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return [{"title": "Success Result"}]

        async def mock_search_failure() -> list[dict[str, Any]]:
            raise Exception("Search failed")

        search_tasks = [mock_search_success, mock_search_failure]
        source_names = ["success_source", "failure_source"]

        updates = []
        async for update in self.streamer.stream_search_results(
            search_tasks, source_names
        ):
            updates.append(update)

        # Should have error updates
        error_updates = [u for u in updates if u.type == "error"]
        assert len(error_updates) == 1
        assert error_updates[0].source == "failure_source"

        # Should still have final results from successful source
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1
        assert len(final_updates[0].results) == 1

    @pytest.mark.asyncio
    async def test_stream_search_results_early_delivery(self) -> None:
        """Test early result delivery functionality."""
        # Configure for immediate early delivery
        early_streamer = ResultStreamer(
            enable_early_results=True,
            min_results_for_early_delivery=1,
            max_wait_time=1.0,
        )

        async def fast_search() -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)
            return [{"title": "Fast Result"}]

        async def slow_search() -> list[dict[str, Any]]:
            await asyncio.sleep(0.5)
            return [{"title": "Slow Result"}]

        search_tasks = [fast_search, slow_search]
        source_names = ["fast_source", "slow_source"]

        updates = []
        async for update in early_streamer.stream_search_results(
            search_tasks, source_names
        ):
            updates.append(update)

        # Should have early result delivery
        result_updates = [u for u in updates if u.type == "result"]
        assert len(result_updates) >= 1  # At least early delivery

        # Should have final results
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1

    @pytest.mark.asyncio
    async def test_stream_search_results_with_processor(self) -> None:
        """Test streaming with result processor."""

        async def mock_search() -> list[dict[str, Any]]:
            return [{"title": "Original Title"}]

        async def result_processor(streamed_result: StreamedResult) -> StreamedResult:
            # Modify the result
            streamed_result.data["title"] = (
                "Processed: " + streamed_result.data["title"]
            )
            return streamed_result

        search_tasks = [mock_search]
        source_names = ["test_source"]

        updates = []
        async for update in self.streamer.stream_search_results(
            search_tasks, source_names, result_processor
        ):
            updates.append(update)

        # Check that results were processed
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1
        assert "Processed:" in final_updates[0].results[0].data["title"]

    @pytest.mark.asyncio
    async def test_stream_search_results_processor_failure(self) -> None:
        """Test handling of result processor failures."""

        async def mock_search() -> list[dict[str, Any]]:
            return [{"title": "Test Title"}]

        async def failing_processor(streamed_result: StreamedResult) -> StreamedResult:
            raise Exception("Processor failed")

        search_tasks = [mock_search]
        source_names = ["test_source"]

        updates = []
        async for update in self.streamer.stream_search_results(
            search_tasks, source_names, failing_processor
        ):
            updates.append(update)

        # Should still get results despite processor failure
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1
        assert len(final_updates[0].results) == 1


class TestGlobalResultStreamer:
    """Test suite for global result streamer instance."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset global state for test isolation
        result_streamer.reset_streaming_state()

    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly configured."""
        assert result_streamer is not None
        assert isinstance(result_streamer, ResultStreamer)

        # Check default configuration
        assert result_streamer.enable_early_results is True
        assert result_streamer.min_results_for_early_delivery == 3
        assert result_streamer.max_wait_time == 30.0

    @pytest.mark.asyncio
    async def test_global_instance_usage(self) -> None:
        """Test using the global instance for streaming."""

        async def mock_search() -> list[dict[str, Any]]:
            await asyncio.sleep(0.01)
            return [{"title": "Global test result"}]

        search_tasks = [mock_search]
        source_names = ["global_source"]

        updates = []
        async for update in result_streamer.stream_search_results(
            search_tasks, source_names
        ):
            updates.append(update)
            break  # Just get first update to test functionality

        assert len(updates) >= 1


class TestCreateStreamingSearch:
    """Test suite for create_streaming_search function."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset global state for test isolation
        result_streamer.reset_streaming_state()

    @pytest.mark.asyncio
    async def test_create_streaming_search_basic(self) -> None:
        """Test basic streaming search creation."""

        async def mock_search_func(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)
            return [{"title": f"Result for {query}"}]

        search_functions = {"source1": mock_search_func, "source2": mock_search_func}
        api_status = {"source1": True, "source2": True}

        updates = []
        async for update in create_streaming_search(
            search_functions, "test query", 10, api_status
        ):
            updates.append(update)

        # Should have updates from streaming search
        assert len(updates) >= 2  # At least some updates

        # Should have final results
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1

    @pytest.mark.asyncio
    async def test_create_streaming_search_filtered_sources(self) -> None:
        """Test streaming search with filtered sources."""

        async def mock_search_func(query: str, limit: int) -> list[dict[str, Any]]:
            return [{"title": f"Result for {query}"}]

        search_functions = {
            "available_source": mock_search_func,
            "unavailable_source": mock_search_func,
        }
        api_status = {"available_source": True, "unavailable_source": False}

        updates = []
        async for update in create_streaming_search(
            search_functions, "test query", 10, api_status
        ):
            updates.append(update)

        # Should only process available source
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1
        # Should only have results from one source
        assert len(final_updates[0].results) == 1

    @pytest.mark.asyncio
    async def test_create_streaming_search_result_processing(self) -> None:
        """Test that results are processed with streaming metadata."""

        async def mock_search_func(query: str, limit: int) -> list[dict[str, Any]]:
            return [{"title": "Test Result"}]

        search_functions = {"test_source": mock_search_func}
        api_status = {"test_source": True}

        updates = []
        async for update in create_streaming_search(
            search_functions, "test query", 5, api_status
        ):
            updates.append(update)

        # Check that results have streaming metadata
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1

        result = final_updates[0].results[0]
        assert "_streaming_metadata" in result.data
        assert "source" in result.data["_streaming_metadata"]
        assert "timestamp" in result.data["_streaming_metadata"]
        assert "confidence" in result.data["_streaming_metadata"]

    @pytest.mark.asyncio
    async def test_create_streaming_search_no_available_sources(self) -> None:
        """Test streaming search with no available sources."""
        search_functions = {"unavailable_source": lambda q, limit: []}
        api_status = {"unavailable_source": False}

        updates = []
        async for update in create_streaming_search(
            search_functions, "test query", 10, api_status
        ):
            updates.append(update)

        # Should have minimal updates for no sources
        final_updates = [u for u in updates if u.type == "final"]
        if final_updates:
            assert len(final_updates[0].results) == 0


class TestResultStreamingEdgeCases:
    """Test suite for edge cases and error conditions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset global state for test isolation
        result_streamer.reset_streaming_state()

        self.streamer = ResultStreamer(
            enable_early_results=False,  # Disable for simpler testing
            max_wait_time=1.0,  # Short timeout
        )

    @pytest.mark.asyncio
    async def test_empty_search_tasks(self) -> None:
        """Test streaming with empty task list."""
        updates = []
        async for update in self.streamer.stream_search_results([], []):
            updates.append(update)

        # Should get final update with empty results
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1
        assert len(final_updates[0].results) == 0

    @pytest.mark.asyncio
    async def test_all_sources_fail(self) -> None:
        """Test streaming when all sources fail."""

        async def failing_search() -> list[dict[str, Any]]:
            raise Exception("All searches fail")

        search_tasks = [failing_search, failing_search]
        source_names = ["fail1", "fail2"]

        updates = []
        async for update in self.streamer.stream_search_results(
            search_tasks, source_names
        ):
            updates.append(update)

        # Should have error updates for all sources
        error_updates = [u for u in updates if u.type == "error"]
        assert len(error_updates) == 2

        # Should still have final update with no results
        final_updates = [u for u in updates if u.type == "final"]
        assert len(final_updates) == 1
        assert len(final_updates[0].results) == 0

    @pytest.mark.asyncio
    async def test_task_cancellation(self) -> None:
        """Test proper task cancellation on completion."""

        async def slow_search() -> list[dict[str, Any]]:
            await asyncio.sleep(10)  # Very slow
            return []

        search_tasks = [slow_search]
        source_names = ["slow_source"]

        # Start streaming but break early
        async for _update in self.streamer.stream_search_results(
            search_tasks, source_names
        ):
            break  # Exit early

        # Task should be cleaned up properly (no hanging coroutines)
        await asyncio.sleep(0.1)  # Allow cleanup

    def test_confidence_edge_cases(self) -> None:
        """Test confidence calculation with edge cases."""
        # Empty result
        confidence = self.streamer._calculate_confidence({})
        assert confidence == 0.5

        # Invalid citation count
        result = {"citation_count": "invalid"}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.5

        # Invalid year
        result = {"year": "not_a_year"}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.5

        # None values
        result: dict[str, Any] = {"year": None, "citation_count": None}
        confidence = self.streamer._calculate_confidence(result)
        assert confidence == 0.5

    def test_stats_with_no_timing(self) -> None:
        """Test statistics calculation with no timing data."""
        stats = self.streamer.get_streaming_stats()

        assert stats["elapsed_time"] == 0
        assert stats["first_result_latency"] is None
        assert stats["results_per_second"] == 0
