"""
Unit tests for performance benchmarking functionality.
Tests timing, metrics collection, and performance reporting.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path

import pytest

from source_crate.utils.performance_benchmark import (
    BenchmarkReport,
    PDFBenchmark,
    PerformanceBenchmark,
    PerformanceMetric,
    SearchBenchmark,
    general_benchmark,
)


class TestPerformanceMetric:
    """Test suite for PerformanceMetric class."""

    def test_metric_creation(self):
        """Test metric creation and properties."""
        start_time = time.time()
        end_time = start_time + 1.5
        duration = end_time - start_time

        metric = PerformanceMetric(
            operation="test_operation",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=True,
            metadata={"test": "data"},
        )

        assert metric.operation == "test_operation"
        assert metric.start_time == start_time
        assert metric.end_time == end_time
        assert metric.duration == duration
        assert metric.success is True
        assert metric.metadata == {"test": "data"}

    def test_metric_to_dict(self):
        """Test metric serialization to dictionary."""
        metric = PerformanceMetric(
            operation="test_op",
            start_time=1000.0,
            end_time=1001.5,
            duration=1.5,
            success=True,
            metadata={"key": "value"},
        )

        metric_dict = metric.to_dict()

        expected = {
            "operation": "test_op",
            "start_time": 1000.0,
            "end_time": 1001.5,
            "duration": 1.5,
            "success": True,
            "metadata": {"key": "value"},
        }

        assert metric_dict == expected


class TestBenchmarkReport:
    """Test suite for BenchmarkReport class."""

    def test_report_creation(self):
        """Test benchmark report creation."""
        metrics = [
            PerformanceMetric("op1", 1000.0, 1001.0, 1.0, True),
            PerformanceMetric("op2", 1001.0, 1003.0, 2.0, True),
        ]

        report = BenchmarkReport(
            operation_type="test",
            total_operations=2,
            successful_operations=2,
            failed_operations=0,
            total_duration=3.0,
            average_duration=1.5,
            min_duration=1.0,
            max_duration=2.0,
            median_duration=1.5,
            std_deviation=0.5,
            operations_per_second=0.67,
            metrics=metrics,
        )

        assert report.operation_type == "test"
        assert report.total_operations == 2
        assert report.successful_operations == 2
        assert report.operations_per_second == 0.67

    def test_report_to_dict(self):
        """Test report serialization to dictionary."""
        metric = PerformanceMetric("op1", 1000.0, 1001.0, 1.0, True)
        report = BenchmarkReport(
            operation_type="test",
            total_operations=1,
            successful_operations=1,
            failed_operations=0,
            total_duration=1.0,
            average_duration=1.0,
            min_duration=1.0,
            max_duration=1.0,
            median_duration=1.0,
            std_deviation=0.0,
            operations_per_second=1.0,
            metrics=[metric],
        )

        report_dict = report.to_dict()

        assert report_dict["operation_type"] == "test"
        assert report_dict["total_operations"] == 1
        assert len(report_dict["metrics"]) == 1
        assert isinstance(report_dict["metrics"][0], dict)


class TestPerformanceBenchmark:
    """Test suite for PerformanceBenchmark class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.benchmark = PerformanceBenchmark("test_benchmark")

    def test_benchmark_initialization(self):
        """Test benchmark initialization."""
        assert self.benchmark.name == "test_benchmark"
        assert len(self.benchmark.metrics) == 0
        assert self.benchmark.start_time is None
        assert self.benchmark.end_time is None

    def test_benchmark_timing(self):
        """Test start and end benchmark timing."""
        self.benchmark.start_benchmark()
        assert self.benchmark.start_time is not None
        assert len(self.benchmark.metrics) == 0  # Should clear metrics

        time.sleep(0.1)

        self.benchmark.end_benchmark()
        assert self.benchmark.end_time is not None
        assert self.benchmark.end_time > self.benchmark.start_time

    @pytest.mark.asyncio
    async def test_measure_operation_success(self):
        """Test successful operation measurement."""
        async with self.benchmark.measure_operation("test_op", {"test": "metadata"}):
            await asyncio.sleep(0.1)

        assert len(self.benchmark.metrics) == 1
        metric = self.benchmark.metrics[0]

        assert metric.operation == "test_op"
        assert metric.success is True
        assert metric.duration >= 0.1
        assert metric.metadata == {"test": "metadata"}

    @pytest.mark.asyncio
    async def test_measure_operation_failure(self):
        """Test failed operation measurement."""
        with pytest.raises(ValueError):
            async with self.benchmark.measure_operation("failing_op"):
                await asyncio.sleep(0.05)
                raise ValueError("Test error")

        assert len(self.benchmark.metrics) == 1
        metric = self.benchmark.metrics[0]

        assert metric.operation == "failing_op"
        assert metric.success is False
        assert metric.duration >= 0.05

    def test_generate_report_empty(self):
        """Test report generation with no metrics."""
        report = self.benchmark.generate_report()

        assert report.operation_type == "all"
        assert report.total_operations == 0
        assert report.successful_operations == 0
        assert report.operations_per_second == 0.0

    def test_generate_report_with_metrics(self):
        """Test report generation with metrics."""
        # Add some test metrics
        self.benchmark.metrics = [
            PerformanceMetric("op1", 1000.0, 1001.0, 1.0, True),
            PerformanceMetric("op2", 1001.0, 1003.0, 2.0, True),
            PerformanceMetric("op3", 1003.0, 1003.5, 0.5, False),
        ]

        report = self.benchmark.generate_report()

        assert report.total_operations == 3
        assert report.successful_operations == 2
        assert report.failed_operations == 1
        assert report.total_duration == 3.5
        assert report.average_duration == pytest.approx(1.167, rel=1e-2)
        assert report.min_duration == 0.5
        assert report.max_duration == 2.0
        assert report.median_duration == 1.0

    def test_generate_report_with_filter(self):
        """Test report generation with operation filter."""
        self.benchmark.metrics = [
            PerformanceMetric("search_op1", 1000.0, 1001.0, 1.0, True),
            PerformanceMetric("convert_op1", 1001.0, 1002.0, 1.0, True),
            PerformanceMetric("search_op2", 1002.0, 1003.0, 1.0, True),
        ]

        report = self.benchmark.generate_report("search")

        assert report.operation_type == "search"
        assert report.total_operations == 2
        assert len(report.metrics) == 2

    def test_save_report(self):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.json"

            # Create a simple report
            report = BenchmarkReport(
                operation_type="test",
                total_operations=1,
                successful_operations=1,
                failed_operations=0,
                total_duration=1.0,
                average_duration=1.0,
                min_duration=1.0,
                max_duration=1.0,
                median_duration=1.0,
                std_deviation=0.0,
                operations_per_second=1.0,
            )

            self.benchmark.save_report(report, str(output_path))

            # Verify file was created and contains valid JSON
            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
                assert data["operation_type"] == "test"
                assert data["total_operations"] == 1


class TestSearchBenchmark:
    """Test suite for SearchBenchmark class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search_benchmark = SearchBenchmark()

    @pytest.mark.asyncio
    async def test_benchmark_search_query(self):
        """Test search query benchmarking."""

        async def mock_search_func(query, category=None):
            await asyncio.sleep(0.1)
            return [{"title": f"Result for {query}"}]

        report = await self.search_benchmark.benchmark_search_query(
            mock_search_func, "test query", iterations=2
        )

        assert report.operation_type == "search_query"
        assert report.total_operations == 2
        assert report.total_duration >= 0.2

    @pytest.mark.asyncio
    async def test_benchmark_multi_source_concurrent(self):
        """Test concurrent multi-source search benchmarking."""

        async def mock_search_func(query):
            await asyncio.sleep(0.1)
            return [{"title": f"Result for {query}"}]

        queries = ["query1", "query2", "query3"]

        report = await self.search_benchmark.benchmark_multi_source_search(
            mock_search_func, queries, concurrent=True
        )

        assert report.total_operations == 3
        # Concurrent execution should be faster than sequential
        assert report.total_duration < 0.35  # Should be ~0.1 with concurrency

    @pytest.mark.asyncio
    async def test_benchmark_multi_source_sequential(self):
        """Test sequential multi-source search benchmarking."""

        async def mock_search_func(query):
            await asyncio.sleep(0.1)
            return [{"title": f"Result for {query}"}]

        queries = ["query1", "query2"]

        report = await self.search_benchmark.benchmark_multi_source_search(
            mock_search_func, queries, concurrent=False
        )

        assert report.total_operations == 2
        # Sequential execution should take longer
        assert report.total_duration >= 0.2


class TestPDFBenchmark:
    """Test suite for PDFBenchmark class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pdf_benchmark = PDFBenchmark()

    @pytest.mark.asyncio
    async def test_benchmark_pdf_conversion_parallel(self):
        """Test parallel PDF conversion benchmarking."""

        async def mock_convert_func(pdf_file):
            await asyncio.sleep(0.1)
            return {"success": True, "file": pdf_file}

        pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]

        report = await self.pdf_benchmark.benchmark_pdf_conversion(
            mock_convert_func, pdf_files, parallel=True
        )

        assert report.total_operations == 3
        # Parallel execution should be faster
        assert report.total_duration < 0.35

    @pytest.mark.asyncio
    async def test_benchmark_pdf_conversion_sequential(self):
        """Test sequential PDF conversion benchmarking."""

        async def mock_convert_func(pdf_file):
            await asyncio.sleep(0.1)
            return {"success": True, "file": pdf_file}

        pdf_files = ["file1.pdf", "file2.pdf"]

        report = await self.pdf_benchmark.benchmark_pdf_conversion(
            mock_convert_func, pdf_files, parallel=False
        )

        assert report.total_operations == 2
        # Sequential should take longer
        assert report.total_duration >= 0.2

    @pytest.mark.asyncio
    async def test_benchmark_single_pdf(self):
        """Test single PDF file benchmarking."""

        async def mock_convert_func(pdf_file):
            await asyncio.sleep(0.1)
            return {"success": True, "file": pdf_file}

        pdf_files = ["single_file.pdf"]

        report = await self.pdf_benchmark.benchmark_pdf_conversion(
            mock_convert_func, pdf_files, parallel=True
        )

        assert report.total_operations == 1
        assert report.total_duration >= 0.1


class TestGlobalBenchmarkInstances:
    """Test suite for global benchmark instances."""

    def test_global_instances_exist(self):
        """Test that global benchmark instances exist."""
        from source_crate.utils.performance_benchmark import (
            pdf_benchmark,
            search_benchmark,
        )

        assert isinstance(search_benchmark, SearchBenchmark)
        assert isinstance(pdf_benchmark, PDFBenchmark)
        assert isinstance(general_benchmark, PerformanceBenchmark)

        assert search_benchmark.name == "search_performance"
        assert pdf_benchmark.name == "pdf_performance"
        assert general_benchmark.name == "general"

    @pytest.mark.asyncio
    async def test_global_search_benchmark_usage(self):
        """Test using the global search benchmark instance."""
        from source_crate.utils.performance_benchmark import search_benchmark

        async def mock_search(query, category=None):
            await asyncio.sleep(0.05)
            return [{"title": "Test result"}]

        # Clear any existing metrics
        search_benchmark.metrics.clear()

        report = await search_benchmark.benchmark_search_query(
            mock_search, "test", iterations=1
        )

        assert report.total_operations == 1
        assert report.successful_operations == 1


class TestPerformanceUtilities:
    """Test suite for performance utility functions."""

    def test_benchmark_context_manager(self):
        """Test benchmark as context manager."""
        benchmark = PerformanceBenchmark("context_test")

        # Test that we can use benchmark methods
        benchmark.start_benchmark()
        assert benchmark.start_time is not None

        benchmark.end_benchmark()
        assert benchmark.end_time is not None
        assert benchmark.end_time >= benchmark.start_time

    def test_benchmark_print_summary(self):
        """Test benchmark summary printing (basic functionality)."""
        benchmark = PerformanceBenchmark("print_test")

        # Add a test metric
        metric = PerformanceMetric("test_op", 1000.0, 1001.0, 1.0, True)
        benchmark.metrics = [metric]

        report = benchmark.generate_report()

        # This should not raise an exception
        try:
            benchmark.print_summary(report)
        except Exception as e:
            pytest.fail(f"print_summary raised an exception: {e}")

    def test_report_statistics_calculation(self):
        """Test that report statistics are calculated correctly."""
        benchmark = PerformanceBenchmark("stats_test")

        # Add metrics with known values for easy testing
        benchmark.metrics = [
            PerformanceMetric("op", 1000.0, 1001.0, 1.0, True),  # 1 second
            PerformanceMetric("op", 1001.0, 1004.0, 3.0, True),  # 3 seconds
            PerformanceMetric("op", 1004.0, 1006.0, 2.0, False),  # 2 seconds, failed
            PerformanceMetric("op", 1006.0, 1010.0, 4.0, True),  # 4 seconds
        ]

        report = benchmark.generate_report()

        assert report.total_operations == 4
        assert report.successful_operations == 3
        assert report.failed_operations == 1
        assert report.total_duration == 10.0
        assert report.average_duration == 2.5
        assert report.min_duration == 1.0
        assert report.max_duration == 4.0
        assert report.median_duration == 2.5
        assert report.operations_per_second == 0.4
