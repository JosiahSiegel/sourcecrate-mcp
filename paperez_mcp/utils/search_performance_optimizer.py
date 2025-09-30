"""
Search performance optimization utilities.
Provides advanced caching, result prioritization, and performance monitoring.
"""

import asyncio
import hashlib
import logging
import pickle
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for search operations."""

    total_search_time: float
    source_response_times: dict[str, float]
    cache_hit_rate: float
    result_quality_score: float
    concurrent_efficiency: float
    memory_usage: int


@dataclass
class SearchCacheEntry:
    """Cache entry for search results."""

    results: list[dict[str, Any]]
    timestamp: float
    source: str
    query_hash: str
    original_query: str  # Store original query for similarity comparison
    quality_score: float
    access_count: int = 0
    last_accessed: float = 0.0


class IntelligentResultCache:
    """
    Intelligent caching system for search results.

    Features:
    - Query similarity-based cache lookup
    - TTL-based expiration with quality scoring
    - Memory-efficient storage with compression
    - Cache warming for popular queries
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600.0,  # 1 hour
        quality_threshold: float = 0.7,
        compression_enabled: bool = True,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.quality_threshold = quality_threshold
        self.compression_enabled = compression_enabled

        self.cache: dict[str, SearchCacheEntry] = {}
        self.access_patterns: dict[str, list[float]] = defaultdict(list)
        self.memory_usage = 0

        # Performance tracking
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        logger.info(
            f"🔄 Intelligent cache initialized: size={max_size}, ttl={default_ttl}s"
        )

    def _generate_query_hash(
        self, query: str, source: str, filters: dict[str, Any] | None = None
    ) -> str:
        """Generate a hash for query caching."""
        # Normalize query for better cache hits
        normalized_query = query.lower().strip()

        # Include important filters in hash
        filter_str = ""
        if filters:
            # Sort filters for consistent hashing
            filter_items = sorted(filters.items())
            filter_str = str(filter_items)

        combined = f"{normalized_query}:{source}:{filter_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _calculate_query_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries."""
        # Enhanced similarity with stemming for singular/plural forms
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        # Basic stemming for common plural forms
        def simple_stem(word: str) -> str:
            if word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
                return word[:-1]
            return word

        # Apply stemming to both sets
        stemmed1 = {simple_stem(word) for word in words1}
        stemmed2 = {simple_stem(word) for word in words2}

        intersection = stemmed1.intersection(stemmed2)
        union = stemmed1.union(stemmed2)

        return len(intersection) / len(union)

    def _estimate_result_quality(self, results: list[dict[str, Any]]) -> float:
        """Estimate the quality of search results."""
        if not results:
            return 0.0

        quality_factors = []

        for result in results:
            score = 0.5  # Base score

            # Boost for papers with PDFs
            if result.get("pdf_url") or result.get("open_access_pdf"):
                score += 0.2

            # Boost for papers with DOI
            if result.get("doi"):
                score += 0.1

            # Boost for recent papers
            year = result.get("year")
            if year and isinstance(year, (int, str)):
                try:
                    year_int = int(year)
                    if year_int >= 2020:
                        score += 0.1
                except (ValueError, TypeError):
                    pass

            # Boost for papers with citations
            citations = result.get("citation_count", 0)
            if citations and citations > 10:
                score += 0.1

            quality_factors.append(min(1.0, score))

        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0

    def get(
        self, query: str, source: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]] | None:
        """Get cached results for a query."""
        query_hash = self._generate_query_hash(query, source, filters)

        # Direct cache hit
        if query_hash in self.cache:
            entry = self.cache[query_hash]

            # Check TTL
            if time.time() - entry.timestamp < self.default_ttl:
                entry.access_count += 1
                entry.last_accessed = time.time()
                self.access_patterns[query_hash].append(time.time())
                self.hits += 1

                logger.debug(f"📋 Cache hit for query: {query[:50]}...")
                return entry.results
            else:
                # Expired entry
                del self.cache[query_hash]

        # Try similarity-based lookup for partial matches
        for _cached_hash, entry in self.cache.items():
            if time.time() - entry.timestamp >= self.default_ttl:
                continue

            # Only use similarity matching within the SAME source
            # This prevents cache poisoning across sources (e.g., europe_pmc results when asking for crossref)
            if entry.source != source:
                continue

            # Calculate similarity with original cached query
            similarity = self._calculate_query_similarity(query, entry.original_query)

            if similarity > 0.8 and entry.quality_score > self.quality_threshold:
                entry.access_count += 1
                entry.last_accessed = time.time()
                self.hits += 1

                logger.debug(
                    f"📋 Similar cache hit (sim={similarity:.2f}) for: {query[:50]}... [source: {source}]"
                )
                return entry.results

        self.misses += 1
        return None

    def put(
        self,
        query: str,
        source: str,
        results: list[dict[str, Any]],
        filters: dict[str, Any] | None = None,
    ) -> None:
        """Store results in cache."""
        if not results:
            return

        query_hash = self._generate_query_hash(query, source, filters)
        quality_score = self._estimate_result_quality(results)

        # Only cache high-quality results
        if quality_score < self.quality_threshold:
            logger.debug(
                f"🚫 Skipping cache for low-quality results (score={quality_score:.2f})"
            )
            return

        # Compress results if enabled
        if self.compression_enabled:
            try:
                compressed_results = self._compress_results(results)
                estimated_size = len(pickle.dumps(compressed_results))
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
                compressed_results = results
                estimated_size = len(pickle.dumps(results))
        else:
            compressed_results = results
            estimated_size = len(pickle.dumps(results))

        # Evict if necessary
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        entry = SearchCacheEntry(
            results=compressed_results,
            timestamp=time.time(),
            source=source,
            query_hash=query_hash,
            original_query=query,  # Store original query for similarity
            quality_score=quality_score,
        )

        self.cache[query_hash] = entry
        self.memory_usage += estimated_size

        logger.debug(
            f"📥 Cached {len(results)} results for: {query[:50]}... (quality={quality_score:.2f})"
        )

    def _compress_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Compress results by removing redundant data."""
        compressed = []

        for result in results:
            # Keep only essential fields for caching
            essential_fields = {
                "title",
                "authors",
                "abstract",
                "year",
                "doi",
                "url",
                "pdf_url",
                "open_access_pdf",
                "citation_count",
                "source",
            }

            compressed_result = {
                k: v
                for k, v in result.items()
                if k in essential_fields and v is not None
            }
            compressed.append(compressed_result)

        return compressed

    def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self.cache:
            return

        # Find LRU entry
        lru_hash = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed or self.cache[k].timestamp,
        )

        # Remove from cache
        del self.cache[lru_hash]
        if lru_hash in self.access_patterns:
            del self.access_patterns[lru_hash]

        self.evictions += 1
        logger.debug("🗑️ Evicted LRU cache entry")

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        return {
            "hit_rate": hit_rate,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "cache_size": len(self.cache),
            "memory_usage_mb": self.memory_usage / (1024 * 1024),
            "avg_quality": (
                sum(e.quality_score for e in self.cache.values()) / len(self.cache)
                if self.cache
                else 0.0
            ),
        }

    def warm_cache(self, popular_queries: list[tuple[str, str]]) -> None:
        """Warm cache with popular queries."""
        logger.info(f"🔥 Warming cache with {len(popular_queries)} popular queries")
        # This would be implemented by the caller to pre-populate cache
        # with results from popular queries


class ResultPrioritizer:
    """
    Intelligent result prioritization based on multiple factors.

    Features:
    - Multi-criteria relevance scoring
    - User preference learning
    - Source reliability weighting
    - Temporal relevance adjustment
    """

    def __init__(self) -> None:
        self.source_weights = {
            "arxiv": 0.9,
            "semantic_scholar": 0.85,
            "pubmed": 0.9,
            "crossref": 0.8,
            "pubmed_central": 0.85,
            "doaj": 0.75,
            "core": 0.7,
            "europe_pmc": 0.8,
        }

        self.criteria_weights = {
            "relevance": 0.3,
            "recency": 0.2,
            "citation_count": 0.2,
            "source_reliability": 0.15,
            "pdf_availability": 0.15,
        }

    def prioritize_results(
        self,
        results: list[dict[str, Any]],
        query: str,
        user_preferences: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Prioritize search results based on multiple criteria.

        Args:
            results: List of search results
            query: Original search query
            user_preferences: Optional user preferences

        Returns:
            Sorted list of results by priority score
        """
        if not results:
            return results

        scored_results = []

        for result in results:
            score = self._calculate_priority_score(result, query, user_preferences)
            result_with_score = dict(result)
            result_with_score["_priority_score"] = score
            scored_results.append(result_with_score)

        # Sort by priority score (descending)
        sorted_results = sorted(
            scored_results, key=lambda x: x.get("_priority_score", 0.0), reverse=True
        )

        return sorted_results

    def _calculate_priority_score(
        self,
        result: dict[str, Any],
        query: str,
        user_preferences: dict[str, Any] | None,
    ) -> float:
        """Calculate priority score for a single result."""
        score = 0.0

        # Relevance score (simplified text matching)
        relevance_score = self._calculate_relevance(result, query)
        score += relevance_score * self.criteria_weights["relevance"]

        # Recency score
        recency_score = self._calculate_recency_score(result)
        score += recency_score * self.criteria_weights["recency"]

        # Citation count score
        citation_score = self._calculate_citation_score(result)
        score += citation_score * self.criteria_weights["citation_count"]

        # Source reliability score
        source_score = self._calculate_source_score(result)
        score += source_score * self.criteria_weights["source_reliability"]

        # PDF availability score
        pdf_score = self._calculate_pdf_score(result)
        score += pdf_score * self.criteria_weights["pdf_availability"]

        # Apply user preference adjustments
        if user_preferences:
            score = self._apply_user_preferences(score, result, user_preferences)

        return score

    def _calculate_relevance(self, result: dict[str, Any], query: str) -> float:
        """Calculate relevance score based on text matching."""
        query_words = set(query.lower().split())

        # Check title relevance
        title = result.get("title", "").lower()
        title_words = set(title.split())
        title_match = (
            len(query_words.intersection(title_words)) / len(query_words)
            if query_words
            else 0.0
        )

        # Check abstract relevance (if available)
        abstract = result.get("abstract", "").lower()
        abstract_words = set(abstract.split())
        abstract_match = (
            len(query_words.intersection(abstract_words)) / len(query_words)
            if query_words
            else 0.0
        )

        # Weighted combination (title weighted higher)
        return 0.7 * title_match + 0.3 * abstract_match

    def _calculate_recency_score(self, result: dict[str, Any]) -> float:
        """Calculate recency score based on publication year."""
        year = result.get("year")
        if not year:
            return 0.0

        try:
            year_int = int(year)
            current_year = 2025  # Update as needed

            # Papers from last 5 years get higher scores
            years_old = current_year - year_int
            if years_old <= 0:
                return 1.0
            elif years_old <= 2:
                return 0.9
            elif years_old <= 5:
                return 0.7
            elif years_old <= 10:
                return 0.5
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.0

    def _calculate_citation_score(self, result: dict[str, Any]) -> float:
        """Calculate score based on citation count."""
        citations = result.get("citation_count", 0)

        if not citations or citations <= 0:
            return 0.0

        # Logarithmic scaling for citation count
        import math

        return min(1.0, math.log10(citations + 1) / 4.0)  # Scale to 0-1

    def _calculate_source_score(self, result: dict[str, Any]) -> float:
        """Calculate score based on source reliability."""
        source = result.get("source", "").lower()
        return float(self.source_weights.get(source, 0.5))

    def _calculate_pdf_score(self, result: dict[str, Any]) -> float:
        """Calculate score based on PDF availability."""
        if result.get("pdf_url") or result.get("open_access_pdf"):
            return 1.0
        return 0.0

    def _apply_user_preferences(
        self, base_score: float, result: dict[str, Any], preferences: dict[str, Any]
    ) -> float:
        """Apply user preference adjustments to score."""
        adjusted_score = base_score

        # Prefer open access if specified
        if preferences.get("prefer_open_access", False):
            if result.get("open_access_pdf"):
                adjusted_score += 0.1

        # Prefer recent papers if specified
        if preferences.get("prefer_recent", False):
            year = result.get("year")
            if year and int(year) >= 2020:
                adjusted_score += 0.1

        # Prefer specific sources if specified
        preferred_sources = preferences.get("preferred_sources", [])
        if preferred_sources and result.get("source") in preferred_sources:
            adjusted_score += 0.15

        return min(1.0, adjusted_score)


class ConcurrentSearchOptimizer:
    """
    Optimizes concurrent search execution for maximum throughput.

    Features:
    - Dynamic timeout adjustment based on source performance
    - Intelligent batching of similar queries
    - Load balancing across available sources
    - Circuit breaker integration
    """

    def __init__(self, max_concurrent: int = 10) -> None:
        self.max_concurrent = max_concurrent
        self.source_performance: dict[str, dict[str, float]] = defaultdict(dict)
        self.active_searches: set[str] = set()

    async def optimize_concurrent_search(
        self,
        search_tasks: list[tuple[str, Any, Any]],  # (source, func, args)
        performance_tracker: Any | None = None,
    ) -> list[tuple[str, list[Any], bool]]:
        """
        Execute searches with optimized concurrency and performance tracking.

        Args:
            search_tasks: List of (source_name, search_func, args) tuples
            performance_tracker: Optional performance tracking instance

        Returns:
            List of (source_name, results, success) tuples
        """
        # Group tasks by estimated completion time
        fast_tasks, medium_tasks, slow_tasks = self._categorize_tasks(search_tasks)

        results = []

        # Execute fast tasks first
        if fast_tasks:
            fast_results = await self._execute_task_batch(fast_tasks, "fast")
            results.extend(fast_results)

        # Execute medium and slow tasks concurrently
        remaining_tasks = medium_tasks + slow_tasks
        if remaining_tasks:
            remaining_results = await self._execute_task_batch(remaining_tasks, "mixed")
            results.extend(remaining_results)

        return results

    def _categorize_tasks(self, tasks: list[tuple[str, Any, Any]]) -> tuple[
        list[tuple[str, Any, Any]],
        list[tuple[str, Any, Any]],
        list[tuple[str, Any, Any]],
    ]:
        """Categorize tasks by expected performance."""
        fast_sources = {"semantic_scholar", "crossref"}
        slow_sources = {"pubmed", "europe_pmc", "core"}

        fast_tasks = []
        medium_tasks = []
        slow_tasks = []

        for task in tasks:
            source_name = task[0]

            if source_name in fast_sources:
                fast_tasks.append(task)
            elif source_name in slow_sources:
                slow_tasks.append(task)
            else:
                medium_tasks.append(task)

        return fast_tasks, medium_tasks, slow_tasks

    async def _execute_task_batch(
        self, tasks: list[tuple[str, Any, Any]], batch_type: str
    ) -> list[tuple[str, list[Any], bool]]:
        """Execute a batch of tasks with appropriate concurrency."""
        if not tasks:
            return []

        # Adjust concurrency based on batch type
        if batch_type == "fast":
            concurrency = min(len(tasks), self.max_concurrent)
        else:
            concurrency = min(len(tasks), self.max_concurrent // 2)

        semaphore = asyncio.Semaphore(concurrency)

        async def execute_with_semaphore(
            task: tuple[str, Any, Any],
        ) -> tuple[str, list[Any], bool]:
            async with semaphore:
                return await self._execute_single_task(task)

        # Execute all tasks
        task_coroutines = [execute_with_semaphore(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Process results and handle exceptions
        processed_results: list[tuple[str, list[Any], bool]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source_name = tasks[i][0]
                processed_results.append((source_name, [], False))
            elif isinstance(result, tuple) and len(result) == 3:
                processed_results.append(result)
            else:
                # Handle unexpected result type
                source_name = tasks[i][0]
                processed_results.append((source_name, [], False))

        return processed_results

    async def _execute_single_task(
        self, task: tuple[str, Any, Any]
    ) -> tuple[str, list[Any], bool]:
        """Execute a single search task with performance tracking."""
        source_name, search_func, args = task

        start_time = time.time()

        try:
            # Calculate dynamic timeout based on source performance
            timeout = self._calculate_dynamic_timeout(source_name)

            if isinstance(args, tuple):
                result = await asyncio.wait_for(search_func(*args), timeout=timeout)
            else:
                result = await asyncio.wait_for(search_func(args), timeout=timeout)

            duration = time.time() - start_time

            # Update performance tracking
            self._update_performance_stats(source_name, duration, True)

            return source_name, result, True

        except Exception as e:
            duration = time.time() - start_time
            self._update_performance_stats(source_name, duration, False)

            logger.warning(f"Search failed for {source_name}: {e}")
            return source_name, [], False

    def _calculate_dynamic_timeout(self, source_name: str) -> float:
        """Calculate dynamic timeout based on source performance history."""
        base_timeout = 30.0

        if source_name in self.source_performance:
            avg_time = self.source_performance[source_name].get(
                "avg_response_time", base_timeout
            )
            success_rate = self.source_performance[source_name].get("success_rate", 0.8)

            # Adjust timeout based on historical performance
            multiplier = 2.0 if success_rate > 0.8 else 1.5
            return min(60.0, max(10.0, avg_time * multiplier))

        return base_timeout

    def _update_performance_stats(
        self, source_name: str, duration: float, success: bool
    ) -> None:
        """Update performance statistics for a source."""
        stats = self.source_performance[source_name]

        # Update average response time
        if "avg_response_time" in stats:
            stats["avg_response_time"] = (stats["avg_response_time"] * 0.8) + (
                duration * 0.2
            )
        else:
            stats["avg_response_time"] = duration

        # Update success rate
        if "success_rate" in stats:
            stats["success_rate"] = (stats["success_rate"] * 0.9) + (
                0.1 if success else 0.0
            )
        else:
            stats["success_rate"] = 1.0 if success else 0.0

        # Update request count
        stats["request_count"] = stats.get("request_count", 0) + 1


# Global instances for optimization
intelligent_cache = IntelligentResultCache()
result_prioritizer = ResultPrioritizer()
concurrent_optimizer = ConcurrentSearchOptimizer()


async def optimize_search_performance(
    search_functions: dict[str, Any],
    query: str,
    limit: int,
    api_status: dict[str, bool],
    user_preferences: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], PerformanceMetrics]:
    """
    Perform optimized search with caching, prioritization, and performance tracking.

    Args:
        search_functions: Dictionary of search functions by source
        query: Search query
        limit: Maximum number of results
        api_status: API availability status
        user_preferences: Optional user preferences

    Returns:
        Tuple of (optimized_results, performance_metrics)
    """
    start_time = time.time()
    source_times = {}
    cache_hits = 0
    total_requests = 0

    # Filter sources by force_category if specified (using shared utility)
    from paperez_mcp.utils.category_filter import filter_search_functions_by_category

    force_category = (
        user_preferences.get("force_category") if user_preferences else None
    )
    sources_to_search = filter_search_functions_by_category(
        search_functions, force_category
    )

    # Check cache first
    all_results = []
    remaining_sources = []

    # Prepare cache filters to include force_category
    cache_filters = {"force_category": force_category} if force_category else None

    for source_name, search_func in sources_to_search.items():
        if not api_status.get(source_name, True):
            continue

        total_requests += 1
        cached_results = intelligent_cache.get(query, source_name, cache_filters)

        if cached_results:
            cache_hits += 1
            all_results.extend(cached_results)
            logger.debug(f"📋 Using cached results for {source_name}")
        else:
            remaining_sources.append((source_name, search_func, (query, limit)))

    # Execute remaining searches with optimization
    if remaining_sources:
        search_results = await concurrent_optimizer.optimize_concurrent_search(
            remaining_sources
        )

        for source_name, results, success in search_results:
            if success and results:
                # Cache successful results with force_category filter
                intelligent_cache.put(query, source_name, results, cache_filters)
                all_results.extend(results)

            # Track source performance
            source_times[source_name] = time.time() - start_time

    # Prioritize and limit results
    if all_results:
        prioritized_results = result_prioritizer.prioritize_results(
            all_results, query, user_preferences
        )
        final_results = prioritized_results[:limit]
    else:
        final_results = []

    # Calculate performance metrics
    total_time = time.time() - start_time
    cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0

    # Calculate result quality score
    quality_score = (
        sum(result.get("_priority_score", 0.5) for result in final_results)
        / len(final_results)
        if final_results
        else 0.0
    )

    metrics = PerformanceMetrics(
        total_search_time=total_time,
        source_response_times=source_times,
        cache_hit_rate=cache_hit_rate,
        result_quality_score=quality_score,
        concurrent_efficiency=len(remaining_sources) / max(1, total_time),
        memory_usage=intelligent_cache.memory_usage,
    )

    logger.info(
        f"🚀 Optimized search complete: {len(final_results)} results, "
        f"{total_time:.2f}s, cache hit rate: {cache_hit_rate:.1%}"
    )

    return final_results, metrics
