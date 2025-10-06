"""
Performance Benchmarks for SDK Agent Mode.

Measures performance characteristics of key operations:
- Batch processing throughput
- Concurrency scaling
- Memory usage
- Latency characteristics

Run with: pytest tests/benchmarks/ -v --benchmark-only
"""

import pytest
import asyncio
from pathlib import Path
import time
from typing import List
import sys


# Try to import pytest-benchmark
try:
    from pytest_benchmark.fixture import BenchmarkFixture
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False
    BenchmarkFixture = None


pytestmark = pytest.mark.skipif(
    not BENCHMARK_AVAILABLE,
    reason="pytest-benchmark not installed. Install with: pip install pytest-benchmark"
)


class TestBatchProcessingPerformance:
    """Benchmark batch processing performance."""

    @pytest.mark.benchmark
    def test_batch_processing_scaling(self, benchmark, tmp_path):
        """Benchmark batch processing with different file counts."""
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Create test files
        file_counts = [10, 50, 100]

        for count in file_counts:
            files = []
            for i in range(count):
                test_file = tmp_path / f"bench_{count}_{i}.java"
                test_file.write_text(f"// Benchmark file {i}")
                files.append(test_file)

            async def mock_process(file_path: Path):
                # Simulate processing time
                await asyncio.sleep(0.001)
                return {"file": str(file_path)}

            # Benchmark
            result = benchmark(
                lambda: asyncio.run(process_files_in_batches(
                    files,
                    mock_process,
                    batch_size=10,
                    max_concurrency=5
                ))
            )

    @pytest.mark.benchmark
    def test_concurrency_levels(self, benchmark, tmp_path):
        """Benchmark different concurrency levels."""
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Create 50 test files
        files = []
        for i in range(50):
            test_file = tmp_path / f"concurrent_{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        async def mock_process(file_path: Path):
            await asyncio.sleep(0.002)
            return {"file": str(file_path)}

        # Test different concurrency levels
        concurrency_levels = [1, 3, 5, 10]
        results = {}

        for level in concurrency_levels:
            start = time.time()
            asyncio.run(process_files_in_batches(
                files,
                mock_process,
                batch_size=10,
                max_concurrency=level
            ))
            elapsed = time.time() - start
            results[level] = elapsed

        # Verify concurrency improves performance
        # (More concurrency should be faster, up to a point)
        assert results[5] < results[1], "Concurrency should improve performance"

    @pytest.mark.benchmark
    def test_batch_size_impact(self, benchmark, tmp_path):
        """Benchmark impact of batch size on performance."""
        from sdk_agent.tools.batch_processor import process_files_in_batches

        files = []
        for i in range(100):
            test_file = tmp_path / f"batch_{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        async def mock_process(file_path: Path):
            await asyncio.sleep(0.001)
            return {"file": str(file_path)}

        # Test different batch sizes
        batch_sizes = [5, 10, 20, 50]
        results = {}

        for size in batch_sizes:
            start = time.time()
            asyncio.run(process_files_in_batches(
                files,
                mock_process,
                batch_size=size,
                max_concurrency=5
            ))
            elapsed = time.time() - start
            results[size] = elapsed


class TestPathValidationPerformance:
    """Benchmark path validation performance."""

    @pytest.mark.benchmark
    def test_path_validation_speed(self, benchmark, tmp_path):
        """Benchmark path validation performance."""
        from sdk_agent.tools.common import validate_and_expand_path

        # Create test file
        test_file = tmp_path / "validation_test.java"
        test_file.write_text("test")

        # Benchmark validation
        benchmark(
            validate_and_expand_path,
            str(test_file),
            project_root=str(tmp_path),
            must_exist=True
        )

    @pytest.mark.benchmark
    def test_validation_with_many_files(self, benchmark, tmp_path):
        """Benchmark validation with many files."""
        from sdk_agent.tools.common import validate_and_expand_path

        # Create many test files
        files = []
        for i in range(100):
            test_file = tmp_path / f"file{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        def validate_all():
            for f in files:
                validate_and_expand_path(
                    str(f),
                    project_root=str(tmp_path),
                    must_exist=True
                )

        benchmark(validate_all)


class TestMemoryUsage:
    """Test memory usage characteristics."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_large_batch_memory(self, tmp_path):
        """Test memory usage with large batches."""
        from sdk_agent.tools.batch_processor import process_files_in_batches
        import tracemalloc

        # Create 1000 files
        files = []
        for i in range(1000):
            test_file = tmp_path / f"memory_{i}.java"
            test_file.write_text(f"// File {i}" * 100)  # Make files larger
            files.append(test_file)

        async def mock_process(file_path: Path):
            content = file_path.read_text()
            return {"file": str(file_path), "size": len(content)}

        # Measure memory
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        asyncio.run(process_files_in_batches(
            files,
            mock_process,
            batch_size=50,
            max_concurrency=10
        ))

        end_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        memory_used = (end_memory - start_memory) / 1024 / 1024  # MB

        # Memory usage should be reasonable (< 100MB for 1000 files)
        assert memory_used < 100, f"Memory usage too high: {memory_used:.2f} MB"


class TestThroughputMetrics:
    """Measure throughput metrics."""

    @pytest.mark.benchmark
    def test_files_per_second(self, tmp_path):
        """Measure files processed per second."""
        from sdk_agent.tools.batch_processor import process_files_in_batches

        file_counts = [10, 50, 100, 500]
        results = {}

        for count in file_counts:
            files = []
            for i in range(count):
                test_file = tmp_path / f"throughput_{count}_{i}.java"
                test_file.write_text(f"// File {i}")
                files.append(test_file)

            async def mock_process(file_path: Path):
                await asyncio.sleep(0.001)
                return {"file": str(file_path)}

            start = time.time()
            asyncio.run(process_files_in_batches(
                files,
                mock_process,
                batch_size=20,
                max_concurrency=10
            ))
            elapsed = time.time() - start

            throughput = count / elapsed if elapsed > 0 else 0
            results[count] = {
                "elapsed": elapsed,
                "throughput": throughput
            }

        # Print results
        print("\nThroughput Results:")
        for count, metrics in results.items():
            print(f"  {count} files: {metrics['throughput']:.2f} files/sec "
                  f"({metrics['elapsed']:.3f}s total)")


class TestLatencyCharacteristics:
    """Measure latency characteristics."""

    @pytest.mark.benchmark
    def test_processing_latency_distribution(self, tmp_path):
        """Measure latency distribution for file processing."""
        from sdk_agent.tools.batch_processor import process_files_in_batches
        import statistics

        files = []
        for i in range(100):
            test_file = tmp_path / f"latency_{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        latencies = []

        async def mock_process(file_path: Path):
            start = time.perf_counter()
            await asyncio.sleep(0.001)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)  # Convert to ms
            return {"file": str(file_path)}

        asyncio.run(process_files_in_batches(
            files,
            mock_process,
            batch_size=10,
            max_concurrency=5
        ))

        # Calculate statistics
        mean_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile

        print(f"\nLatency Statistics:")
        print(f"  Mean: {mean_latency:.3f} ms")
        print(f"  Median: {median_latency:.3f} ms")
        print(f"  P95: {p95_latency:.3f} ms")
        print(f"  P99: {p99_latency:.3f} ms")


class TestScalabilityLimits:
    """Test scalability limits and breaking points."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_maximum_concurrent_operations(self, tmp_path):
        """Test system behavior at maximum concurrency."""
        from sdk_agent.tools.batch_processor import process_files_in_batches

        files = []
        for i in range(100):
            test_file = tmp_path / f"concurrent_{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        async def mock_process(file_path: Path):
            await asyncio.sleep(0.002)
            return {"file": str(file_path)}

        # Test increasing concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        results = {}

        for level in concurrency_levels:
            try:
                start = time.time()
                asyncio.run(process_files_in_batches(
                    files,
                    mock_process,
                    batch_size=10,
                    max_concurrency=level
                ))
                elapsed = time.time() - start
                results[level] = {
                    "success": True,
                    "elapsed": elapsed,
                    "throughput": len(files) / elapsed
                }
            except Exception as e:
                results[level] = {
                    "success": False,
                    "error": str(e)
                }

        # Print scalability results
        print("\nScalability Results:")
        for level, result in results.items():
            if result["success"]:
                print(f"  Concurrency {level}: {result['throughput']:.2f} files/sec")
            else:
                print(f"  Concurrency {level}: FAILED - {result['error']}")


# Performance regression tests
class TestPerformanceRegression:
    """Detect performance regressions."""

    @pytest.mark.benchmark
    def test_baseline_batch_processing(self, benchmark, tmp_path):
        """
        Baseline benchmark for batch processing.

        This test establishes performance baseline.
        Future runs should not be significantly slower.
        """
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Standard test: 50 files, batch_size=10, concurrency=5
        files = []
        for i in range(50):
            test_file = tmp_path / f"baseline_{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        async def mock_process(file_path: Path):
            await asyncio.sleep(0.001)
            return {"file": str(file_path)}

        result = benchmark(
            lambda: asyncio.run(process_files_in_batches(
                files,
                mock_process,
                batch_size=10,
                max_concurrency=5
            ))
        )

        # Baseline should complete in reasonable time (< 5 seconds)
        # Adjust based on your system's performance
        assert benchmark.stats.stats.mean < 5.0, "Performance regression detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
