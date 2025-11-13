# Tests (`tests/`)

This directory contains all tests for the Vocabulator MVP.

## Directory Structure

- **`unit/`** - Unit tests (fast, isolated, no external dependencies)
- **`integration/`** - Integration tests (require external services like LocalStack)
- **`fixtures/`** - Test data and fixtures
  - **`sample_transcripts/`** - Sample student transcripts for testing
- **`mocks/`** - Mock implementations for external services
- **`patterns/`** - Test pattern examples and templates

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_text_analyzer.py
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require external services)
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.aws` - Tests requiring AWS services
- `@pytest.mark.openai` - Tests requiring OpenAI API

Run specific marker:
```bash
pytest -m unit
pytest -m integration
```

## Test-First Development

Follow TDD workflow:
1. Write failing test (RED)
2. Implement to pass (GREEN)
3. Refactor (REFACTOR)

See `_docs/guides/test-first-workflow.md` for details.

## Fixtures

Common fixtures are defined in `conftest.py`:
- `project_root` - Project root directory
- `test_data_dir` - Test fixtures directory
- `temp_env_vars` - Temporary environment variables
- `mock_aws_credentials` - Mock AWS credentials for LocalStack

## Coverage Target

Target: 60-80% code coverage for MVP.

