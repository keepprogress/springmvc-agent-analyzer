# Test Suite

## Overview

Comprehensive test suite for SpringMVC Agent Analyzer covering:
- Unit tests for core components (graph, schema, utilities)
- Integration tests for agents and MCP server
- Benchmarks for performance validation

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run Specific Test File

```bash
pytest tests/unit/test_graph_schema.py
```

### Run with Coverage

```bash
pytest --cov=agents --cov=core --cov=graph --cov=mcp --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Verbose

```bash
pytest -v
```

### Run Tests Matching Pattern

```bash
pytest -k "test_node"
```

## Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_graph_schema.py       # Graph schema tests
│   ├── test_graph_builder.py      # Graph builder tests
│   └── ...
├── integration/             # Integration tests (slower, require dependencies)
│   ├── test_controller_agent.py   # Agent integration tests
│   └── test_mcp_server.py         # MCP server tests
├── fixtures/                # Test data and fixtures
└── benchmark_controller.py  # Performance benchmarks
```

## Test Markers

Tests are marked with categories:

- `@pytest.mark.unit`: Fast unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Tests taking > 1 second
- `@pytest.mark.requires_api`: Tests requiring Anthropic API key

Run only unit tests:
```bash
pytest -m unit
```

Skip slow tests:
```bash
pytest -m "not slow"
```

## Writing Tests

### Unit Test Template

```python
import pytest
from your_module import YourClass


class TestYourClass:
    """Test YourClass functionality."""

    def test_something(self):
        """Test that something works."""
        obj = YourClass()
        result = obj.method()
        assert result == expected
```

### Integration Test Template

```python
import pytest


@pytest.mark.integration
@pytest.mark.requires_api
async def test_agent_analysis():
    """Test full agent analysis pipeline."""
    # Setup
    agent = create_agent()

    # Execute
    result = await agent.analyze("test_file.java")

    # Verify
    assert result["confidence"] > 0.7
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage for core modules
- **Integration Tests**: Cover all major user workflows
- **Benchmarks**: Validate performance targets

## Continuous Integration

Tests run automatically on:
- Every commit to main branch
- Every pull request
- Nightly builds

## Troubleshooting

### API Key Issues

Set environment variable:
```bash
export ANTHROPIC_API_KEY=your_key
```

Or create `.env` file:
```
ANTHROPIC_API_KEY=your_key
```

### Import Errors

Install in development mode:
```bash
pip install -e ".[dev]"
```

### Slow Tests

Skip slow tests during development:
```bash
pytest -m "not slow"
```

## Performance Benchmarks

Run performance benchmarks:
```bash
python tests/benchmark_controller.py
```

See [README_BENCHMARK.md](README_BENCHMARK.md) for details.
