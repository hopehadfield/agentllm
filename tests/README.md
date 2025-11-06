# Tests

This directory contains the test suite for agentllm.

## Test Structure

### Unit Tests

- **`test_custom_handler.py`** - Tests for the LiteLLM custom handler
- **`test_release_manager.py`** - Tests for the ReleaseManager agent
  - Tests sync `run()` method
  - Tests async `arun()` method (streaming and non-streaming)
  - Validates that streaming returns proper async generators
  - Tests configuration management (Jira token handling)
  - Tests token extraction from natural language
  - Tests configured vs unconfigured user flows

### Integration Tests

- **`test_proxy_integration.py`** - End-to-end tests with real proxy server
  - Tests non-streaming completions through proxy
  - Tests streaming completions through proxy
  - Tests session management
  - Marked with `@pytest.mark.integration`

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run only unit tests (skip integration):
```bash
pytest tests/ -m "not integration"
```

### Run only integration tests:
```bash
pytest tests/ -m integration
```

### Run specific test file:
```bash
pytest tests/test_release_manager.py -v
```

### Run with coverage:
```bash
pytest tests/ --cov=agentllm --cov-report=html
```

## Requirements

Tests require:
- `pytest>=8.4.2`
- `pytest-asyncio>=1.2.0` (for async tests)
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable (for API tests)
- `.env` file with API keys (loaded automatically)

## Test Markers

- `@pytest.mark.integration` - Integration tests that require full proxy setup
- `@pytest.mark.asyncio` - Async tests that use pytest-asyncio
- `@pytest.mark.skipif` - Tests skipped when API keys not available

## Key Tests for Streaming Fix

The following tests specifically validate the streaming fix:

1. **`test_release_manager.py::test_async_streaming`**
   - Validates streaming works end-to-end

2. **`test_release_manager.py::test_streaming_returns_async_generator_not_coroutine`**
   - Validates that `arun(stream=True)` returns async generator, not coroutine
   - This was the root cause of the OpenWebUI streaming bug

3. **`test_proxy_integration.py::test_streaming_completion`**
   - Integration test validating streaming through full proxy stack
