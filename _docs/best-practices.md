# Vocabulator Best Practices Guide

**Project:** Personalized Vocabulary Recommendation Engine for Middle School Students
**Version:** 1.0.0 (MVP)
**Last Updated:** 2025-11-10

---

## Overview

This document provides navigation to best practices for building modular, scalable, and maintainable Python applications with our specific tech stack: FastAPI, OpenAI SDK, AWS services (Lambda, Fargate, DynamoDB, S3), and pytest.

These practices ensure code quality, security, testability, and cost-efficiency throughout the development lifecycle.

**Documentation Structure:**
- **This file:** High-level overview and navigation to detailed guides
- **Practice detail files:** Complete best practices with code examples and patterns

---

## Quick Navigation

### Detailed Practice Guides
- [Python Development Standards](best-practices/python-development.md) - Start here
- [FastAPI Best Practices](best-practices/fastapi-patterns.md)
- [OpenAI API Integration](best-practices/openai-integration.md)
- [AWS Services Best Practices](best-practices/aws-services.md)
- [Testing Standards](best-practices/testing-standards.md)
- [Security & Privacy](best-practices/security-privacy.md)
- [Performance Optimization](best-practices/performance.md)
- [Code Organization](best-practices/code-organization.md)
- [Error Handling](best-practices/error-handling.md)
- [Logging & Monitoring](best-practices/logging-monitoring.md)
- [Documentation Standards](best-practices/documentation.md)
- [Git Workflow](best-practices/git-workflow.md)

### Supporting Documentation
- [architecture.md](architecture.md) - System architecture and tech stack
- [task-list.md](task-list.md) - MVP implementation roadmap
- [required-reading.md](required-reading.md) - Developer onboarding materials

---

## Practice Area Summaries

### 1. Python Development Standards
**Guide:** [python-development.md](best-practices/python-development.md)

**What:** Code style, formatting, dependency management, async patterns
**Key Topics:**
- Automated formatters (black, ruff, mypy)
- Virtual environments and dependency pinning
- Async/await patterns for I/O operations
- Type hints and docstrings

**Quick Reference:**
```bash
# Format and lint
black src/ tests/
ruff check src/ tests/
mypy src/ --strict

# Virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. FastAPI Best Practices
**Guide:** [fastapi-patterns.md](best-practices/fastapi-patterns.md)

**What:** Application structure, dependency injection, request/response models, error handling
**Key Topics:**
- Feature-based organization (not type-based)
- Dependency injection for shared resources
- Pydantic validation with clear error messages
- TestClient for endpoint testing

**Quick Reference:**
```python
# Dependency injection
@app.post("/api/v1/transcripts/upload")
async def upload_transcript(
    request: TranscriptUploadRequest,
    db: Annotated[DynamoDBClient, Depends(get_db_client)]
):
    return await process_upload(request, db)
```

---

### 3. OpenAI API Integration
**Guide:** [openai-integration.md](best-practices/openai-integration.md)

**What:** Client configuration, prompt engineering, cost optimization, error handling
**Key Topics:**
- Reusable OpenAI client with retry logic
- Structured prompt templates (Jinja2)
- Cost tracking and optimization strategies
- Rate limit handling with exponential backoff

**Quick Reference:**
```python
# Use GPT-4o-mini for extraction (10x cheaper)
response = await openai_client.complete(
    model="gpt-4o-mini",
    messages=[...],
    temperature=0.3,  # Lower for consistency
    max_tokens=2000
)
```

---

### 4. AWS Services Best Practices
**Guide:** [aws-services.md](best-practices/aws-services.md)

**What:** boto3 clients, DynamoDB patterns, S3 operations, Lambda optimization
**Key Topics:**
- Client reuse and connection pooling
- Efficient DynamoDB queries (use GSI, avoid scan)
- S3 multipart upload and presigned URLs
- Lambda cold start optimization

**Quick Reference:**
```python
# DynamoDB: Use GSI for non-key queries
response = table.query(
    IndexName="grade_level-index",
    KeyConditionExpression=Key("grade_level").eq(7)
)

# S3: Enable encryption by default
extra_args = {"ServerSideEncryption": "AES256"}
```

---

### 5. Testing Standards
**Guide:** [testing-standards.md](best-practices/testing-standards.md)

**What:** Test organization, TDD workflow, pytest fixtures, mocking, coverage
**Key Topics:**
- Test-first development (RED-GREEN-REFACTOR)
- Pytest fixtures for setup/teardown
- Mocking OpenAI and AWS services
- Target: 60-80% code coverage

**Quick Reference:**
```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-fail-under=60

# Mock AWS services
from moto import mock_dynamodb

@mock_dynamodb
def test_student_repository():
    # Test with mocked DynamoDB
```

---

### 6. Security & Privacy
**Guide:** [security-privacy.md](best-practices/security-privacy.md)

**What:** COPPA compliance, secrets management, input validation, IAM least privilege
**Key Topics:**
- Anonymous student IDs (no PII collection)
- Environment variables and AWS Secrets Manager
- Input sanitization (XSS prevention)
- IAM policies with minimum permissions

**Quick Reference:**
```python
# Anonymous student ID validation
STUDENT_ID_PATTERN = re.compile(r"^STU-\d{3}$")

# Never hardcode secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Sanitize user input
text = bleach.clean(text, tags=[], strip=True)
```

---

### 7. Performance Optimization
**Guide:** [performance.md](best-practices/performance.md)

**What:** Parallel processing, caching, database query optimization
**Key Topics:**
- Multiprocessing for CPU-bound tasks
- Asyncio for I/O-bound tasks
- In-memory caching (lru_cache) and Redis
- DynamoDB batch operations

**Quick Reference:**
```python
# Parallel processing for independent tasks
from multiprocessing import Pool
with Pool() as pool:
    results = pool.map(process_student, student_ids)

# Async for I/O operations
results = await asyncio.gather(*tasks)

# Cache expensive computations
@lru_cache(maxsize=1000)
def get_common_core_words(grade: int):
    return query_database(grade)
```

---

### 8. Code Organization
**Guide:** [code-organization.md](best-practices/code-organization.md)

**What:** Module structure, dependency injection
**Key Topics:**
- Domain-driven design (not layer-based)
- Dependency injection for testability
- Clear separation of concerns

**Quick Reference:**
```python
# Domain-driven structure
src/
├── students/              # Student domain
│   ├── models.py
│   ├── repository.py
│   └── service.py
├── vocabulary/            # Vocabulary domain
└── processing/            # Processing domain
```

---

### 9. Error Handling
**Guide:** [error-handling.md](best-practices/error-handling.md)

**What:** Custom exceptions, error context, retry logic
**Key Topics:**
- Exception hierarchy (base VocabulatorError)
- Rich error context for debugging
- Exponential backoff for retries

**Quick Reference:**
```python
class VocabulatorError(Exception):
    """Base exception."""
    pass

class StudentNotFoundError(VocabulatorError):
    """Student profile not found."""
    pass
```

---

### 10. Logging & Monitoring
**Guide:** [logging-monitoring.md](best-practices/logging-monitoring.md)

**What:** Structured logging, correlation IDs, CloudWatch integration
**Key Topics:**
- JSON-formatted logs (machine-readable)
- Correlation IDs for request tracking
- Structured logging with extra fields

**Quick Reference:**
```python
# JSON structured logging
logger.info(
    "Processing transcript",
    extra={
        "student_id": "STU-001",
        "correlation_id": get_correlation_id()
    }
)
```

---

### 11. Documentation Standards
**Guide:** [documentation.md](best-practices/documentation.md)

**What:** Docstring format, API documentation
**Key Topics:**
- Google-style docstrings
- FastAPI OpenAPI documentation
- Clear examples and edge cases

**Quick Reference:**
```python
def generate_recommendations(student_id: str, grade: int) -> List[dict]:
    """Generate vocabulary recommendations.

    Args:
        student_id: Anonymous student identifier (STU-###)
        grade: Student grade level (6-8)

    Returns:
        List of recommendation dictionaries

    Raises:
        StudentNotFoundError: If student doesn't exist
    """
```

---

### 12. Git Workflow
**Guide:** [git-workflow.md](best-practices/git-workflow.md)

**What:** Commit messages, branch strategy, pull requests
**Key Topics:**
- Conventional commit messages (feat, fix, docs, test)
- Feature branches (feat/, fix/, test/, docs/)
- PR checklist and description template

**Quick Reference:**
```bash
# Good commit messages
git commit -m "feat: add vocabulary extraction with GPT-4o-mini"
git commit -m "fix: handle rate limit errors in OpenAI client"
git commit -m "test: add integration tests for batch processing"

# Feature branch workflow
git checkout -b feat/vocabulary-extraction
# Make changes...
git push origin feat/vocabulary-extraction
# Create PR on GitHub
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

## Technology-Specific Quick Links

### Python 3.11+
- [Python Development Standards](best-practices/python-development.md)
- [Testing Standards](best-practices/testing-standards.md)
- [Code Organization](best-practices/code-organization.md)

### FastAPI
- [FastAPI Patterns](best-practices/fastapi-patterns.md)
- [Error Handling](best-practices/error-handling.md)
- [Documentation Standards](best-practices/documentation.md)

### OpenAI SDK
- [OpenAI Integration](best-practices/openai-integration.md)
- [Performance Optimization](best-practices/performance.md)

### AWS Services
- [AWS Services Best Practices](best-practices/aws-services.md)
- [Security & Privacy](best-practices/security-privacy.md)
- [Logging & Monitoring](best-practices/logging-monitoring.md)

### Testing (pytest)
- [Testing Standards](best-practices/testing-standards.md)

### Security & Compliance
- [Security & Privacy](best-practices/security-privacy.md)

---

## Getting Started

### For New Developers
1. Read [Python Development Standards](best-practices/python-development.md)
2. Review [Testing Standards](best-practices/testing-standards.md)
3. Study [FastAPI Patterns](best-practices/fastapi-patterns.md)
4. Review [Security & Privacy](best-practices/security-privacy.md)

### For Specific Tasks
- **Implementing API endpoints?** → [FastAPI Patterns](best-practices/fastapi-patterns.md)
- **Integrating OpenAI?** → [OpenAI Integration](best-practices/openai-integration.md)
- **Working with AWS?** → [AWS Services](best-practices/aws-services.md)
- **Writing tests?** → [Testing Standards](best-practices/testing-standards.md)
- **Debugging errors?** → [Error Handling](best-practices/error-handling.md) + [Logging & Monitoring](best-practices/logging-monitoring.md)

---

## Cross-Project Documentation

### Architecture & Planning
- [architecture.md](architecture.md) - System architecture and design decisions
- [task-list.md](task-list.md) - MVP implementation roadmap with 9 phases
- [required-reading.md](required-reading.md) - Curated learning resources

### Implementation Guides
- [Phase 0: Project Setup](task-list/phase-0-project-setup.md)
- [Phase 1: Data Layer](task-list/phase-1-data-layer.md)
- [Phase 2: AI/ML Layer](task-list/phase-2-ai-ml-layer.md)
- [Phases 3-9: Summary](task-list/phases-3-to-9-summary.md)

---

## Document Status

**Version:** 1.0.0
**Status:** Active Reference
**Next Review Date:** Quarterly (after major tech stack updates)
**Owner:** Technical Lead
**Last Updated:** 2025-11-10

**Change Log:**
- 2025-11-10: Restructured into modular practice guides for better navigation
- Original detailed best practices preserved in topic-specific files

---

**Ready to dive in?** → Open [Python Development Standards](best-practices/python-development.md) to begin!
