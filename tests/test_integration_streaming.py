"""
Integration tests for streaming functionality.
Tests end-to-end streaming workflows including MCP server integration,
search orchestration, and real-world source interactions.
"""

import asyncio
import time
from typing import Any

import pytest

from source_crate.utils.adaptive_concurrency import AdaptiveConcurrencyManager
from source_crate.utils.fuzzy_matching import FuzzyPaperMatcher

# Import streaming components
from source_crate.utils.result_streaming import (
    ResultStreamer,
    create_streaming_search,
)

# Import global instances for cleanup
from source_crate.utils.search_analytics import search_analytics
from source_crate.utils.result_streaming import result_streamer


class TestStreamingSearchIntegration:
    """Integration tests for the complete streaming search workflow."""

    def setup_method(self) -> None:
        """Set up test fixtures with realistic mock sources."""
        # Reset global state for test isolation
        search_analytics.reset_analytics_state()
        result_streamer.reset_streaming_state()

        self.streamer = ResultStreamer(
            enable_early_results=True,
            min_results_for_early_delivery=2,
            max_wait_time=5.0,
        )
        self.concurrency_manager = AdaptiveConcurrencyManager(
            base_concurrency=3, max_concurrency=8, circuit_breaker_threshold=2
        )
        self.fuzzy_matcher = FuzzyPaperMatcher()

    def create_mock_papers(
        self, source: str, count: int, query: str
    ) -> list[dict[str, Any]]:
        """Create mock academic papers for testing."""
        papers = []
        for i in range(count):
            paper = {
                "title": f"{source} Paper {i+1}: {query} Research",
                "authors": [f"Author {i+1}", f"Coauthor {i+1}"],
                "abstract": f"This paper discusses {query} from the perspective of {source}. "
                f"It presents novel findings and methodologies.",
                "year": 2024 - (i % 3),  # Mix of recent years
                "journal": f"{source} Journal of Advanced Research",
                "url": f"https://{source.lower()}.org/papers/{i+1}",
                "source": source,
                "doi": f"10.{1000 + hash(source) % 9000}/{query.replace(' ', '.')}.{i+1}",
                "citation_count": 50 + (i * 10),
                "pdf_url": (
                    f"https://{source.lower()}.org/pdf/{i+1}.pdf"
                    if i % 2 == 0
                    else None
                ),
                "open_access_pdf": (
                    f"https://oa.{source.lower()}.org/{i+1}.pdf" if i % 3 == 0 else None
                ),
                "_search_relevance": 0.9 - (i * 0.1),
            }
            papers.append(paper)
        return papers

    @pytest.mark.asyncio
    async def test_end_to_end_streaming_workflow(self) -> None:
        """Test complete streaming workflow from query to final results."""
        query = "machine learning"
        limit = 5

        # Mock multiple academic sources with different performance characteristics
        async def fast_source_search(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)  # Fast response
            return self.create_mock_papers("FastSource", 3, q)

        async def medium_source_search(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.3)  # Medium response
            return self.create_mock_papers("MediumSource", 4, q)

        async def slow_source_search(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.8)  # Slower response
            return self.create_mock_papers("SlowSource", 2, q)

        search_functions = {
            "fast_source": fast_source_search,
            "medium_source": medium_source_search,
            "slow_source": slow_source_search,
        }
        api_status = {"fast_source": True, "medium_source": True, "slow_source": True}

        # Collect all streaming updates
        all_updates = []
        source_completions = []
        early_results = []
        final_results = []
        error_count = 0

        async for update in create_streaming_search(
            search_functions, query, limit, api_status
        ):
            all_updates.append(update)

            if update.type == "source_complete":
                source_completions.append(update.source)
            elif update.type == "result":
                if update.progress and update.progress.get("type") == "progressive_delivery":
                    early_results.extend(update.results or [])
                else:
                    # Regular results during streaming
                    pass
            elif update.type == "error":
                error_count += 1
            elif update.type == "final":
                final_results.extend(update.results or [])

        # Verify streaming workflow
        assert len(all_updates) >= 4  # At least 3 completions + 1 final
        assert len(source_completions) == 3  # All sources completed
        assert error_count == 0  # No errors in this test

        # Verify early results were delivered
        assert len(early_results) > 0, "Early results should be delivered"

        # Verify final results contain all papers
        assert (
            len(final_results) >= 5
        ), f"Expected at least 5 results, got {len(final_results)}"

        # Verify results have streaming metadata
        for result in final_results:
            assert "_streaming_metadata" in result.data
            assert "source" in result.data["_streaming_metadata"]
            assert "confidence" in result.data["_streaming_metadata"]

        # Verify source ordering (fast source should complete first)
        first_completed = source_completions[0]
        assert (
            first_completed == "fast_source"
        ), f"Expected fast_source first, got {first_completed}"

    @pytest.mark.asyncio
    async def test_streaming_with_source_failures(self) -> None:
        """Test streaming behavior when some sources fail."""
        query = "neural networks"
        limit = 3

        async def successful_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return self.create_mock_papers("SuccessSource", 2, q)

        async def failing_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)
            raise Exception("Source temporarily unavailable")

        async def timeout_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(10)  # Will timeout
            return []

        search_functions = {
            "success_source": successful_source,
            "failing_source": failing_source,
            "timeout_source": timeout_source,
        }
        api_status = {
            "success_source": True,
            "failing_source": True,
            "timeout_source": True,
        }

        updates = []
        errors = []
        final_results = []

        async for update in create_streaming_search(
            search_functions, query, limit, api_status
        ):
            updates.append(update)

            if update.type == "error":
                errors.append(update)
            elif update.type == "final":
                final_results.extend(update.results or [])

        # Should have errors from failing sources
        assert len(errors) >= 1, "Should have error updates from failed sources"

        # Should still get results from successful source
        assert len(final_results) >= 1, "Should get results from successful sources"

        # Verify error information
        error_sources = [e.source for e in errors]
        assert "failing_source" in error_sources

    @pytest.mark.asyncio
    async def test_streaming_performance_optimization(self) -> None:
        """Test streaming performance with adaptive concurrency."""
        query = "artificial intelligence"
        limit = 4

        # Create sources with different performance characteristics
        async def high_latency_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(1.5)  # High latency
            return self.create_mock_papers("HighLatency", 1, q)

        async def variable_source(q: str, lim: int) -> list[dict[str, Any]]:
            # Variable performance to test adaptive behavior
            await asyncio.sleep(0.2 + (hash(q) % 3) * 0.1)
            return self.create_mock_papers("Variable", 2, q)

        async def fast_reliable_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)  # Consistently fast
            return self.create_mock_papers("FastReliable", 3, q)

        search_functions = {
            "high_latency": high_latency_source,
            "variable": variable_source,
            "fast_reliable": fast_reliable_source,
        }
        api_status = {name: True for name in search_functions.keys()}

        start_time = time.time()
        final_update = None

        async for update in create_streaming_search(
            search_functions, query, limit, api_status
        ):
            if update.type == "final":
                final_update = update
                break

        total_time = time.time() - start_time

        # Verify performance characteristics
        assert (
            total_time < 3.0
        ), f"Total time should be under 3s due to concurrency, got {total_time:.2f}s"
        assert final_update is not None, "Should have final update"

        if final_update.progress:
            # Verify streaming stats are tracked
            streaming_stats = final_update.progress.get("streaming_stats", {})
            assert "total_results" in streaming_stats
            assert "sources_completed" in streaming_stats

    @pytest.mark.asyncio
    async def test_streaming_with_duplicate_detection(self) -> None:
        """Test streaming with realistic paper deduplication."""
        query = "quantum computing"
        limit = 3

        # Create sources that return some duplicate papers
        async def arxiv_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            papers = [
                {
                    "title": "Quantum Machine Learning Algorithms",
                    "authors": ["Alice Quantum", "Bob Computing"],
                    "doi": "10.1234/quantum.ml.2024",
                    "source": "arXiv",
                    "year": 2024,
                    "abstract": "Novel quantum algorithms for machine learning.",
                },
                {
                    "title": "Advances in Quantum Error Correction",
                    "authors": ["Charlie Error", "Diana Correction"],
                    "doi": "10.1234/quantum.ecc.2024",
                    "source": "arXiv",
                    "year": 2024,
                    "abstract": "New techniques for quantum error correction.",
                },
            ]
            return papers

        async def crossref_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.2)
            papers = [
                {
                    "title": "Quantum Machine Learning Algorithms",  # Duplicate title
                    "authors": ["Alice Quantum", "Bob Computing"],
                    "doi": "10.1234/quantum.ml.2024",  # Same DOI
                    "source": "CrossRef",
                    "year": 2024,
                    "abstract": "Novel quantum algorithms for machine learning applications.",
                },
                {
                    "title": "Quantum Supremacy in Practice",
                    "authors": ["Eve Supremacy"],
                    "doi": "10.1234/quantum.supremacy.2024",
                    "source": "CrossRef",
                    "year": 2024,
                    "abstract": "Practical demonstrations of quantum supremacy.",
                },
            ]
            return papers

        search_functions = {"arxiv": arxiv_source, "crossref": crossref_source}
        api_status = {"arxiv": True, "crossref": True}

        final_results = []
        async for update in create_streaming_search(
            search_functions, query, limit, api_status
        ):
            if update.type == "final":
                final_results.extend(update.results or [])

        # Should have deduplicated results (3 unique papers from 4 total)
        assert (
            len(final_results) == 3
        ), f"Expected 3 unique papers after deduplication, got {len(final_results)}"

        # Verify DOI-based deduplication worked
        dois = [result.data.get("doi") for result in final_results]
        unique_dois = set(dois)
        assert (
            len(unique_dois) == 3
        ), "All papers should have unique DOIs after deduplication"

    @pytest.mark.asyncio
    async def test_streaming_progress_tracking(self) -> None:
        """Test detailed progress tracking during streaming."""
        query = "deep learning"
        limit = 2

        # Sources with staggered completion times
        async def source_1(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return self.create_mock_papers("Source1", 1, q)

        async def source_2(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.3)
            return self.create_mock_papers("Source2", 1, q)

        async def source_3(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.5)
            return self.create_mock_papers("Source3", 1, q)

        search_functions = {
            "source_1": source_1,
            "source_2": source_2,
            "source_3": source_3,
        }
        api_status = {name: True for name in search_functions.keys()}

        progress_updates = []
        completion_updates = []

        async for update in create_streaming_search(
            search_functions, query, limit, api_status
        ):
            if update.type == "progress":
                progress_updates.append(update)
            elif update.type == "source_complete":
                completion_updates.append(update)
            elif update.type == "final":
                # Final update should have comprehensive progress info
                assert update.progress is not None
                assert "total_time" in update.progress
                assert "completed_sources" in update.progress
                assert "total_sources" in update.progress
                assert update.progress["total_sources"] == 3
                break

        # Should have completion updates for each source
        assert (
            len(completion_updates) == 3
        ), f"Expected 3 completion updates, got {len(completion_updates)}"

        # Verify completion order matches expected timing
        completion_sources = [u.source for u in completion_updates]
        assert (
            completion_sources[0] == "source_1"
        ), "Fastest source should complete first"

    @pytest.mark.asyncio
    async def test_streaming_circuit_breaker_integration(self) -> None:
        """Test streaming integration with circuit breaker pattern."""
        query = "computer vision"
        limit = 2

        # Simulate a source that consistently fails
        failure_count = 0

        async def unreliable_source(q: str, lim: int) -> list[dict[str, Any]]:
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 3:  # Fail first few attempts
                raise Exception(f"Network error {failure_count}")
            return self.create_mock_papers("Unreliable", 1, q)

        async def reliable_source(q: str, lim: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return self.create_mock_papers("Reliable", 2, q)

        search_functions = {
            "unreliable": unreliable_source,
            "reliable": reliable_source,
        }
        api_status = {"unreliable": True, "reliable": True}

        # First attempt - should get error from unreliable source
        errors = []
        final_results = []

        async for update in create_streaming_search(
            search_functions, query, limit, api_status
        ):
            if update.type == "error":
                errors.append(update)
            elif update.type == "final":
                final_results.extend(update.results or [])

        # Should have error from unreliable source
        assert len(errors) >= 1, "Should have errors from unreliable source"

        # Should still get results from reliable source
        assert len(final_results) >= 1, "Should get results from reliable sources"

        error_sources = [e.source for e in errors if e.source]
        assert "unreliable" in error_sources, "Unreliable source should have errors"


class TestStreamingWithMockMCPServer:
    """Test streaming functionality in the context of MCP server operations."""

    def setup_method(self) -> None:
        """Set up test fixtures with global state reset."""
        # Reset global state for test isolation
        search_analytics.reset_analytics_state()
        result_streamer.reset_streaming_state()

    @pytest.mark.asyncio
    async def test_browse_papers_streaming_simulation(self) -> None:
        """Simulate the browse_papers_streaming MCP tool workflow."""
        # Mock the search functions that would be imported
        mock_search_funcs = {}

        async def mock_arxiv_search(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return [
                {
                    "title": f"arXiv: {query} Research Paper 1",
                    "authors": ["Dr. ArXiv Author"],
                    "abstract": f"Comprehensive study of {query} using novel methodologies.",
                    "year": 2024,
                    "source": "arXiv",
                    "url": "https://arxiv.org/abs/2024.001",
                    "pdf_url": "https://arxiv.org/pdf/2024.001.pdf",
                }
            ]

        async def mock_pubmed_search(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.2)
            return [
                {
                    "title": f"PubMed: Clinical Applications of {query}",
                    "authors": ["Dr. Medical Research"],
                    "abstract": f"Medical applications and clinical trials involving {query}.",
                    "year": 2024,
                    "source": "PubMed",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345",
                    "doi": "10.1234/pubmed.2024.001",
                }
            ]

        mock_search_funcs = {
            "search_arxiv": mock_arxiv_search,
            "search_pubmed": mock_pubmed_search,
        }

        # Simulate API status
        api_status = {"search_arxiv": True, "search_pubmed": True}

        query = "machine learning"
        limit = 10

        # Simulate the MCP tool logic
        available_search_funcs = {
            name: func
            for name, func in mock_search_funcs.items()
            if api_status.get(name, True) and callable(func)
        }

        # Collect results as the MCP tool would
        streaming_results = []
        early_results = []
        final_results = []
        error_messages = []
        source_completion_order = []

        async for update in create_streaming_search(
            available_search_funcs, query, limit, api_status.copy()
        ):
            if update.type == "source_complete":
                source_completion_order.append(update.source)

            elif update.type == "result":
                if update.results:
                    update_results = []
                    for streamed_result in update.results:
                        result_dict = dict(streamed_result.data)
                        result_dict["_streaming_source"] = streamed_result.source
                        result_dict["_streaming_timestamp"] = streamed_result.timestamp
                        result_dict["_streaming_confidence"] = (
                            streamed_result.confidence_score
                        )
                        update_results.append(result_dict)

                    if (
                        update.progress
                        and update.progress.get("type") == "progressive_delivery"
                    ):
                        early_results.extend(update_results)
                    else:
                        streaming_results.extend(update_results)

            elif update.type == "error":
                error_messages.append(f"{update.source}: {update.error}")

            elif update.type == "final":
                if update.results:
                    for streamed_result in update.results:
                        result_dict = dict(streamed_result.data)
                        result_dict["_streaming_source"] = streamed_result.source
                        result_dict["_streaming_timestamp"] = streamed_result.timestamp
                        result_dict["_streaming_confidence"] = (
                            streamed_result.confidence_score
                        )
                        result_dict["_streaming_final"] = True
                        final_results.append(result_dict)

        # Verify MCP tool simulation results
        assert len(source_completion_order) == 2, "Both sources should complete"
        assert len(final_results) == 2, "Should have results from both sources"
        assert len(error_messages) == 0, "Should have no errors in successful case"

        # Verify streaming metadata is properly attached
        for result in final_results:
            assert "_streaming_source" in result
            assert "_streaming_confidence" in result
            assert "_streaming_final" in result

    @pytest.mark.asyncio
    async def test_streaming_category_filtering(self) -> None:
        """Test streaming with force_category filtering like the MCP tool."""

        # Mock search functions for different categories
        async def mock_arxiv(query: str, limit: int) -> list[dict[str, Any]]:
            return [{"title": f"arXiv: {query}", "source": "arXiv"}]

        async def mock_pubmed(query: str, limit: int) -> list[dict[str, Any]]:
            return [{"title": f"PubMed: {query}", "source": "PubMed"}]

        async def mock_crossref(query: str, limit: int) -> list[dict[str, Any]]:
            return [{"title": f"CrossRef: {query}", "source": "CrossRef"}]

        all_search_funcs = {
            "search_arxiv": mock_arxiv,
            "search_pubmed": mock_pubmed,
            "search_crossref": mock_crossref,
        }

        # Simulate category filtering like in the MCP tool
        category_sources = {
            "preprints": ["search_arxiv"],
            "medical": ["search_pubmed"],
            "journals": ["search_crossref", "search_pubmed"],
        }

        # Test preprints category
        force_category = "preprints"
        if force_category in category_sources:
            filtered_funcs = {
                name: func
                for name, func in all_search_funcs.items()
                if name in category_sources[force_category]
            }
        else:
            filtered_funcs = all_search_funcs

        api_status = {name: True for name in all_search_funcs.keys()}

        final_results = []
        async for update in create_streaming_search(
            filtered_funcs, "test query", 5, api_status
        ):
            if update.type == "final":
                final_results.extend(update.results or [])

        # Should only have results from arXiv for preprints category
        assert len(final_results) == 1, "Should have 1 result for preprints category"
        assert (
            final_results[0].data["source"] == "arXiv"
        ), "Should only have arXiv results"

    @pytest.mark.asyncio
    async def test_streaming_error_handling_robustness(self) -> None:
        """Test comprehensive error handling in streaming workflow."""

        # Simulate various types of failures
        async def network_error_source(query: str, limit: int) -> list[dict[str, Any]]:
            raise ConnectionError("Network connection failed")

        async def timeout_source(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(10)  # Simulate timeout
            return []

        async def invalid_response_source(
            query: str, limit: int
        ) -> list[dict[str, Any]]:
            raise ValueError("Invalid JSON response from API")

        async def partial_success_source(
            query: str, limit: int
        ) -> list[dict[str, Any]]:
            # Simulate source that sometimes works
            import random

            if random.random() < 0.7:  # 70% success rate
                return [{"title": "Partial Success Paper", "source": "PartialSuccess"}]
            else:
                raise Exception("Temporary service unavailable")

        search_functions = {
            "network_error": network_error_source,
            "timeout": timeout_source,
            "invalid_response": invalid_response_source,
            "partial_success": partial_success_source,
        }
        api_status = {name: True for name in search_functions.keys()}

        # Collect all updates to analyze error handling
        all_updates = []
        error_count = 0
        successful_sources = 0

        async for update in create_streaming_search(
            search_functions, "test query", 5, api_status
        ):
            all_updates.append(update)

            if update.type == "error":
                error_count += 1
            elif update.type == "source_complete":
                successful_sources += 1

        # Should handle errors gracefully
        assert error_count >= 2, "Should have multiple error updates for failed sources"

        # May have some successful results from partial_success_source
        final_updates = [u for u in all_updates if u.type == "final"]
        assert len(final_updates) == 1, "Should have exactly one final update"

        # Streaming should complete despite errors
        assert len(all_updates) >= 4, "Should have multiple updates despite errors"


class TestStreamingPerformanceIntegration:
    """Integration tests focusing on streaming performance characteristics."""

    def setup_method(self) -> None:
        """Set up test fixtures with global state reset."""
        # Reset global state for test isolation
        search_analytics.reset_analytics_state()
        result_streamer.reset_streaming_state()

    @pytest.mark.asyncio
    async def test_streaming_early_delivery_timing(self) -> None:
        """Test that early delivery happens within expected timeframes."""

        async def instant_source(query: str, limit: int) -> list[dict[str, Any]]:
            return [
                {"title": "Instant Result 1", "source": "InstantSource"},
                {"title": "Instant Result 2", "source": "InstantSource"},
            ]

        async def quick_source(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)  # Quick response
            return [{"title": "Quick Result", "source": "QuickSource"}]

        async def delayed_source(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(1.0)  # 1 second delay
            return [
                {"title": "Delayed Result 1", "source": "DelayedSource"},
                {"title": "Delayed Result 2", "source": "DelayedSource"},
            ]

        search_functions = {
            "instant": instant_source,
            "quick": quick_source,
            "delayed": delayed_source,
        }
        api_status = {"instant": True, "quick": True, "delayed": True}

        start_time = time.time()
        early_delivery_time = None
        final_delivery_time = None

        async for update in create_streaming_search(
            search_functions, "test query", 5, api_status
        ):
            if (
                update.type == "result"
                and update.progress
                and update.progress.get("type") == "progressive_delivery"
            ):
                if early_delivery_time is None:
                    early_delivery_time = time.time() - start_time
            elif update.type == "final":
                final_delivery_time = time.time() - start_time
                break

        # Early delivery should happen quickly (within 0.5 seconds)
        assert early_delivery_time is not None, "Early delivery should occur"
        assert (
            early_delivery_time < 0.5
        ), f"Early delivery should be fast, took {early_delivery_time:.2f}s"

        # Final delivery should include delayed source
        assert (
            final_delivery_time > early_delivery_time
        ), "Final delivery should be after early delivery"
        assert (
            final_delivery_time >= 1.0
        ), "Final delivery should wait for delayed source"

    @pytest.mark.asyncio
    async def test_streaming_concurrent_performance_scaling(self) -> None:
        """Test streaming performance scales with concurrent sources."""
        # Test with increasing numbers of concurrent sources
        for source_count in [2, 4, 8]:
            start_time = time.time()

            # Create multiple sources with similar timing
            search_functions = {}
            for i in range(source_count):

                async def source_func(
                    query: str, limit: int, source_id: int = i
                ) -> list[dict[str, Any]]:
                    await asyncio.sleep(0.2)  # All sources take same time
                    return [
                        {
                            "title": f"Source {source_id} Result",
                            "source": f"Source{source_id}",
                        }
                    ]

                search_functions[f"source_{i}"] = source_func

            api_status = {name: True for name in search_functions.keys()}

            final_results = []
            async for update in create_streaming_search(
                search_functions, "test query", 5, api_status
            ):
                if update.type == "final":
                    final_results.extend(update.results or [])
                    break

            total_time = time.time() - start_time

            # With concurrency, time should not scale linearly with source count
            # Should be closer to 0.2s (single source time) than 0.2s * source_count
            max_expected_time = 0.5  # Allow some overhead
            assert (
                total_time < max_expected_time
            ), f"With {source_count} sources, time {total_time:.2f}s should be under {max_expected_time}s"

            # Should get results from all sources
            assert (
                len(final_results) == source_count
            ), f"Should get {source_count} results, got {len(final_results)}"

    @pytest.mark.asyncio
    async def test_streaming_memory_efficiency(self) -> None:
        """Test that streaming doesn't accumulate excessive memory."""

        # Test with larger result sets to check memory handling
        async def large_result_source(query: str, limit: int) -> list[dict[str, Any]]:
            # Generate a moderate number of results with realistic data
            results = []
            for i in range(20):  # Moderate size to test memory handling
                results.append(
                    {
                        "title": f"Large Dataset Paper {i}: {query} Analysis with extensive methodology and findings",
                        "authors": [f"Author{j}" for j in range(5)],  # Multiple authors
                        "abstract": f"Extensive abstract for paper {i} discussing {query}. "
                        * 10,  # Longer abstract
                        "keywords": [f"keyword{k}" for k in range(10)],
                        "source": "LargeSource",
                        "year": 2024 - (i % 5),
                    }
                )
            return results

        search_functions = {"large_source": large_result_source}
        api_status = {"large_source": True}

        # Process streaming results
        total_results_processed = 0
        async for update in create_streaming_search(
            search_functions, "memory test", 50, api_status
        ):
            if update.type == "final":
                total_results_processed = len(update.results or [])

        # Should process all results without issues
        assert (
            total_results_processed == 20
        ), f"Should process 20 results, got {total_results_processed}"

        # Memory test passes if no exceptions and reasonable processing time
        # This is a basic test - more sophisticated memory profiling could be added
