# Developer Onboarding Guide

**Project:** Vocabulator - Personalized Vocabulary Recommendation Engine  
**Version:** 1.0.0 (MVP)  
**Last Updated:** 2025-11-12

---

## Table of Contents

1. [Welcome](#welcome)
2. [Quick Start](#quick-start)
3. [Prerequisites](#prerequisites)
4. [Development Environment Setup](#development-environment-setup)
5. [Project Structure](#project-structure)
6. [Common Development Tasks](#common-development-tasks)
7. [Testing](#testing)
8. [Code Quality](#code-quality)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## Welcome

Welcome to the Vocabulator project! This guide will help you get up and running quickly. By the end of this guide, you'll be able to:

- Set up your local development environment
- Run tests and verify everything works
- Understand the project structure
- Make your first contribution

**Estimated Setup Time:** 30-45 minutes

---

## Quick Start

If you're experienced with Python/FastAPI projects, here's the TL;DR:

```bash
# Clone and setup
git clone <repo-url>
cd vocabulator
./scripts/setup-dev-env.sh

# Start LocalStack (AWS emulation)
docker-compose up -d localstack

# Run tests
pytest

# Start API server
uvicorn src.api.main:app --reload
```

**API will be available at:** `http://localhost:8000`  
**Interactive docs:** `http://localhost:8000/api/v1/docs`

---

## Prerequisites

Before you begin, ensure you have:

### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Docker** | 20.10+ | [docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.0+ | Included with Docker Desktop |
| **Git** | 2.30+ | [git-scm.com](https://git-scm.com/downloads) |

### Verify Installation

```bash
python3 --version  # Should show 3.11 or higher
docker --version   # Should show 20.10 or higher
docker-compose --version  # Should show 2.0 or higher
git --version      # Should show 2.30 or higher
```

### Required Accounts & Keys

- **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com/api-keys)
  - Required for vocabulary extraction and recommendations
  - Free tier available for testing
- **AWS Account** (optional for local development)
  - Only needed for deploying to AWS
  - LocalStack emulates AWS services locally

---

## Development Environment Setup

### Step 1: Clone the Repository

```bash
git clone <repo-url>
cd vocabulator
```

### Step 2: Run Setup Script

We provide an automated setup script that handles everything:

```bash
./scripts/setup-dev-env.sh
```

**What it does:**
- ✅ Checks Python version (3.11+)
- ✅ Creates virtual environment (`venv/`)
- ✅ Installs all dependencies (production + development)
- ✅ Sets up pre-commit hooks
- ✅ Creates `.env` file from template
- ✅ Verifies Docker installation

**Manual Setup** (if script doesn't work):

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Create .env file
cp .env.example .env
```

### Step 3: Configure Environment Variables

Edit `.env` file with your configuration:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
AWS_REGION=us-east-1
ENVIRONMENT=development

# LocalStack (for local AWS emulation)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
LOCALSTACK_ENDPOINT_URL=http://localhost:4566

# DynamoDB & S3 (local development)
DYNAMODB_TABLE_PREFIX=vocabulator-dev
S3_BUCKET_NAME=vocabulator-data-dev

# Optional
LOG_LEVEL=DEBUG
```

**Important:** Never commit `.env` file to git (it's in `.gitignore`).

### Step 4: Start LocalStack (AWS Emulation)

LocalStack provides local AWS services for development:

```bash
docker-compose up -d localstack
```

**Verify LocalStack is running:**

```bash
docker ps | grep localstack
# Should show localstack container running
```

**Access LocalStack services:**
- DynamoDB: `http://localhost:4566`
- S3: `http://localhost:4566`
- CloudWatch: `http://localhost:4566`

### Step 5: Initialize Local Database

Seed the Common Core vocabulary database:

```bash
python scripts/setup_localstack_tables.py
python scripts/seed_vocabulary_db.py --local
```

### Step 6: Verify Setup

Run the setup verification tests:

```bash
pytest tests/test_setup.py -v
```

**Expected output:** All tests pass ✅

---

## Project Structure

Understanding the project structure helps you navigate the codebase:

```
vocabulator/
├── src/                          # Source code
│   ├── api/                      # FastAPI application
│   │   ├── main.py              # FastAPI app initialization
│   │   ├── routes/              # API endpoints
│   │   ├── models/              # Request/response models
│   │   └── dependencies.py      # Dependency injection
│   ├── data/                     # Data layer
│   │   ├── dynamodb_client.py   # DynamoDB client wrapper
│   │   ├── s3_client.py         # S3 client wrapper
│   │   ├── models/              # Data models (Pydantic)
│   │   └── repositories/        # Repository pattern implementations
│   ├── ai/                       # AI/ML layer
│   │   ├── openai_client.py     # OpenAI client wrapper
│   │   ├── vocabulary_extractor.py
│   │   └── prompts/             # Prompt templates
│   ├── processing/              # Processing layer
│   │   ├── text_processing_pipeline.py
│   │   ├── batch_client.py      # AWS Batch integration
│   │   └── parallel_executor.py
│   ├── vocabulary/              # Vocabulary data
│   │   ├── common_core_loader.py
│   │   └── corpus/              # JSON corpus files
│   ├── frontend/                 # Frontend layer
│   │   ├── report_generator.py
│   │   └── templates/           # Jinja2 HTML templates
│   └── utils/                    # Utilities
│       ├── config.py             # Configuration management
│       └── logger.py             # Structured logging
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── fixtures/                 # Test fixtures
│   └── mocks/                    # Mock objects
├── infrastructure/               # Infrastructure as Code
│   ├── cloudformation/          # CloudFormation templates
│   └── docker/                   # Dockerfiles
├── scripts/                      # Utility scripts
│   ├── setup-dev-env.sh         # Development setup
│   ├── seed_vocabulary_db.py    # Database seeding
│   └── deploy-infrastructure.sh # Deployment script
├── _docs/                        # Documentation
│   ├── architecture.md          # System architecture
│   ├── api-documentation.md     # API reference
│   ├── best-practices.md        # Coding standards
│   └── required-reading.md      # Learning resources
├── memory-bank/                  # Project context (for AI assistants)
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml               # Project configuration
├── docker-compose.yml           # LocalStack configuration
└── .env.example                 # Environment variable template
```

### Key Directories

- **`src/api/`**: FastAPI application, routes, models
- **`src/data/`**: Data access layer (DynamoDB, S3, repositories)
- **`src/ai/`**: OpenAI integration, vocabulary extraction
- **`src/processing/`**: Text processing pipeline, batch processing
- **`tests/`**: Test suite (unit, integration, fixtures)
- **`infrastructure/`**: CloudFormation templates, Dockerfiles
- **`_docs/`**: All project documentation

---

## Common Development Tasks

### Running the API Server

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start development server with auto-reload
uvicorn src.api.main:app --reload --port 8000
```

**Access:**
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- Health check: `http://localhost:8000/health`

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_student_repository.py

# Run specific test
pytest tests/unit/test_student_repository.py::test_create_student

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf
```

### Code Quality Checks

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run individual tools
black src/ tests/              # Format code
ruff check src/ tests/         # Lint code
mypy src/                      # Type checking
pytest --cov=src              # Run tests with coverage
```

### Adding a New Endpoint

1. **Create request/response models** (`src/api/models/requests.py`, `responses.py`)
2. **Create route handler** (`src/api/routes/your_feature.py`)
3. **Register router** (`src/api/main.py`)
4. **Write tests** (`tests/unit/test_your_feature.py`)
5. **Update API documentation** (`_docs/api-documentation.md`)

**Example:**

```python
# src/api/routes/your_feature.py
from fastapi import APIRouter
from src.api.models.requests import YourRequest
from src.api.models.responses import YourResponse

router = APIRouter()

@router.post("/your-endpoint", response_model=YourResponse)
async def your_handler(request: YourRequest) -> YourResponse:
    # Implementation
    pass
```

### Adding a New Data Model

1. **Create Pydantic model** (`src/data/models/your_model.py`)
2. **Create repository** (`src/data/repositories/your_repository.py`)
3. **Write tests** (`tests/unit/test_your_model.py`, `test_your_repository.py`)
4. **Update CloudFormation** (if new DynamoDB table needed)

### Working with LocalStack

```bash
# Start LocalStack
docker-compose up -d localstack

# View logs
docker-compose logs -f localstack

# Stop LocalStack
docker-compose down

# Reset LocalStack (clears all data)
docker-compose down -v
docker-compose up -d localstack
```

**Accessing LocalStack services:**

```python
# In your code, use LOCALSTACK_ENDPOINT_URL
import boto3
from src.utils.config import get_config

config = get_config()
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=config.get_aws_endpoint_url()
)
```

---

## Testing

### Test-First Development (TDD)

We follow test-first development. Here's the workflow:

1. **Write failing test** (RED)
   ```python
   def test_new_feature():
       result = your_function()
       assert result == expected_value
   ```

2. **Run test** (should fail)
   ```bash
   pytest tests/unit/test_your_feature.py -v
   ```

3. **Implement feature** (GREEN)
   ```python
   def your_function():
       return expected_value
   ```

4. **Run test** (should pass)
   ```bash
   pytest tests/unit/test_your_feature.py -v
   ```

5. **Refactor** (if needed)
   - Improve code quality
   - Ensure all tests still pass

### Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_student_repository.py
│   └── test_vocabulary_extractor.py
├── integration/             # Integration tests (slower, require LocalStack)
│   ├── test_api_workflows.py
│   └── test_batch_processing.py
├── fixtures/                # Test fixtures
│   ├── dynamodb_setup.py
│   └── s3_setup.py
└── mocks/                   # Mock objects
    └── mock_openai.py
```

### Writing Tests

**Unit Test Example:**

```python
import pytest
from src.data.repositories.student_repository import StudentRepository
from src.data.models.student_profile import StudentProfile

def test_create_student(student_repo: StudentRepository):
    """Test creating a new student profile."""
    profile = StudentProfile(
        student_id="STU-001",
        grade_level=7,
        vocabulary_list=[],
        proficiency_score=0.0,
    )
    
    created = student_repo.create(profile)
    
    assert created.student_id == "STU-001"
    assert created.grade_level == 7
    assert len(created.vocabulary_list) == 0
```

**Integration Test Example:**

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_create_student_and_upload_transcript():
    """Test complete workflow: create student → upload transcript."""
    # Create student
    response = client.post("/api/v1/students", json={
        "student_id": "STU-001",
        "grade_level": 7
    })
    assert response.status_code == 201
    
    # Upload transcript
    response = client.post("/api/v1/transcripts/upload", json={
        "student_id": "STU-001",
        "text": "Today we learned about photosynthesis.",
        "session_date": "2025-11-10",
        "grade_level": 7
    })
    assert response.status_code == 200
    assert response.json()["words_extracted"] > 0
```

### Test Coverage

We aim for 60-80% test coverage:

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Code Quality

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking
- **pytest**: Run tests

**Manual run:**

```bash
pre-commit run --all-files
```

### Code Style

- **Formatting**: Black (line length: 100)
- **Linting**: Ruff (with strict rules)
- **Type Hints**: Required for all functions (mypy strict mode)
- **Docstrings**: Google style for all public functions/classes

**Example:**

```python
from typing import Optional

def process_text(
    text: str,
    student_id: str,
    grade_level: int,
    request_id: Optional[str] = None,
) -> dict:
    """Process text and extract vocabulary.
    
    Args:
        text: Text content to process
        student_id: Student identifier
        grade_level: Student grade level (6-8)
        request_id: Optional request ID for correlation
        
    Returns:
        Dictionary with extracted vocabulary
        
    Raises:
        ValueError: If text is invalid
    """
    # Implementation
    pass
```

### Type Hints

**Required:**
- All function parameters
- All return types
- All class attributes

**Example:**

```python
from typing import List, Optional
from datetime import datetime

class StudentProfile:
    student_id: str
    grade_level: int
    vocabulary_list: List[str]
    created_at: datetime
    last_updated: Optional[datetime] = None
```

---

## Troubleshooting

### Common Issues

#### "Python 3.11+ required"

**Problem:** Python version is too old.

**Solution:**
```bash
# Check version
python3 --version

# Install Python 3.11+ from python.org
# Or use pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

#### "Module not found" errors

**Problem:** Virtual environment not activated or dependencies not installed.

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### LocalStack connection errors

**Problem:** LocalStack not running or wrong endpoint URL.

**Solution:**
```bash
# Check LocalStack status
docker ps | grep localstack

# Start LocalStack
docker-compose up -d localstack

# Verify endpoint URL in .env
LOCALSTACK_ENDPOINT_URL=http://localhost:4566
```

#### Tests failing with "Table not found"

**Problem:** LocalStack tables not initialized.

**Solution:**
```bash
# Initialize tables
python scripts/setup_localstack_tables.py

# Seed vocabulary database
python scripts/seed_vocabulary_db.py --local
```

#### OpenAI API errors

**Problem:** Invalid API key or rate limit exceeded.

**Solution:**
- Verify `OPENAI_API_KEY` in `.env` file
- Check API key at [platform.openai.com](https://platform.openai.com/api-keys)
- Verify account has credits/quota

#### Pre-commit hooks failing

**Problem:** Code doesn't pass quality checks.

**Solution:**
```bash
# Auto-fix formatting
black src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Fix type errors
mypy src/  # Review errors and fix manually
```

### Getting Help

1. **Check Documentation:**
   - `_docs/architecture.md` - System architecture
   - `_docs/api-documentation.md` - API reference
   - `_docs/best-practices.md` - Coding standards

2. **Check Existing Issues:**
   - Search GitHub issues for similar problems

3. **Ask for Help:**
   - Create a new issue with:
     - Error message
     - Steps to reproduce
     - Environment details (`python --version`, OS, etc.)

---

## Next Steps

Now that you're set up, here's what to do next:

### 1. Read Essential Documentation

**Priority 0 (Must Read):**
- [ ] [PRD](PRD_Flourish_Schools_Personalized_Vocabulary_Recommendation_Engine_for_.md) - Product requirements
- [ ] [Architecture](architecture.md) - System design
- [ ] [Best Practices](best-practices.md) - Coding standards
- [ ] [Test-First Workflow](guides/test-first-workflow.md) - TDD process

**Priority 1 (Recommended):**
- [ ] [API Documentation](api-documentation.md) - API reference
- [ ] [Required Reading](required-reading.md) - Technology tutorials

### 2. Explore the Codebase

- Run the API server and explore endpoints in Swagger UI
- Read through existing code to understand patterns
- Run tests to see how features are tested

### 3. Make Your First Contribution

**Good First Tasks:**
- Fix a bug (check GitHub issues)
- Add a test for existing feature
- Improve documentation
- Add code comments

**Workflow:**
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes following TDD
3. Run tests: `pytest`
4. Run quality checks: `pre-commit run --all-files`
5. Commit: `git commit -m "feat: your feature"`
6. Push: `git push origin feature/your-feature`
7. Create pull request

### 4. Learn the Technologies

See [required-reading.md](required-reading.md) for curated learning resources:
- Python 3.11+ (type hints, async/await)
- FastAPI (dependency injection, testing)
- AWS services (DynamoDB, S3, Lambda, Batch)
- OpenAI API (prompt engineering, cost optimization)

---

## Additional Resources

- **Project Repository:** [GitHub URL]
- **Issue Tracker:** [GitHub Issues]
- **Architecture Diagram:** See `_docs/architecture.md`
- **API Interactive Docs:** `http://localhost:8000/api/v1/docs` (when server running)

---

**Welcome to the team! 🎉**

If you have questions or need help, don't hesitate to ask. Happy coding!

---

**Last Updated:** 2025-11-12  
**Maintained by:** Development Team

