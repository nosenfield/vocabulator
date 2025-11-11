# Technical Context: vocabulator

**Last Updated**: 2025-11-10

## Tech Stack

### Backend
- **Runtime**: Python 3.11+
- **Framework**: FastAPI 0.104+ (for API layer)
- **Language**: Python with type hints
- **Database**: Amazon DynamoDB (NoSQL)
- **File Storage**: Amazon S3
- **AI/ML**: OpenAI SDK (GPT-4o-mini, GPT-4o)

### Infrastructure
- **Compute**: AWS Lambda (API), AWS Batch + Fargate (processing)
- **API Gateway**: AWS API Gateway (REST)
- **Storage**: DynamoDB (structured data), S3 (files)
- **IaC**: CloudFormation (Infrastructure as Code)
- **CI/CD**: GitHub Actions (planned)
- **Monitoring**: CloudWatch Logs (planned)

### Testing
- **Unit Tests**: pytest
- **Integration Tests**: pytest with LocalStack
- **Mocking**: unittest.mock, moto (for AWS services)
- **Coverage Tool**: pytest-cov
- **Code Quality**: black, ruff, mypy, pre-commit hooks

---

## Development Setup

### Prerequisites
```bash
- Python 3.11+
- pip or poetry
- Docker & Docker Compose (for LocalStack)
- Git
```

### Installation
```bash
# Clone repository
git clone [repo-url]
cd vocabulator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Start LocalStack (for local AWS emulation)
docker-compose up -d

# Run tests
pytest

# Run code quality checks
pre-commit run --all-files
```

### Environment Variables
```bash
# Required
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test              # For LocalStack
AWS_SECRET_ACCESS_KEY=test          # For LocalStack
DYNAMODB_TABLE_PREFIX=vocabulator
S3_BUCKET_NAME=vocabulator-data-dev
OPENAI_API_KEY=sk-...               # Your OpenAI API key
ENVIRONMENT=development

# Optional
LOCALSTACK_ENDPOINT_URL=http://localhost:4566  # For local development
LOG_LEVEL=DEBUG                     # DEBUG, INFO, WARNING, ERROR
```

---

## Dependencies

### Core Dependencies
- `fastapi@0.104+` - Modern async web framework
- `boto3@1.28+` - AWS SDK for Python
- `openai@1.0+` - OpenAI API client
- `pydantic@2.0+` - Data validation and settings management
- `pydantic-settings@2.0+` - Settings management for Pydantic
- `httpx@0.25+` - HTTP client (for async requests)

### Development Dependencies
- `pytest@8.0+` - Testing framework
- `pytest-asyncio@0.24+` - Async test support
- `black@23.0+` - Code formatter
- `ruff@0.1+` - Fast Python linter
- `mypy@1.5+` - Static type checker
- `pre-commit@3.0+` - Git hooks framework

### Why We Chose These

**FastAPI**: Modern, async-capable, automatic OpenAPI documentation, excellent performance

**Pydantic**: Type-safe data validation, excellent for API request/response models and configuration

**boto3**: Official AWS SDK, well-maintained, comprehensive service coverage

**OpenAI SDK**: Official client, handles streaming, retries, and rate limiting

**pytest**: Industry standard for Python testing, excellent fixture system, plugin ecosystem

---

## Technical Constraints

### Performance Requirements
- API response time: < 200ms (p95) for simple queries
- Batch processing: Process 50 students in < 5 minutes
- DynamoDB queries: < 100ms (p95)
- S3 upload/download: < 2s for typical files (< 1MB)

### Platform Constraints
- Must run on AWS (Lambda, Batch, DynamoDB, S3)
- Must support Python 3.11+ (specified in PRD)
- Must work with LocalStack for local development
- Must be COPPA-compliant (no PII collection)

### Security Requirements
- Authentication: API keys (MVP), IAM roles (production)
- Authorization: API Gateway + Lambda authorizers (planned)
- Data encryption: AES256 at rest (S3, DynamoDB), TLS in transit
- Secrets management: Environment variables (MVP), AWS Secrets Manager (production)

---

## Build & Deployment

### Build Process
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run code quality checks
black src tests
ruff check src tests
mypy src

# Package Lambda deployment (future)
# (Will use AWS SAM or similar)
```

### Deployment
```bash
# Deploy CloudFormation stack (future)
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/dynamodb-tables.yaml \
  --stack-name vocabulator-dev \
  --parameter-overrides Environment=development

# Deploy Lambda functions (future)
# (Will use AWS SAM or Serverless Framework)
```

### Environments
- **Development**: Local with LocalStack
- **Staging**: AWS (planned)
- **Production**: AWS (planned)

---

## Troubleshooting

### Common Issues

#### Issue 1: LocalStack Connection Errors
**Problem**: Tests fail with "Could not connect to endpoint URL"
**Solution**: 
```bash
# Start LocalStack
docker-compose up -d

# Verify it's running
curl http://localhost:4566/_localstack/health
```

#### Issue 2: Missing Environment Variables
**Problem**: `MissingConfigError` when running tests
**Solution**: 
- Check that `tests/conftest.py` sets environment variables
- Or set them manually: `export AWS_ACCESS_KEY_ID=test`

#### Issue 3: Import Errors
**Problem**: `ModuleNotFoundError` when importing from `src/`
**Solution**:
- Ensure you're in the project root directory
- Verify virtual environment is activated
- Check that `src/` is in Python path (or use `PYTHONPATH=src`)

#### Issue 4: DynamoDB Table Not Found
**Problem**: Tests fail with "ResourceNotFoundException"
**Solution**:
- Ensure LocalStack is running
- Check that test fixtures create tables before tests run
- Verify table names match configuration
