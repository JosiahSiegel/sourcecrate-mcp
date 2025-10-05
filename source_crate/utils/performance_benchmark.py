"""
Performance benchmarking utilities for SourceCrateMCP.
Provides timing, profiling, and performance measurement tools.
"""

import asyncio
import json
import logging
import statistics
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance measurement."""

    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "success": self.success,
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkReport:
    """Comprehensive benchmark report."""

    operation_type: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_duration: float
    average_duration: float
    min_duration: float
    max_duration: float
    median_duration: float
    std_deviation: float
    operations_per_second: float
    metrics: list[PerformanceMetric] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation_type": self.operation_type,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "total_duration": self.total_duration,
            "average_duration": self.average_duration,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "median_duration": self.median_duration,
            "std_deviation": self.std_deviation,
            "operations_per_second": self.operations_per_second,
            "metrics": [m.to_dict() for m in self.metrics],
        }


class PerformanceBenchmark:
    """Performance benchmarking and profiling tool."""

    def __init__(self, name: str = "benchmark"):
        self.name = name
        self.metrics: list[PerformanceMetric] = []
        self.start_time: float | None = None
        self.end_time: float | None = None

    @asynccontextmanager
    async def measure_operation(
        self, operation_name: str, metadata: dict[str, Any] | None = None
    ) -> Any:
        """Context manager to measure operation performance."""
        start_time = time.time()
        success = True

        try:
            yield
        except Exception as e:
            success = False
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            metric = PerformanceMetric(
                operation=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                metadata=metadata or {},
            )

            self.metrics.append(metric)

            logger.debug(
                f"📊 {operation_name}: {duration:.3f}s " f"{'✅' if success else '❌'}"
            )

    def start_benchmark(self) -> None:
        """Start the overall benchmark timer."""
        self.start_time = time.time()
        self.metrics.clear()
        logger.info(f"🚀 Starting benchmark: {self.name}")

    def end_benchmark(self) -> None:
        """End the overall benchmark timer."""
        self.end_time = time.time()
        logger.info(f"🏁 Completed benchmark: {self.name}")

    def generate_report(self, operation_filter: str | None = None) -> BenchmarkReport:
        """Generate a comprehensive performance report."""
        filtered_metrics = self.metrics

        if operation_filter:
            filtered_metrics = [
                m
                for m in self.metrics
                if operation_filter.lower() in m.operation.lower()
            ]

        if not filtered_metrics:
            logger.warning("No metrics found for report generation")
            return BenchmarkReport(
                operation_type=operation_filter or "all",
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                total_duration=0.0,
                average_duration=0.0,
                min_duration=0.0,
                max_duration=0.0,
                median_duration=0.0,
                std_deviation=0.0,
                operations_per_second=0.0,
            )

        successful_metrics = [m for m in filtered_metrics if m.success]
        durations = [m.duration for m in filtered_metrics]

        total_duration = sum(durations)

        # Calculate statistics
        avg_duration = statistics.mean(durations) if durations else 0.0
        min_duration = min(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0.0
        median_duration = statistics.median(durations) if durations else 0.0
        std_dev = statistics.stdev(durations) if len(durations) > 1 else 0.0

        # Calculate operations per second
        ops_per_second = (
            len(filtered_metrics) / total_duration if total_duration > 0 else 0.0
        )

        return BenchmarkReport(
            operation_type=operation_filter or "all",
            total_operations=len(filtered_metrics),
            successful_operations=len(successful_metrics),
            failed_operations=len(filtered_metrics) - len(successful_metrics),
            total_duration=total_duration,
            average_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            median_duration=median_duration,
            std_deviation=std_dev,
            operations_per_second=ops_per_second,
            metrics=filtered_metrics,
        )

    def save_report(self, report: BenchmarkReport, output_path: str) -> None:
        """Save benchmark report to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(report.to_dict(), f, indent=2)

            logger.info(f"📄 Benchmark report saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save benchmark report: {e}")

    def print_summary(self, report: BenchmarkReport) -> None:
        """Print a human-readable benchmark summary."""
        print(f"\n{'='*60}")
        print(f"📊 PERFORMANCE BENCHMARK REPORT: {self.name}")
        print(f"{'='*60}")
        print(f"Operation Type: {report.operation_type}")
        print(f"Total Operations: {report.total_operations}")
        print(f"Successful: {report.successful_operations}")
        print(f"Failed: {report.failed_operations}")
        print(
            f"Success Rate: {(report.successful_operations/report.total_operations*100):.1f}%"
        )
        print("\n📈 TIMING STATISTICS:")
        print(f"Total Duration: {report.total_duration:.3f} seconds")
        print(f"Average Duration: {report.average_duration:.3f} seconds")
        print(f"Min Duration: {report.min_duration:.3f} seconds")
        print(f"Max Duration: {report.max_duration:.3f} seconds")
        print(f"Median Duration: {report.median_duration:.3f} seconds")
        print(f"Std Deviation: {report.std_deviation:.3f} seconds")
        print(f"Operations/Second: {report.operations_per_second:.2f}")
        print(f"{'='*60}\n")


class SearchBenchmark(PerformanceBenchmark):
    """Specialized benchmark for search operations."""

    def __init__(self) -> None:
        super().__init__("search_performance")

    async def benchmark_search_query(
        self,
        search_func: Callable,
        query: str,
        category: str | None = None,
        iterations: int = 3,
    ) -> BenchmarkReport:
        """Benchmark a specific search query multiple times."""
        self.start_benchmark()

        for i in range(iterations):
            metadata = {"query": query, "category": category, "iteration": i + 1}

            async with self.measure_operation(f"search_query_{i+1}", metadata):
                try:
                    await search_func(query, category=category)
                except Exception as e:
                    logger.error(f"Search failed on iteration {i+1}: {e}")

        self.end_benchmark()
        return self.generate_report("search_query")

    async def benchmark_multi_source_search(
        self, search_func: Callable, queries: list[str], concurrent: bool = True
    ) -> BenchmarkReport:
        """Benchmark multiple search queries."""
        self.start_benchmark()

        if concurrent:
            # Run searches concurrently
            tasks = []
            for i, query in enumerate(queries):
                metadata = {"query": query, "concurrent": True}

                async def search_with_measurement(
                    q: str, meta: dict[str, Any], idx: int
                ) -> None:
                    async with self.measure_operation(f"concurrent_search_{idx}", meta):
                        await search_func(q)

                tasks.append(search_with_measurement(query, metadata, i))

            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Run searches sequentially
            for i, query in enumerate(queries):
                metadata = {"query": query, "concurrent": False}
                async with self.measure_operation(f"sequential_search_{i}", metadata):
                    await search_func(query)

        self.end_benchmark()
        return self.generate_report()


class PDFBenchmark(PerformanceBenchmark):
    """Specialized benchmark for PDF processing operations."""

    def __init__(self) -> None:
        super().__init__("pdf_performance")

    async def benchmark_pdf_conversion(
        self, convert_func: Callable, pdf_files: list[str], parallel: bool = True
    ) -> BenchmarkReport:
        """Benchmark PDF conversion operations."""
        self.start_benchmark()

        if parallel and len(pdf_files) > 1:
            # Parallel conversion
            tasks = []
            for i, pdf_file in enumerate(pdf_files):
                metadata = {"pdf_file": pdf_file, "parallel": True}

                async def convert_with_measurement(
                    file: str, meta: dict[str, Any], idx: int
                ) -> None:
                    async with self.measure_operation(f"parallel_convert_{idx}", meta):
                        await convert_func(file)

                tasks.append(convert_with_measurement(pdf_file, metadata, i))

            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Sequential conversion
            for i, pdf_file in enumerate(pdf_files):
                metadata = {"pdf_file": pdf_file, "parallel": False}
                async with self.measure_operation(f"sequential_convert_{i}", metadata):
                    await convert_func(pdf_file)

        self.end_benchmark()
        return self.generate_report()


# Global benchmark instances
search_benchmark = SearchBenchmark()
pdf_benchmark = PDFBenchmark()
general_benchmark = PerformanceBenchmark("general")


async def run_comprehensive_benchmark(
    search_func: Callable | None = None,
    pdf_convert_func: Callable | None = None,
    output_dir: str = ".sourcecrate/benchmarks",
) -> dict[str, BenchmarkReport]:
    """Run a comprehensive performance benchmark suite."""
    logger.info("🚀 Starting comprehensive performance benchmark")

    reports = {}

    if search_func:
        # Benchmark search operations
        test_queries = [
            "machine learning",
            "climate change",
            "quantum computing",
            "medical research",
        ]

        # Sequential search benchmark
        seq_report = await search_benchmark.benchmark_multi_source_search(
            search_func, test_queries, concurrent=False
        )
        reports["search_sequential"] = seq_report

        # Concurrent search benchmark
        conc_report = await search_benchmark.benchmark_multi_source_search(
            search_func, test_queries, concurrent=True
        )
        reports["search_concurrent"] = conc_report

    if pdf_convert_func:
        # Note: This would require actual PDF files to be meaningful
        logger.info("PDF benchmark requires actual PDF files - skipping for now")

    # Save all reports
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    for name, report in reports.items():
        report_file = output_path / f"{name}_benchmark_{timestamp}.json"
        search_benchmark.save_report(report, str(report_file))
        search_benchmark.print_summary(report)

    logger.info("✅ Comprehensive benchmark completed")
    return reports
