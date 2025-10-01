"""
Unit tests for search performance optimization functionality.
Tests caching, result prioritization, and concurrent optimization.
"""

import asyncio
import time
from typing import Any
from unittest.mock import patch

import pytest

from paperez_mcp.utils.search_performance_optimizer import (
    ConcurrentSearchOptimizer,
    IntelligentResultCache,
    PerformanceMetrics,
    ResultPrioritizer,
    concurrent_optimizer,
    intelligent_cache,
    optimize_search_performance,
    result_prioritizer,
)


class TestIntelligentResultCache:
    """Test suite for IntelligentResultCache class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.cache = IntelligentResultCache(
            max_size=100, default_ttl=60.0, quality_threshold=0.6
        )

    def test_cache_initialization(self) -> None:
        """Test cache initialization with parameters."""
        assert self.cache.max_size == 100
        assert self.cache.default_ttl == 60.0
        assert self.cache.quality_threshold == 0.6
        assert len(self.cache.cache) == 0
        assert self.cache.hits == 0
        assert self.cache.misses == 0

    def test_query_hash_generation(self) -> None:
        """Test query hash generation."""
        hash1 = self.cache._generate_query_hash("machine learning", "arxiv")
        hash2 = self.cache._generate_query_hash("Machine Learning", "arxiv")
        hash3 = self.cache._generate_query_hash("machine learning", "pubmed")

        # Same query, same source should produce same hash
        assert hash1 == hash2

        # Different source should produce different hash
        assert hash1 != hash3

    def test_query_similarity_calculation(self) -> None:
        """Test query similarity calculation."""
        sim1 = self.cache._calculate_query_similarity(
            "machine learning", "machine learning"
        )
        assert sim1 == 1.0

        sim2 = self.cache._calculate_query_similarity(
            "machine learning", "deep learning"
        )
        assert 0 < sim2 < 1.0

        sim3 = self.cache._calculate_query_similarity(
            "machine learning", "quantum physics"
        )
        assert sim3 < sim2

    def test_result_quality_estimation(self) -> None:
        """Test result quality estimation."""
        # High quality results
        high_quality_results = [
            {
                "title": "Great Paper",
                "pdf_url": "https://example.com/paper.pdf",
                "doi": "10.1234/example",
                "year": 2024,
                "citation_count": 50,
            }
        ]
        high_score = self.cache._estimate_result_quality(high_quality_results)
        assert high_score > 0.8

        # Low quality results
        low_quality_results = [{"title": "Basic Paper"}]  # No PDF, DOI, etc.
        low_score = self.cache._estimate_result_quality(low_quality_results)
        assert low_score < 0.7

        # Empty results
        empty_score = self.cache._estimate_result_quality([])
        assert empty_score == 0.0

    def test_cache_put_and_get(self) -> None:
        """Test basic cache put and get operations."""
        query = "machine learning"
        source = "arxiv"
        results = [
            {
                "title": "ML Paper",
                "pdf_url": "https://example.com/paper.pdf",
                "doi": "10.1234/example",
            }
        ]

        # Put results in cache
        self.cache.put(query, source, results)

        # Get results from cache
        cached_results = self.cache.get(query, source)
        assert cached_results is not None
        assert len(cached_results) == 1
        assert cached_results[0]["title"] == "ML Paper"

        # Check statistics
        assert self.cache.hits == 1
        assert self.cache.misses == 0

    def test_cache_miss(self) -> None:
        """Test cache miss scenario."""
        result = self.cache.get("nonexistent query", "arxiv")
        assert result is None
        assert self.cache.hits == 0
        assert self.cache.misses == 1

    def test_cache_ttl_expiration(self) -> None:
        """Test cache TTL expiration."""
        # Use very short TTL for testing
        short_cache = IntelligentResultCache(default_ttl=0.1)

        query = "test query"
        source = "test_source"
        results = [{"title": "Test Paper", "pdf_url": "test.pdf"}]

        # Put in cache
        short_cache.put(query, source, results)

        # Should get results immediately
        cached = short_cache.get(query, source)
        assert cached is not None

        # Wait for expiration
        time.sleep(0.2)

        # Should be expired now
        expired = short_cache.get(query, source)
        assert expired is None

    def test_cache_quality_threshold(self) -> None:
        """Test that low quality results are not cached."""
        low_quality_results = [{"title": "Poor Paper"}]  # No PDF, DOI, etc.

        self.cache.put("test query", "test_source", low_quality_results)

        # Should not be cached due to low quality
        result = self.cache.get("test query", "test_source")
        assert result is None

    def test_cache_similarity_lookup(self) -> None:
        """Test similarity-based cache lookup."""
        # Cache results for one query
        original_results = [
            {
                "title": "Neural Networks",
                "pdf_url": "https://example.com/nn.pdf",
                "doi": "10.1234/nn",
            }
        ]
        self.cache.put("neural networks", "arxiv", original_results)

        # Try similar query
        similar_results = self.cache.get("neural network", "arxiv")
        assert similar_results is not None  # Should find similar cached results

    def test_cache_eviction_lru(self) -> None:
        """Test LRU cache eviction."""
        small_cache = IntelligentResultCache(max_size=2)

        # Fill cache to capacity
        for i in range(2):
            results = [{"title": f"Paper {i}", "pdf_url": f"paper{i}.pdf"}]
            small_cache.put(f"query {i}", "source", results)

        # Add one more item to trigger eviction
        new_results = [{"title": "New Paper", "pdf_url": "new.pdf"}]
        small_cache.put("new query", "source", new_results)

        # First item should be evicted
        assert small_cache.get("query 0", "source") is None
        assert small_cache.get("query 1", "source") is not None
        assert small_cache.get("new query", "source") is not None

    def test_cache_statistics(self) -> None:
        """Test cache statistics reporting."""
        # Add some cache activity
        results = [{"title": "Test", "pdf_url": "test.pdf"}]
        self.cache.put("test", "source", results)
        self.cache.get("test", "source")  # Hit
        self.cache.get("nonexistent", "source")  # Miss

        stats = self.cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["cache_size"] == 1


class TestResultPrioritizer:
    """Test suite for ResultPrioritizer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.prioritizer = ResultPrioritizer()

    def test_prioritizer_initialization(self) -> None:
        """Test prioritizer initialization."""
        assert len(self.prioritizer.source_weights) > 0
        assert len(self.prioritizer.criteria_weights) > 0
        assert "arxiv" in self.prioritizer.source_weights

    def test_relevance_calculation(self) -> None:
        """Test relevance score calculation."""
        result = {
            "title": "Machine Learning Algorithms for Data Science",
            "abstract": "This paper presents novel machine learning techniques",
        }

        relevance = self.prioritizer._calculate_relevance(result, "machine learning")
        assert relevance > 0.5  # Should have good relevance

        # Test with irrelevant paper
        irrelevant_result = {
            "title": "Quantum Physics Fundamentals",
            "abstract": "Quantum mechanics and wave functions",
        }

        irrelevance = self.prioritizer._calculate_relevance(
            irrelevant_result, "machine learning"
        )
        assert irrelevance < relevance

    def test_recency_score_calculation(self) -> None:
        """Test recency score calculation."""
        # Recent paper
        recent_result = {"year": 2024}
        recent_score = self.prioritizer._calculate_recency_score(recent_result)
        assert recent_score > 0.8

        # Old paper
        old_result = {"year": 2000}
        old_score = self.prioritizer._calculate_recency_score(old_result)
        assert old_score < recent_score

        # No year
        no_year_result = {}
        no_year_score = self.prioritizer._calculate_recency_score(no_year_result)
        assert no_year_score == 0.0

    def test_citation_score_calculation(self) -> None:
        """Test citation score calculation."""
        # High citation count
        high_cited = {"citation_count": 1000}
        high_score = self.prioritizer._calculate_citation_score(high_cited)
        assert high_score > 0.5

        # Low citation count
        low_cited = {"citation_count": 5}
        low_score = self.prioritizer._calculate_citation_score(low_cited)
        assert low_score < high_score

        # No citations
        no_citations = {}
        no_score = self.prioritizer._calculate_citation_score(no_citations)
        assert no_score == 0.0

    def test_source_score_calculation(self) -> None:
        """Test source reliability scoring."""
        arxiv_result = {"source": "arxiv"}
        arxiv_score = self.prioritizer._calculate_source_score(arxiv_result)
        assert arxiv_score > 0.8  # ArXiv should have high score

        unknown_result = {"source": "unknown_source"}
        unknown_score = self.prioritizer._calculate_source_score(unknown_result)
        assert unknown_score == 0.5  # Default score

    def test_pdf_score_calculation(self) -> None:
        """Test PDF availability scoring."""
        with_pdf = {"pdf_url": "https://example.com/paper.pdf"}
        pdf_score = self.prioritizer._calculate_pdf_score(with_pdf)
        assert pdf_score == 1.0

        without_pdf = {"title": "No PDF"}
        no_pdf_score = self.prioritizer._calculate_pdf_score(without_pdf)
        assert no_pdf_score == 0.0

        with_open_access = {"open_access_pdf": "https://oa.example.com/paper.pdf"}
        oa_score = self.prioritizer._calculate_pdf_score(with_open_access)
        assert oa_score == 1.0

    def test_priority_calculation(self) -> None:
        """Test overall priority score calculation."""
        high_priority_result = {
            "title": "Machine Learning Advances",
            "abstract": "Novel machine learning algorithms",
            "year": 2024,
            "citation_count": 100,
            "source": "arxiv",
            "pdf_url": "https://example.com/paper.pdf",
        }

        score = self.prioritizer._calculate_priority_score(
            high_priority_result, "machine learning", None
        )
        assert score > 0.7  # Should have high priority

    def test_user_preference_application(self) -> None:
        """Test user preference adjustments."""
        result = {
            "title": "Open Access Paper",
            "year": 2024,
            "source": "arxiv",
            "open_access_pdf": "https://oa.example.com/paper.pdf",
        }

        preferences = {
            "prefer_open_access": True,
            "prefer_recent": True,
            "preferred_sources": ["arxiv"],
        }

        base_score = 0.5
        adjusted_score = self.prioritizer._apply_user_preferences(
            base_score, result, preferences
        )

        assert adjusted_score > base_score  # Should be boosted

    def test_result_prioritization(self) -> None:
        """Test full result prioritization."""
        results = [
            {
                "title": "Old Low Quality Paper",
                "year": 2000,
                "citation_count": 1,
                "source": "unknown",
            },
            {
                "title": "Recent High Quality Machine Learning Paper",
                "abstract": "Advanced machine learning techniques",
                "year": 2024,
                "citation_count": 200,
                "source": "arxiv",
                "pdf_url": "https://example.com/ml.pdf",
            },
            {
                "title": "Medium Quality Paper",
                "year": 2020,
                "citation_count": 50,
                "source": "pubmed",
            },
        ]

        prioritized = self.prioritizer.prioritize_results(results, "machine learning")

        # Should be sorted by priority score
        assert len(prioritized) == 3
        assert prioritized[0]["title"] == "Recent High Quality Machine Learning Paper"
        assert "_priority_score" in prioritized[0]
        assert prioritized[0]["_priority_score"] > prioritized[1]["_priority_score"]


class TestConcurrentSearchOptimizer:
    """Test suite for ConcurrentSearchOptimizer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.optimizer = ConcurrentSearchOptimizer(max_concurrent=5)

    def test_optimizer_initialization(self) -> None:
        """Test optimizer initialization."""
        assert self.optimizer.max_concurrent == 5
        assert len(self.optimizer.source_performance) == 0
        assert len(self.optimizer.active_searches) == 0

    def test_task_categorization(self) -> None:
        """Test task categorization by expected performance."""
        tasks = [
            ("semantic_scholar", "func1", "args1"),
            ("pubmed", "func2", "args2"),
            ("crossref", "func3", "args3"),
            ("unknown_source", "func4", "args4"),
        ]

        fast, medium, slow = self.optimizer._categorize_tasks(tasks)

        # Check categorization
        fast_sources = [task[0] for task in fast]
        slow_sources = [task[0] for task in slow]

        assert "semantic_scholar" in fast_sources
        assert "crossref" in fast_sources
        assert "pubmed" in slow_sources

    def test_dynamic_timeout_calculation(self) -> None:
        """Test dynamic timeout calculation."""
        # No performance data - should use base timeout
        timeout = self.optimizer._calculate_dynamic_timeout("new_source")
        assert timeout == 30.0  # Base timeout

        # Add performance data
        self.optimizer._update_performance_stats("test_source", 5.0, True)
        timeout_with_data = self.optimizer._calculate_dynamic_timeout("test_source")
        assert timeout_with_data != 30.0  # Should be adjusted

    def test_performance_stats_update(self) -> None:
        """Test performance statistics updating."""
        source = "test_source"

        # Update with successful operation
        self.optimizer._update_performance_stats(source, 2.0, True)
        stats = self.optimizer.source_performance[source]

        assert stats["avg_response_time"] == 2.0
        assert stats["success_rate"] == 1.0
        assert stats["request_count"] == 1

        # Update with failed operation
        self.optimizer._update_performance_stats(source, 5.0, False)
        stats = self.optimizer.source_performance[source]

        assert stats["avg_response_time"] < 5.0  # Weighted average
        assert stats["success_rate"] < 1.0  # Should decrease
        assert stats["request_count"] == 2

    @pytest.mark.asyncio
    async def test_single_task_execution(self) -> None:
        """Test execution of a single search task."""

        async def mock_search_func(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return [{"title": f"Result for {query}"}]

        task = ("test_source", mock_search_func, ("test query", 5))

        source, results, success = await self.optimizer._execute_single_task(task)

        assert source == "test_source"
        assert success is True
        assert len(results) == 1
        assert results[0]["title"] == "Result for test query"

    @pytest.mark.asyncio
    async def test_single_task_execution_failure(self) -> None:
        """Test handling of task execution failure."""

        async def failing_search_func(query: str, limit: int) -> list[dict[str, Any]]:
            raise Exception("Search failed")

        task = ("failing_source", failing_search_func, ("test query", 5))

        source, results, success = await self.optimizer._execute_single_task(task)

        assert source == "failing_source"
        assert success is False
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_batch_execution(self) -> None:
        """Test batch task execution."""

        async def mock_search_1(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)
            return [{"title": f"Result 1 for {query}"}]

        async def mock_search_2(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)
            return [{"title": f"Result 2 for {query}"}]

        tasks = [
            ("source1", mock_search_1, ("test", 5)),
            ("source2", mock_search_2, ("test", 5)),
        ]

        results = await self.optimizer._execute_task_batch(tasks, "fast")

        assert len(results) == 2
        successful_results = [r for r in results if r[2] is True]
        assert len(successful_results) == 2

    @pytest.mark.asyncio
    async def test_optimize_concurrent_search(self) -> None:
        """Test full concurrent search optimization."""

        async def fast_search(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.05)
            return [{"title": f"Fast result for {query}"}]

        async def slow_search(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.2)
            return [{"title": f"Slow result for {query}"}]

        tasks = [
            ("crossref", fast_search, ("test", 5)),  # Fast source
            ("pubmed", slow_search, ("test", 5)),  # Slow source
        ]

        start_time = time.time()
        results = await self.optimizer.optimize_concurrent_search(tasks)
        total_time = time.time() - start_time

        assert len(results) == 2
        # Should be faster than sequential execution due to batching
        assert total_time < 0.5  # Much faster than 0.05 + 0.2 = 0.25 sequential time


class TestOptimizeSearchPerformance:
    """Test suite for the main optimization function."""

    @pytest.mark.asyncio
    async def test_optimize_search_performance(self) -> None:
        """Test the main search optimization function."""

        async def mock_arxiv_search(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return [
                {
                    "title": f"ArXiv paper for {query}",
                    "source": "arxiv",
                    "year": 2024,
                    "pdf_url": "https://arxiv.org/pdf/test.pdf",
                }
            ]

        async def mock_pubmed_search(query: str, limit: int) -> list[dict[str, Any]]:
            await asyncio.sleep(0.1)
            return [
                {
                    "title": f"PubMed paper for {query}",
                    "source": "pubmed",
                    "year": 2023,
                    "doi": "10.1234/pubmed.test",
                }
            ]

        search_functions = {"arxiv": mock_arxiv_search, "pubmed": mock_pubmed_search}

        api_status = {"arxiv": True, "pubmed": True}

        results, metrics = await optimize_search_performance(
            search_functions, "machine learning", 10, api_status
        )

        assert isinstance(results, list)
        assert isinstance(metrics, PerformanceMetrics)
        assert len(results) <= 10
        assert metrics.total_search_time > 0
        assert len(metrics.source_response_times) > 0

    @pytest.mark.asyncio
    async def test_optimize_with_cache_hit(self) -> None:
        """Test optimization with cache hits."""
        # Clear cache first
        test_cache = IntelligentResultCache(max_size=10)

        # Pre-populate cache
        cached_results = [{"title": "Cached Result", "pdf_url": "test.pdf"}]
        test_cache.put("test query", "arxiv", cached_results)

        async def mock_search(query: str, limit: int) -> list[dict[str, Any]]:
            return [{"title": "New Result"}]

        search_functions = {"arxiv": mock_search}
        api_status = {"arxiv": True}

        # Mock the global cache with our test cache
        with patch(
            "paperez_mcp.utils.search_performance_optimizer.intelligent_cache",
            test_cache,
        ):
            results, metrics = await optimize_search_performance(
                search_functions, "test query", 5, api_status
            )

        # Should get cached results
        assert len(results) >= 1
        assert metrics.cache_hit_rate > 0

    @pytest.mark.asyncio
    async def test_optimize_with_user_preferences(self) -> None:
        """Test optimization with user preferences."""

        async def mock_search(query: str, limit: int) -> list[dict[str, Any]]:
            return [
                {"title": "Regular Paper", "year": 2020, "source": "crossref"},
                {
                    "title": "Open Access Paper",
                    "year": 2024,
                    "source": "arxiv",
                    "open_access_pdf": "https://oa.example.com/paper.pdf",
                },
            ]

        search_functions = {"arxiv": mock_search}
        api_status = {"arxiv": True}

        user_preferences = {"prefer_open_access": True, "prefer_recent": True}

        results, metrics = await optimize_search_performance(
            search_functions, "test", 5, api_status, user_preferences
        )

        # Open access paper should be prioritized
        assert results[0]["title"] == "Open Access Paper"


class TestGlobalOptimizationInstances:
    """Test suite for global optimization instances."""

    def test_global_instances_exist(self) -> None:
        """Test that global optimization instances exist."""
        assert intelligent_cache is not None
        assert result_prioritizer is not None
        assert concurrent_optimizer is not None

        assert isinstance(intelligent_cache, IntelligentResultCache)
        assert isinstance(result_prioritizer, ResultPrioritizer)
        assert isinstance(concurrent_optimizer, ConcurrentSearchOptimizer)

    def test_global_cache_functionality(self) -> None:
        """Test global cache basic functionality."""
        # Test basic operations
        results = [{"title": "Global Test", "pdf_url": "test.pdf"}]
        intelligent_cache.put("global test", "test_source", results)

        cached = intelligent_cache.get("global test", "test_source")
        assert cached is not None
        assert len(cached) == 1

    def test_global_prioritizer_functionality(self) -> None:
        """Test global prioritizer basic functionality."""
        results = [
            {"title": "Test Paper 1", "year": 2024},
            {"title": "Test Paper 2", "year": 2020},
        ]

        prioritized = result_prioritizer.prioritize_results(results, "test")
        assert len(prioritized) == 2
        assert "_priority_score" in prioritized[0]


class TestPerformanceMetrics:
    """Test suite for PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self) -> None:
        """Test creation of PerformanceMetrics."""
        metrics = PerformanceMetrics(
            total_search_time=2.5,
            source_response_times={"arxiv": 1.0, "pubmed": 1.5},
            cache_hit_rate=0.3,
            result_quality_score=0.8,
            concurrent_efficiency=3.2,
            memory_usage=1024000,
        )

        assert metrics.total_search_time == 2.5
        assert metrics.source_response_times["arxiv"] == 1.0
        assert metrics.cache_hit_rate == 0.3
        assert metrics.result_quality_score == 0.8
        assert metrics.concurrent_efficiency == 3.2
        assert metrics.memory_usage == 1024000
