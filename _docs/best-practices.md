# Vocabulator Best Practices Guide

**Project:** Personalized Vocabulary Recommendation Engine for Middle School Students
**Version:** 1.0.0 (MVP)
**Last Updated:** 2025-11-10

---

## Overview

This document defines best practices for building modular, scalable, and maintainable Python applications with our specific tech stack: FastAPI, OpenAI SDK, AWS services (Lambda, Fargate, DynamoDB, S3), and pytest.

These practices ensure code quality, security, testability, and cost-efficiency throughout the development lifecycle.

---

## Table of Contents

1. [Python Development Standards](#python-development-standards)
2. [FastAPI Best Practices](#fastapi-best-practices)
3. [OpenAI API Integration](#openai-api-integration)
4. [AWS Services Best Practices](#aws-services-best-practices)
5. [Testing Standards](#testing-standards)
6. [Security & Privacy](#security--privacy)
7. [Performance Optimization](#performance-optimization)
8. [Code Organization](#code-organization)
9. [Error Handling](#error-handling)
10. [Logging & Monitoring](#logging--monitoring)
11. [Documentation Standards](#documentation-standards)
12. [Git Workflow](#git-workflow)

---

## Python Development Standards

### Code Style & Formatting

**Use automated formatters and linters:**

```bash
# Format code with black (line length: 88)
black src/ tests/

# Lint with ruff (replaces flake8, isort, pylint)
ruff check src/ tests/

# Type checking with mypy
mypy src/ --strict
```

**Configuration (pyproject.toml):**
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "N", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

**Style Guidelines:**
- ✅ Use type hints for all function signatures
- ✅ Write docstrings for all public functions (Google or NumPy style)
- ✅ Use descriptive variable names (no single letters except loop counters)
- ✅ Prefer f-strings over `.format()` or `%` formatting
- ✅ Use `pathlib.Path` instead of `os.path` for file operations
- ❌ Avoid `import *` (explicit imports only)
- ❌ Avoid mutable default arguments (`def func(items=[]): ...`)

**Example:**
```python
from typing import List, Optional
from pathlib import Path

def extract_vocabulary(
    text: str,
    min_word_length: int = 3,
    exclude_stopwords: bool = True
) -> List[str]:
    """Extract unique vocabulary words from text.

    Args:
        text: Input text to analyze
        min_word_length: Minimum word length to include
        exclude_stopwords: Whether to exclude common stopwords

    Returns:
        List of unique vocabulary words, lowercase and sorted

    Raises:
        ValueError: If text is empty or min_word_length < 1
    """
    if not text:
        raise ValueError("Text cannot be empty")
    # Implementation...
```

---

### Dependency Management

**Pin dependencies for reproducibility:**

```txt
# requirements.txt - Production dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
openai==1.3.5
boto3==1.28.85
httpx==0.25.1

# requirements-dev.txt - Development dependencies
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
black==23.11.0
ruff==0.1.5
mypy==1.7.0
```

**Best practices:**
- ✅ Use exact version pins for production (`==`)
- ✅ Separate dev dependencies from production
- ✅ Update dependencies regularly (monthly security review)
- ✅ Use `pip-tools` or `poetry` for dependency resolution
- ❌ Don't commit virtual environment (`venv/` in `.gitignore`)

---

### Virtual Environments

**Always use virtual environments:**

```bash
# Create virtual environment
python -m venv venv

# Activate (Unix/MacOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Freeze dependencies
pip freeze > requirements-freeze.txt
```

---

### Async/Await Patterns

**Use async for I/O-bound operations:**

```python
import asyncio
from typing import List
import httpx

# ✅ Good - Async for I/O operations
async def fetch_multiple_definitions(words: List[str]) -> List[str]:
    """Fetch definitions for multiple words concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_definition(client, word) for word in words]
        return await asyncio.gather(*tasks)

async def fetch_definition(client: httpx.AsyncClient, word: str) -> str:
    response = await client.get(f"https://api.dictionary.com/{word}")
    return response.json()["definition"]

# ❌ Bad - Sync in async function (blocks event loop)
async def bad_fetch():
    import time
    time.sleep(5)  # Blocks event loop!
    # Use: await asyncio.sleep(5) instead
```

**When to use async:**
- ✅ API calls (OpenAI, external services)
- ✅ Database queries (DynamoDB, S3)
- ✅ Multiple I/O operations that can run concurrently
- ❌ CPU-bound tasks (use multiprocessing instead)
- ❌ Simple CRUD operations with no concurrency benefit

---

## FastAPI Best Practices

### Application Structure

**Organize by feature, not by type:**

```python
# ✅ Good - Feature-based organization
src/api/
├── main.py              # FastAPI app initialization
├── routes/
│   ├── upload.py        # Upload-related endpoints
│   ├── profiles.py      # Profile-related endpoints
│   └── recommendations.py
├── models/
│   ├── requests.py      # All request models
│   └── responses.py     # All response models
└── middleware/
    ├── auth.py
    └── logging.py

# ❌ Bad - Type-based organization (hard to scale)
src/api/
├── routes.py            # All routes in one file
├── models.py            # All models in one file
└── utils.py             # Grab bag of functions
```

---

### Dependency Injection

**Use FastAPI's dependency injection for shared resources:**

```python
from fastapi import Depends, FastAPI
from typing import Annotated

app = FastAPI()

# Define dependencies
def get_db_client():
    """Provide DynamoDB client."""
    client = DynamoDBClient()
    try:
        yield client
    finally:
        client.close()

def get_current_user(api_key: str = Header(...)):
    """Validate API key and return user."""
    # Validation logic
    return user

# Use in endpoints
@app.post("/api/v1/transcripts/upload")
async def upload_transcript(
    request: TranscriptUploadRequest,
    db: Annotated[DynamoDBClient, Depends(get_db_client)],
    user: Annotated[User, Depends(get_current_user)]
):
    """Upload student transcript."""
    # db and user are automatically injected
    return await process_upload(request, db, user)
```

**Benefits:**
- Automatic cleanup (context managers)
- Easy mocking in tests
- Reusable across endpoints
- Clear dependency hierarchy

---

### Request/Response Models

**Use Pydantic for validation:**

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date

class TranscriptUploadRequest(BaseModel):
    """Request model for transcript upload."""

    student_id: str = Field(
        ...,
        pattern=r"^STU-\d{3}$",
        description="Student identifier (format: STU-001)",
        examples=["STU-001"]
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Transcript text content"
    )
    session_date: date = Field(
        ...,
        description="Date of the recorded session"
    )
    grade_level: int = Field(
        ...,
        ge=6,
        le=8,
        description="Student grade level (6-8)"
    )

    @field_validator("text")
    @classmethod
    def text_must_contain_words(cls, v: str) -> str:
        """Validate text contains actual words."""
        if not any(c.isalpha() for c in v):
            raise ValueError("Text must contain alphabetic characters")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "STU-001",
                "text": "Today we learned about photosynthesis...",
                "session_date": "2025-11-10",
                "grade_level": 7
            }
        }
```

**Best practices:**
- ✅ Use `Field()` for validation constraints and documentation
- ✅ Add `description` and `examples` for OpenAPI docs
- ✅ Use custom validators for complex logic
- ✅ Define `Config.json_schema_extra` for clear examples
- ❌ Don't put business logic in models (keep them data-only)

---

### Error Handling

**Use HTTPException with clear messages:**

```python
from fastapi import HTTPException, status

@app.get("/api/v1/students/{student_id}/profile")
async def get_student_profile(student_id: str):
    """Retrieve student vocabulary profile."""

    # Validate input format
    if not student_id.startswith("STU-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_student_id",
                "message": "Student ID must start with 'STU-'",
                "student_id": student_id
            }
        )

    # Check if exists
    profile = await student_repo.get(student_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "student_not_found",
                "message": f"No profile found for student {student_id}",
                "student_id": student_id
            }
        )

    return profile
```

**Custom exception handler:**

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError as 400 Bad Request."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "path": request.url.path
        }
    )
```

---

### Testing FastAPI Applications

**Use TestClient for endpoint testing:**

```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_upload_transcript_success():
    """Test successful transcript upload."""
    response = client.post(
        "/api/v1/transcripts/upload",
        json={
            "student_id": "STU-001",
            "text": "Today we learned about photosynthesis...",
            "session_date": "2025-11-10",
            "grade_level": 7
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "STU-001"
    assert "profile_url" in data

def test_upload_transcript_invalid_student_id():
    """Test upload with invalid student ID format."""
    response = client.post(
        "/api/v1/transcripts/upload",
        json={
            "student_id": "INVALID",
            "text": "Sample text",
            "session_date": "2025-11-10",
            "grade_level": 7
        }
    )

    assert response.status_code == 422  # Validation error
    assert "student_id" in response.json()["detail"][0]["loc"]
```

---

## OpenAI API Integration

### Client Configuration

**Create reusable, configured client:**

```python
from openai import AsyncOpenAI
import os
from typing import Optional

class OpenAIClient:
    """Wrapper for OpenAI API with error handling and retry logic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            max_retries=max_retries,
            timeout=timeout
        )
        self.cost_tracker = CostTracker()

    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Send completion request with error handling."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Track costs
            self.cost_tracker.log(
                model=model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
```

---

### Prompt Engineering

**Use structured prompts with templates:**

```python
from jinja2 import Template

VOCABULARY_EXTRACTION_PROMPT = Template("""
You are a vocabulary extraction specialist for middle school education.

TASK: Extract academically significant words from the student text below.

INSTRUCTIONS:
1. Extract words that demonstrate vocabulary usage
2. Exclude common function words (the, a, an, is, are)
3. Exclude words below 3rd grade reading level
4. For each word, provide:
   - Lemmatized form (base form)
   - Usage count
   - One example sentence from the text

STUDENT TEXT:
{{ text }}

OUTPUT FORMAT: Valid JSON only
{
  "words": [
    {
      "word": "analyze",
      "count": 3,
      "example": "We need to analyze the data carefully."
    }
  ]
}
""")

async def extract_vocabulary(text: str) -> list[dict]:
    """Extract vocabulary from text using GPT-4o-mini."""
    prompt = VOCABULARY_EXTRACTION_PROMPT.render(text=text)

    response = await openai_client.complete(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a vocabulary expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower temperature for consistency
        max_tokens=2000
    )

    return json.loads(response)["words"]
```

**Best practices:**
- ✅ Use templates (Jinja2) for reusable prompts
- ✅ Specify output format clearly (JSON preferred)
- ✅ Use lower temperature (0.1-0.3) for consistent extraction
- ✅ Provide clear examples in the prompt
- ✅ Include validation instructions
- ❌ Don't rely on exact output format (parse defensively)

---

### Cost Optimization

**Strategies to minimize OpenAI API costs:**

```python
class CostOptimizer:
    """Optimize OpenAI API usage for cost efficiency."""

    def __init__(self):
        self.cache = {}  # Response cache

    async def extract_vocabulary_batch(
        self,
        texts: list[str],
        batch_size: int = 50
    ) -> list[dict]:
        """Process multiple texts in batches to reduce API calls."""

        # Batch texts together
        batches = [
            texts[i:i + batch_size]
            for i in range(0, len(texts), batch_size)
        ]

        results = []
        for batch in batches:
            # Single API call for multiple texts
            combined_text = "\n---NEXT_TEXT---\n".join(batch)
            response = await self.extract_vocabulary(combined_text)
            results.extend(response)

        return results

    async def extract_with_cache(
        self,
        text: str,
        cache_ttl: int = 3600
    ) -> list[dict]:
        """Extract vocabulary with response caching."""
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < cache_ttl:
                return cached_result

        # Make API call
        result = await self.extract_vocabulary(text)
        self.cache[cache_key] = (result, time.time())
        return result
```

**Cost reduction techniques:**
- ✅ Use GPT-4o-mini for simple tasks (10x cheaper than GPT-4o)
- ✅ Batch multiple requests when possible
- ✅ Cache responses for identical inputs
- ✅ Use shorter prompts (fewer input tokens)
- ✅ Set `max_tokens` to minimum needed
- ✅ Monitor daily spending with alarms
- ❌ Don't use GPT-4o for tasks GPT-4o-mini can handle

---

### Error Handling

**Handle rate limits and transient errors:**

```python
import asyncio
from openai import RateLimitError, APIError

async def call_openai_with_retry(
    func,
    *args,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    **kwargs
):
    """Call OpenAI API with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            wait_time = backoff_factor ** attempt
            logger.warning(
                f"Rate limit hit, retrying in {wait_time}s "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            await asyncio.sleep(wait_time)

        except APIError as e:
            if attempt == max_retries - 1:
                raise

            logger.warning(f"API error: {e}, retrying...")
            await asyncio.sleep(backoff_factor ** attempt)
```

---

## AWS Services Best Practices

### boto3 Client Management

**Use session and resource clients appropriately:**

```python
import boto3
from botocore.config import Config
from typing import Optional

class AWSClientFactory:
    """Factory for creating configured AWS clients."""

    def __init__(self, region: str = "us-east-1"):
        self.config = Config(
            region_name=region,
            retries={"max_attempts": 3, "mode": "adaptive"},
            max_pool_connections=50
        )
        self.session = boto3.Session()

    def get_dynamodb_client(self):
        """Get DynamoDB client with retry configuration."""
        return self.session.client("dynamodb", config=self.config)

    def get_s3_client(self):
        """Get S3 client with retry configuration."""
        return self.session.client("s3", config=self.config)

# Singleton instance
aws_clients = AWSClientFactory()
```

**Best practices:**
- ✅ Reuse clients (don't create new client per request)
- ✅ Configure retries explicitly
- ✅ Use connection pooling for high throughput
- ✅ Use resource for higher-level operations, client for low-level
- ❌ Don't hardcode credentials (use IAM roles)

---

### DynamoDB Patterns

**Efficient query and scan patterns:**

```python
from typing import List, Optional
from boto3.dynamodb.conditions import Key, Attr

class StudentRepository:
    """Repository for student profile operations."""

    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    async def get_by_id(self, student_id: str) -> Optional[dict]:
        """Get student profile by ID (efficient query)."""
        try:
            response = self.table.get_item(
                Key={"student_id": student_id},
                ConsistentRead=False  # Eventually consistent (cheaper)
            )
            return response.get("Item")
        except ClientError as e:
            logger.error(f"Error fetching student {student_id}: {e}")
            return None

    async def get_by_grade(
        self,
        grade_level: int,
        limit: int = 100
    ) -> List[dict]:
        """Get students by grade level (GSI query)."""
        response = self.table.query(
            IndexName="grade_level-proficiency_score-index",
            KeyConditionExpression=Key("grade_level").eq(grade_level),
            Limit=limit
        )
        return response.get("Items", [])

    async def batch_get(self, student_ids: List[str]) -> List[dict]:
        """Get multiple students in one request (batch operation)."""
        response = boto3.resource("dynamodb").batch_get_item(
            RequestItems={
                self.table.name: {
                    "Keys": [{"student_id": sid} for sid in student_ids]
                }
            }
        )
        return response["Responses"][self.table.name]

    async def update_vocabulary(
        self,
        student_id: str,
        new_words: List[dict]
    ):
        """Update student vocabulary list atomically."""
        self.table.update_item(
            Key={"student_id": student_id},
            UpdateExpression="SET vocabulary_list = list_append(vocabulary_list, :words)",
            ExpressionAttributeValues={":words": new_words},
            ReturnValues="UPDATED_NEW"
        )
```

**Best practices:**
- ✅ Use `get_item` for single-item retrieval (not `query`)
- ✅ Use GSI for queries on non-key attributes
- ✅ Use batch operations for multiple items (up to 25)
- ✅ Use eventually consistent reads when possible (50% cheaper)
- ✅ Use `UpdateExpression` for atomic updates
- ❌ Avoid `scan` operations (expensive and slow)
- ❌ Don't use strongly consistent reads unless necessary

---

### S3 Operations

**Efficient file operations:**

```python
import boto3
from pathlib import Path
from typing import BinaryIO, Optional

class S3Client:
    """Client for S3 operations with best practices."""

    def __init__(self, bucket_name: str):
        self.s3 = boto3.client("s3")
        self.bucket = bucket_name

    async def upload_file(
        self,
        file_path: Path,
        s3_key: str,
        content_type: Optional[str] = None
    ):
        """Upload file to S3 with metadata."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        # Server-side encryption by default
        extra_args["ServerSideEncryption"] = "AES256"

        self.s3.upload_file(
            str(file_path),
            self.bucket,
            s3_key,
            ExtraArgs=extra_args
        )

    async def upload_large_file(
        self,
        file_path: Path,
        s3_key: str,
        part_size: int = 10 * 1024 * 1024  # 10MB parts
    ):
        """Upload large file using multipart upload."""
        config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=part_size,
            multipart_chunksize=part_size
        )

        self.s3.upload_file(
            str(file_path),
            self.bucket,
            s3_key,
            Config=config
        )

    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> str:
        """Generate temporary download URL."""
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expiration
        )

    async def list_files(self, prefix: str) -> List[str]:
        """List all files with given prefix (handles pagination)."""
        files = []
        paginator = self.s3.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if "Contents" in page:
                files.extend([obj["Key"] for obj in page["Contents"]])

        return files
```

**Best practices:**
- ✅ Use multipart upload for files > 5MB
- ✅ Enable server-side encryption by default
- ✅ Use presigned URLs for temporary access (not public buckets)
- ✅ Use pagination for listing large directories
- ✅ Set lifecycle policies for automatic cleanup
- ❌ Don't store sensitive data without encryption
- ❌ Don't make buckets public

---

### Lambda Best Practices

**Optimize for cold starts and performance:**

```python
import os
import boto3
from typing import Any, Dict

# ✅ Initialize clients outside handler (reused across invocations)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STUDENT_TABLE"])
openai_client = OpenAIClient()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler."""

    # ✅ Extract environment variables once
    log_level = os.getenv("LOG_LEVEL", "INFO")

    try:
        # Business logic
        student_id = event["pathParameters"]["student_id"]
        profile = table.get_item(Key={"student_id": student_id})

        return {
            "statusCode": 200,
            "body": json.dumps(profile["Item"])
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing parameter: {e}"})
        }

    except Exception as e:
        logger.exception("Unexpected error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

**Best practices:**
- ✅ Initialize clients outside handler (cold start optimization)
- ✅ Use environment variables for configuration
- ✅ Set appropriate memory (512MB-1GB for most workloads)
- ✅ Use Lambda layers for shared dependencies
- ✅ Keep deployment package small (< 50MB)
- ✅ Use provisioned concurrency for latency-sensitive functions
- ❌ Don't initialize clients inside handler
- ❌ Don't use recursion (risk of runaway costs)

---

## Testing Standards

### Test Organization

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

### Test-First Development (TDD)

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

### Pytest Best Practices

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

### Mocking External Services

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

### Test Coverage

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

## Security & Privacy

### COPPA Compliance

**Implement anonymous processing:**

```python
from typing import Pattern
import re

STUDENT_ID_PATTERN: Pattern = re.compile(r"^STU-\d{3}$")

def validate_anonymous_student_id(student_id: str) -> bool:
    """Ensure student ID is anonymous (no PII)."""
    if not STUDENT_ID_PATTERN.match(student_id):
        raise ValueError("Invalid student ID format")

    # ❌ Reject IDs that look like names
    if any(char.isalpha() and char.isupper() for char in student_id[4:]):
        raise ValueError("Student ID appears to contain name")

    return True

# ❌ Never log or store PII
logger.info(f"Processing student: {mask_student_id(student_id)}")

def mask_student_id(student_id: str) -> str:
    """Mask student ID for logging."""
    return f"STU-***{student_id[-2:]}"
```

**Data retention policies:**

```python
# DynamoDB TTL for auto-expiration
recommendation_item = {
    "student_id": "STU-001",
    "recommendation_date": "2025-11-10",
    "words": [...],
    "expires_at": int(time.time()) + (30 * 24 * 3600)  # 30 days
}

# S3 lifecycle policy (in CloudFormation)
# Automatically delete transcripts after 90 days
```

---

### Secrets Management

**Never hardcode secrets:**

```python
import os
from typing import Optional

# ✅ Good - Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable required")

# ✅ Better - AWS Secrets Manager (production)
import boto3
import json

def get_secret(secret_name: str) -> dict:
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

# ❌ Bad - Hardcoded secrets
# OPENAI_API_KEY = "sk-proj-abcd1234..."  # NEVER DO THIS!
```

**.env for development:**
```bash
# .env (gitignored)
OPENAI_API_KEY=sk-proj-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

**.env.example for documentation:**
```bash
# .env.example (committed to git)
OPENAI_API_KEY=your_openai_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
```

---

### Input Validation

**Sanitize all user inputs:**

```python
from typing import Optional
import bleach

def sanitize_text_input(text: str, max_length: int = 50000) -> str:
    """Sanitize user-provided text input."""
    # Remove potential XSS
    text = bleach.clean(text, tags=[], strip=True)

    # Limit length
    if len(text) > max_length:
        raise ValueError(f"Text exceeds maximum length of {max_length}")

    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char == "\n")

    return text.strip()

# Use in API endpoints
@app.post("/api/v1/transcripts/upload")
async def upload_transcript(request: TranscriptUploadRequest):
    sanitized_text = sanitize_text_input(request.text)
    # Process sanitized text...
```

---

### IAM Least Privilege

**Grant minimum permissions required:**

```yaml
# CloudFormation IAM policy
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    Policies:
      - PolicyName: StudentProfileAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            # ✅ Specific table access only
            - Effect: Allow
              Action:
                - dynamodb:GetItem
                - dynamodb:PutItem
                - dynamodb:UpdateItem
              Resource: !GetAtt StudentProfilesTable.Arn

            # ✅ Specific S3 prefix only
            - Effect: Allow
              Action:
                - s3:GetObject
                - s3:PutObject
              Resource: !Sub "${TranscriptsBucket.Arn}/transcripts/*"

            # ✅ CloudWatch Logs (standard)
            - Effect: Allow
              Action:
                - logs:CreateLogGroup
                - logs:CreateLogStream
                - logs:PutLogEvents
              Resource: !Sub "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*"
```

---

## Performance Optimization

### Parallel Processing

**Use multiprocessing for CPU-bound tasks:**

```python
from multiprocessing import Pool, cpu_count
from typing import List, Callable

def process_students_parallel(
    student_ids: List[str],
    processor_func: Callable,
    max_workers: int = None
) -> List[dict]:
    """Process multiple students in parallel."""
    if max_workers is None:
        max_workers = min(cpu_count(), 10)

    with Pool(processes=max_workers) as pool:
        results = pool.map(processor_func, student_ids)

    return results

# ✅ Good - Parallel processing for independent tasks
results = process_students_parallel(student_ids, analyze_transcript)

# ❌ Bad - Sequential processing (slow)
results = [analyze_transcript(sid) for sid in student_ids]
```

**Use asyncio for I/O-bound tasks:**

```python
import asyncio
from typing import List

async def process_students_async(student_ids: List[str]) -> List[dict]:
    """Process multiple students concurrently (I/O-bound)."""
    tasks = [process_student(sid) for sid in student_ids]
    return await asyncio.gather(*tasks)

async def process_student(student_id: str) -> dict:
    """Process single student (async I/O operations)."""
    # Fetch from DynamoDB
    profile = await fetch_profile(student_id)

    # Call OpenAI API
    vocab = await extract_vocabulary(profile["text"])

    # Update profile
    await update_profile(student_id, vocab)

    return {"student_id": student_id, "status": "complete"}

# ✅ Good - Async for I/O operations
results = await process_students_async(student_ids)
```

---

### Caching

**Implement response caching:**

```python
from functools import lru_cache
import hashlib
from typing import Optional

# ✅ In-memory cache for expensive computations
@lru_cache(maxsize=1000)
def get_common_core_words(grade_level: int) -> List[str]:
    """Get Common Core words for grade level (cached)."""
    # Expensive database query cached in memory
    return query_vocabulary_database(grade_level)

# ✅ Redis cache for distributed systems
import redis

class CacheClient:
    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379)

    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: int = 3600
    ) -> Optional[str]:
        """Get from cache or compute and store."""
        # Try cache first
        cached = self.redis.get(key)
        if cached:
            return cached.decode()

        # Compute and cache
        result = await compute_func()
        self.redis.setex(key, ttl, result)
        return result

# Usage
cache = CacheClient()
vocab = await cache.get_or_compute(
    f"vocab:{student_id}",
    lambda: extract_vocabulary(text),
    ttl=3600
)
```

---

### Database Query Optimization

**Optimize DynamoDB queries:**

```python
# ❌ Bad - Scan entire table (expensive)
def get_all_students_slow():
    response = table.scan()
    return response["Items"]

# ✅ Good - Query with GSI
def get_students_by_grade(grade: int):
    response = table.query(
        IndexName="grade_level-index",
        KeyConditionExpression=Key("grade_level").eq(grade)
    )
    return response["Items"]

# ✅ Good - Batch get for multiple IDs
def get_students_batch(student_ids: List[str]):
    keys = [{"student_id": sid} for sid in student_ids]
    response = dynamodb.batch_get_item(
        RequestItems={table.name: {"Keys": keys}}
    )
    return response["Responses"][table.name]
```

---

## Code Organization

### Module Structure

**Organize by domain, not by layer:**

```python
# ✅ Good - Domain-driven structure
src/
├── students/              # Student domain
│   ├── models.py          # Student data models
│   ├── repository.py      # Data access
│   ├── service.py         # Business logic
│   └── validators.py      # Validation rules
├── vocabulary/            # Vocabulary domain
│   ├── models.py
│   ├── extractor.py
│   ├── recommender.py
│   └── corpus/
└── processing/            # Processing domain
    ├── pipeline.py
    └── batch.py

# ❌ Bad - Layer-based structure (doesn't scale)
src/
├── models/               # All models mixed together
├── repositories/         # All repos mixed together
└── services/             # All services mixed together
```

---

### Dependency Injection

**Inject dependencies for testability:**

```python
# ✅ Good - Dependencies injected
class VocabularyService:
    def __init__(
        self,
        openai_client: OpenAIClient,
        student_repo: StudentRepository,
        vocab_repo: VocabularyRepository
    ):
        self.openai = openai_client
        self.students = student_repo
        self.vocabulary = vocab_repo

    async def process_transcript(self, student_id: str, text: str):
        words = await self.openai.extract_vocabulary(text)
        await self.students.update_vocabulary(student_id, words)
        return words

# Easy to test with mocks
def test_process_transcript():
    mock_openai = Mock()
    mock_repo = Mock()
    service = VocabularyService(mock_openai, mock_repo, mock_vocab_repo)
    # Test with mocks...

# ❌ Bad - Hard dependencies
class VocabularyService:
    def __init__(self):
        self.openai = OpenAIClient()  # Hard to mock
        self.students = StudentRepository()  # Hard to mock
```

---

## Error Handling

### Exception Hierarchy

**Create custom exceptions:**

```python
class VocabulatorError(Exception):
    """Base exception for Vocabulator."""
    pass

class StudentNotFoundError(VocabulatorError):
    """Student profile not found."""
    pass

class VocabularyExtractionError(VocabulatorError):
    """Failed to extract vocabulary."""
    pass

class OpenAIAPIError(VocabulatorError):
    """OpenAI API request failed."""
    pass

# Usage
def get_student_profile(student_id: str) -> dict:
    profile = student_repo.get(student_id)
    if not profile:
        raise StudentNotFoundError(f"No profile for student {student_id}")
    return profile
```

---

### Error Context

**Provide rich error context:**

```python
import traceback
from typing import Optional

class ErrorContext:
    """Capture error context for debugging."""

    def __init__(
        self,
        operation: str,
        student_id: Optional[str] = None,
        **kwargs
    ):
        self.operation = operation
        self.student_id = student_id
        self.context = kwargs

    def log_error(self, error: Exception):
        """Log error with full context."""
        logger.error(
            f"Error in {self.operation}",
            extra={
                "student_id": self.student_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": self.context,
                "traceback": traceback.format_exc()
            }
        )

# Usage
try:
    ctx = ErrorContext(
        operation="vocabulary_extraction",
        student_id="STU-001",
        text_length=1500,
        model="gpt-4o-mini"
    )
    result = await extract_vocabulary(text)
except Exception as e:
    ctx.log_error(e)
    raise
```

---

## Logging & Monitoring

### Structured Logging

**Use JSON for machine-readable logs:**

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields
        if hasattr(record, "student_id"):
            log_data["student_id"] = record.student_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("vocabulator")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("Processing transcript", extra={"student_id": "STU-001"})
```

---

### Correlation IDs

**Track requests across services:**

```python
import uuid
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id")

def set_correlation_id(cid: str = None):
    """Set correlation ID for current context."""
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid

def get_correlation_id() -> str:
    """Get correlation ID for current context."""
    try:
        return correlation_id.get()
    except LookupError:
        return set_correlation_id()

# Middleware to set correlation ID
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(cid)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response

# Use in logging
logger.info("Processing request", extra={"correlation_id": get_correlation_id()})
```

---

## Documentation Standards

### Docstring Format

**Use Google-style docstrings:**

```python
def generate_recommendations(
    student_id: str,
    grade_level: int,
    num_words: int = 10
) -> List[dict]:
    """Generate vocabulary recommendations for student.

    Analyzes student's current vocabulary profile and identifies
    appropriate challenge words from Common Core standards.

    Args:
        student_id: Anonymous student identifier (format: STU-###)
        grade_level: Student's current grade level (6-8)
        num_words: Number of words to recommend (default: 10)

    Returns:
        List of recommendation dictionaries containing:
            - word (str): The recommended word
            - definition (str): Word definition
            - difficulty_score (int): Difficulty rating 1-10
            - rationale (str): Why this word was recommended

    Raises:
        StudentNotFoundError: If student profile doesn't exist
        ValueError: If grade_level not in range 6-8

    Example:
        >>> recommendations = generate_recommendations("STU-001", 7, num_words=5)
        >>> len(recommendations)
        5
        >>> recommendations[0]["word"]
        'analyze'

    Note:
        This function makes OpenAI API calls and may be slow for
        large vocabulary profiles. Consider caching results.
    """
    # Implementation...
```

---

### API Documentation

**Document API endpoints thoroughly:**

```python
from fastapi import FastAPI, Path, Query
from typing import Annotated

@app.get(
    "/api/v1/students/{student_id}/profile",
    response_model=StudentProfileResponse,
    summary="Get student vocabulary profile",
    description="""
    Retrieve complete vocabulary profile for a student including:
    - Current vocabulary size and proficiency score
    - Recently acquired words
    - Vocabulary growth trend

    This endpoint returns eventually consistent data (may be delayed by up to 5 seconds).
    """,
    responses={
        200: {
            "description": "Student profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "student_id": "STU-001",
                        "grade_level": 7,
                        "vocabulary_size": 1250,
                        "proficiency_score": 75.5
                    }
                }
            }
        },
        404: {
            "description": "Student not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "student_not_found",
                        "message": "No profile found for student STU-999"
                    }
                }
            }
        }
    },
    tags=["Students"]
)
async def get_student_profile(
    student_id: Annotated[str, Path(description="Student identifier (format: STU-###)")],
    include_vocabulary: Annotated[bool, Query(description="Include full vocabulary list")] = False
):
    """Get student profile endpoint."""
    # Implementation...
```

---

## Git Workflow

### Commit Messages

**Write clear, descriptive commit messages:**

```bash
# ✅ Good commit messages
git commit -m "feat: add vocabulary extraction with GPT-4o-mini"
git commit -m "fix: handle rate limit errors in OpenAI client"
git commit -m "test: add integration tests for batch processing"
git commit -m "docs: update API documentation with examples"
git commit -m "refactor: extract common DynamoDB logic to base repository"

# ❌ Bad commit messages
git commit -m "updates"
git commit -m "fix bug"
git commit -m "WIP"
```

**Commit message format:**
```
<type>: <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `style`: Code style changes (formatting)

---

### Branch Strategy

**Use feature branches:**

```bash
# Create feature branch
git checkout -b feat/vocabulary-extraction

# Make changes and commit
git add src/processing/text_analyzer.py tests/unit/test_text_analyzer.py
git commit -m "feat: implement vocabulary extraction with GPT-4o-mini"

# Push to remote
git push origin feat/vocabulary-extraction

# Create pull request on GitHub
# After review and approval, merge to main
```

**Branch naming:**
- `feat/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `test/test-description` - Test additions
- `docs/doc-description` - Documentation updates

---

### Pull Request Guidelines

**PR checklist:**
- [ ] Tests written and passing (for code changes)
- [ ] Code coverage maintained or improved
- [ ] Linting passes (black, ruff, mypy)
- [ ] Documentation updated (if needed)
- [ ] PR description explains what and why
- [ ] Self-reviewed code for obvious issues
- [ ] Breaking changes documented
- [ ] Memory Bank updated (if relevant)

**PR description template:**
```markdown
## What
Brief description of changes

## Why
Reason for the changes (link to issue/task)

## How
Technical approach and design decisions

## Testing
How was this tested? Manual testing steps if applicable

## Screenshots
(If UI changes)

## Checklist
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Reviewed by self
```

---

## Summary Checklist

### Code Quality
- [ ] Code formatted with black
- [ ] Linting passes (ruff)
- [ ] Type hints added (mypy)
- [ ] Docstrings written (Google style)
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Error handling comprehensive
- [ ] Logging added (structured JSON)

### Testing
- [ ] Tests written before implementation (TDD)
- [ ] Unit tests for business logic
- [ ] Integration tests for workflows
- [ ] Mocks for external services
- [ ] Test coverage > 60%
- [ ] Tests run in CI/CD

### Performance
- [ ] Async used for I/O operations
- [ ] Parallel processing for CPU-bound tasks
- [ ] Response caching implemented
- [ ] Database queries optimized
- [ ] OpenAI API costs monitored

### Security
- [ ] Anonymous student IDs enforced
- [ ] Secrets in environment variables
- [ ] IAM least privilege applied
- [ ] Input sanitization implemented
- [ ] Data encryption enabled

### AWS Best Practices
- [ ] boto3 clients reused
- [ ] Retry logic configured
- [ ] DynamoDB uses GSI for queries
- [ ] S3 uses multipart upload
- [ ] Lambda cold starts optimized
- [ ] CloudWatch metrics added

### Documentation
- [ ] README updated
- [ ] API endpoints documented
- [ ] Architecture documented
- [ ] Deployment guide written
- [ ] Code comments where needed

---

**Document Status:** Active Reference
**Next Review Date:** Quarterly (after major tech stack updates)
**Owner:** Technical Lead
**Last Updated:** 2025-11-10
