# Performance Benchmarks

Comprehensive performance benchmarks for SDK Agent mode.

## Prerequisites

Install pytest-benchmark:

```bash
pip install pytest-benchmark
```

## Running Benchmarks

### Run All Benchmarks

```bash
pytest tests/benchmarks/ -v --benchmark-only
```

### Run Specific Benchmark

```bash
pytest tests/benchmarks/test_performance.py::TestBatchProcessingPerformance -v --benchmark-only
```

### Generate HTML Report

```bash
pytest tests/benchmarks/ --benchmark-only --benchmark-autosave --benchmark-save=baseline
```

### Compare with Baseline

```bash
# Run new benchmarks and compare
pytest tests/benchmarks/ --benchmark-only --benchmark-compare=baseline
```

## Benchmark Categories

### 1. Batch Processing Performance
- **File count scaling**: 10, 50, 100, 500, 1000 files
- **Concurrency levels**: 1, 3, 5, 10, 20, 50 concurrent operations
- **Batch sizes**: 5, 10, 20, 50 files per batch

**Expected Results:**
- 10 files: < 0.5s
- 50 files: < 1.5s
- 100 files: < 2.5s
- 500 files: < 10s

### 2. Path Validation Performance
- Single file validation: < 1ms
- 100 files validation: < 50ms

### 3. Memory Usage
- 1000 files: < 100MB memory usage
- Should scale linearly with file count

### 4. Throughput Metrics
- **Target**: 50-100 files/second with concurrency=10
- Actual throughput varies by system

### 5. Latency Distribution
- **Mean**: ~1-2ms
- **P95**: < 5ms
- **P99**: < 10ms

## Performance Targets

| Metric | Target | Acceptable | Warning |
|--------|--------|------------|---------|
| **50 files** | < 1s | < 2s | > 2s |
| **100 files** | < 2s | < 4s | > 4s |
| **Throughput** | 100 files/s | 50 files/s | < 50 files/s |
| **Memory (1K files)** | < 50MB | < 100MB | > 100MB |
| **P95 Latency** | < 3ms | < 5ms | > 5ms |

## Interpreting Results

### Good Performance
```
test_batch_processing_scaling: 1.23s (mean)
test_concurrency_levels: Shows improvement with concurrency
test_memory: < 50MB for 1000 files
```

### Performance Regression
```
test_batch_processing_scaling: 5.45s (mean)  ⚠️ REGRESSION
test_memory: > 150MB for 1000 files          ⚠️ MEMORY LEAK?
```

## Optimization Tips

### If Batch Processing is Slow
1. **Increase `max_concurrency`** (try 10-20)
2. **Adjust `batch_size`** (try 20-50)
3. **Check for I/O bottlenecks**

### If Memory Usage is High
1. **Decrease `batch_size`**
2. **Process files in smaller chunks**
3. **Check for memory leaks in process functions**

### If Concurrency Doesn't Help
1. **Check for GIL contention** (use ProcessPool instead)
2. **Verify I/O operations are truly async**
3. **Profile with `cProfile` or `py-spy`**

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/benchmark.yml
- name: Run Performance Benchmarks
  run: |
    pytest tests/benchmarks/ --benchmark-only --benchmark-autosave
    pytest tests/benchmarks/ --benchmark-compare --benchmark-compare-fail=mean:5%
```

This fails the build if performance degrades by more than 5%.

## Profiling

For detailed profiling:

```bash
# CPU profiling
python -m cProfile -o profile.stats -m pytest tests/benchmarks/ --benchmark-disable

# Memory profiling
python -m memory_profiler tests/benchmarks/test_performance.py

# Line profiling
kernprof -l -v tests/benchmarks/test_performance.py
```

## Troubleshooting

### Benchmarks Too Slow
- Reduce file counts in tests
- Skip expensive tests: `pytest -m "benchmark and not slow"`

### Inconsistent Results
- Close other applications
- Run multiple times and use median: `--benchmark-sort=median`
- Increase warmup rounds: `--benchmark-warmup-iterations=5`

### Memory Issues
- Reduce test file counts
- Run tests sequentially: `pytest -n 0`
- Monitor with: `pytest --memprof`

## Advanced Usage

### Custom Benchmark Configuration

Create `pytest.ini`:

```ini
[pytest]
markers =
    benchmark: Performance benchmark tests
    slow: Slow running tests (> 5s)
    expensive: Tests that cost money (API calls)

addopts =
    --benchmark-warmup=on
    --benchmark-warmup-iterations=3
    --benchmark-min-rounds=5
```

### Continuous Benchmarking

Track performance over time:

```bash
# Save each run
pytest tests/benchmarks/ --benchmark-autosave --benchmark-name=short

# Generate history
pytest-benchmark compare --group-by=name --histogram
```

## References

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [Python profiling tools](https://docs.python.org/3/library/profile.html)
- [Memory profiler](https://pypi.org/project/memory-profiler/)
