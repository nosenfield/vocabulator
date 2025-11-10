# Testing Standards

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [FastAPI Patterns](fastapi-patterns.md)

---

## Test Organization

**Structure tests to mirror source code:**

```
tests/
├── unit/                      # Fast, isolated tests
│   ├── test_student_profile.py
│   ├── test_vocabulary_extraction.py
│   └── test_openai_client.py
├── integration/               # Tests with external dependencies
│   ├── test_api_endpoints.py
│   ├── test_batch_processing.py
│   └── test_dynamodb_operations.py
├── fixtures/                  # Test data
│   ├── sample_transcripts/
│   └── sample_profiles.json
├── mocks/                     # Mock implementations
│   ├── mock_openai.py
│   └── mock_aws.py
└── conftest.py               # Shared pytest fixtures
```

---

## Test-First Development (TDD)

**Write tests before implementation:**

```python
# Step 1: Write failing test (RED)
def test_extract_vocabulary_from_transcript():
    """Test vocabulary extraction from sample transcript."""
    # Arrange
    text = "Today we learned about photosynthesis and cellular respiration."
    expected_words = ["learned", "photosynthesis", "cellular", "respiration"]

    # Act
    result = extract_vocabulary(text)

    # Assert
    assert len(result) >= 4
    assert all(word in result for word in expected_words)
    assert "today" not in result  # Common word excluded
    assert "the" not in result    # Stopword excluded

# Step 2: Implement to make test pass (GREEN)
def extract_vocabulary(text: str) -> List[str]:
    # Implementation...
    pass

# Step 3: Refactor (REFACTOR)
# Improve code quality while keeping tests green
```

---

## Pytest Best Practices

**Use fixtures for setup/teardown:**

```python
import pytest
from typing import Generator

@pytest.fixture
def dynamodb_table() -> Generator:
    """Create DynamoDB table for testing."""
    table = create_test_table("test-students")
    yield table
    table.delete()  # Cleanup

@pytest.fixture
def sample_student():
    """Provide sample student data."""
    return {
        "student_id": "STU-001",
        "grade_level": 7,
        "vocabulary_list": [
            {"word": "analyze", "count": 3},
            {"word": "hypothesis", "count": 1}
        ]
    }

def test_create_student_profile(dynamodb_table, sample_student):
    """Test creating student profile."""
    repo = StudentRepository(dynamodb_table.name)
    repo.create(sample_student)

    # Verify
    result = repo.get("STU-001")
    assert result["student_id"] == "STU-001"
    assert result["grade_level"] == 7
```

**Parametrize tests for multiple cases:**

```python
@pytest.mark.parametrize("grade,expected_words", [
    (6, ["analyze", "compare", "describe"]),
    (7, ["analyze", "evaluate", "synthesize"]),
    (8, ["analyze", "critique", "hypothesize"])
])
def test_grade_appropriate_vocabulary(grade, expected_words):
    """Test vocabulary recommendations match grade level."""
    recommendations = generate_recommendations(grade)
    assert all(word in recommendations for word in expected_words)
```

---

## Mocking External Services

**Mock OpenAI API responses:**

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with sample responses."""
    mock = AsyncMock()
    mock.complete.return_value = json.dumps({
        "words": [
            {"word": "photosynthesis", "count": 2},
            {"word": "chloroplast", "count": 1}
        ]
    })
    return mock

@pytest.mark.asyncio
async def test_extract_vocabulary_calls_openai(mock_openai_client):
    """Test vocabulary extraction uses OpenAI API."""
    with patch("src.processing.text_analyzer.openai_client", mock_openai_client):
        result = await extract_vocabulary("Sample text about photosynthesis")

        # Verify API was called
        assert mock_openai_client.complete.called
        assert len(result) == 2
        assert result[0]["word"] == "photosynthesis"
```

**Mock AWS services with moto:**

```python
import boto3
from moto import mock_dynamodb, mock_s3

@mock_dynamodb
def test_student_repository_crud():
    """Test student repository CRUD operations."""
    # Create mock DynamoDB table
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="test-students",
        KeySchema=[{"AttributeName": "student_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "student_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )

    # Test repository operations
    repo = StudentRepository("test-students")
    repo.create({"student_id": "STU-001", "grade_level": 7})

    result = repo.get("STU-001")
    assert result["grade_level"] == 7
```

---

## Test Coverage

**Aim for 60-80% coverage:**

```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Fail if coverage below threshold
pytest tests/ --cov=src --cov-fail-under=60
```

**Coverage configuration (.coveragerc):**
```ini
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for async test patterns
- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for TestClient usage
- **OpenAI Integration**: See [openai-integration.md](openai-integration.md) for mocking API calls
- **AWS Services**: See [aws-services.md](aws-services.md) for mocking AWS with moto
- **Test-First Workflow**: See [../guides/test-first-workflow.md](../guides/test-first-workflow.md)

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [FastAPI Patterns](fastapi-patterns.md)
- [Test-First Workflow](../guides/test-first-workflow.md)
