# Vocabulator MVP Task List

**Project:** Personalized Vocabulary Recommendation Engine for Middle School Students
**Version:** 1.0.0 (MVP)
**Last Updated:** 2025-11-10

---

## Overview

This document provides a comprehensive task breakdown for building the Vocabulator MVP from 0 to 1. Tasks are organized in dependency order and prioritized using the MoSCoW method (Must-have, Should-have, Could-have, Won't-have).

**Development Approach:** Test-First Development (TDD)
- Write tests BEFORE implementation
- All tasks marked with 🧪 require tests written first
- Reference: `_docs/guides/test-first-workflow.md`

---

## Task Priority Legend

| Symbol | Priority | Description |
|--------|----------|-------------|
| 🔴 P0 | Must-have | Critical for MVP launch |
| 🟡 P1 | Should-have | Important but can be deferred |
| 🟢 P2 | Could-have | Nice to have, post-MVP |
| 🧪 | Test-first | Write tests before implementation |
| ⚙️ | Infrastructure | DevOps/deployment task |
| 📝 | Documentation | Documentation update required |

---

## Phase 0: Project Setup & Foundation

### 0.1 Development Environment Setup
**Priority:** 🔴 P0
**Estimated Time:** 2-3 hours
**Dependencies:** None

**Tasks:**
- [ ] Create Python virtual environment (Python 3.11+)
- [ ] Install core dependencies (FastAPI, pytest, boto3, openai)
- [ ] Set up `.env.example` and `.env` files
- [ ] Install development tools (black, ruff, mypy, pytest-cov)
- [ ] Configure pre-commit hooks for code quality
- [ ] Set up LocalStack for AWS emulation
- [ ] Create Docker Compose file for local services
- [ ] Verify setup with hello-world test

**Acceptance Criteria:**
- `pytest --version` runs successfully
- `pip list` shows all required packages
- LocalStack starts without errors
- Sample test passes

**Files Created:**
- `requirements.txt`
- `requirements-dev.txt`
- `.env.example`
- `docker-compose.yml`
- `.pre-commit-config.yaml`
- `tests/test_setup.py`

---

### 0.2 Project Structure Creation
**Priority:** 🔴 P0
**Estimated Time:** 1 hour
**Dependencies:** 0.1

**Tasks:**
- [ ] Create all directories per architecture.md structure
- [ ] Add `__init__.py` files to all Python packages
- [ ] Create placeholder README.md files for major directories
- [ ] Set up pytest configuration (`pytest.ini`, `conftest.py`)
- [ ] Create `pyproject.toml` for project metadata
- [ ] Initialize git repository (if not already done)
- [ ] Configure `.gitignore` for Python, AWS, IDE files

**Acceptance Criteria:**
- All directories from architecture.md exist
- `pytest tests/` discovers test directory
- Import statements work: `from src.api import main`

**Files Created:**
- Complete directory structure
- `pytest.ini`
- `pyproject.toml`
- `tests/conftest.py`

---

### 0.3 Configuration Management System
**Priority:** 🔴 P0 🧪
**Estimated Time:** 3-4 hours
**Dependencies:** 0.2

**Tasks:**
- [ ] 🧪 Write tests for `src/utils/config.py`
- [ ] Implement configuration loader (environment variables)
- [ ] Add validation for required config values
- [ ] Support multiple environments (dev, staging, prod)
- [ ] Create configuration dataclasses with Pydantic
- [ ] Add secrets management integration (AWS Secrets Manager stub)
- [ ] Document all configuration options

**Acceptance Criteria:**
- Tests pass for config loading and validation
- Missing required config raises clear error
- Config values accessible via type-safe objects
- Environment switching works correctly

**Files Created:**
- `src/utils/config.py`
- `tests/unit/test_config.py`
- `.env.example` (updated with all variables)

**Environment Variables Needed:**
```
ENVIRONMENT=development
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
OPENAI_API_KEY=sk-...
S3_BUCKET_NAME=vocabulator-data-dev
DYNAMODB_TABLE_PREFIX=vocabulator-dev
LOG_LEVEL=INFO
```

---

### 0.4 Logging Utility Setup
**Priority:** 🔴 P0 🧪
**Estimated Time:** 2-3 hours
**Dependencies:** 0.3

**Tasks:**
- [ ] 🧪 Write tests for `src/utils/logger.py`
- [ ] Implement structured JSON logging
- [ ] Add correlation ID support for request tracing
- [ ] Configure log levels per environment
- [ ] Add CloudWatch Logs integration (stub for local)
- [ ] Create logger factory for different components
- [ ] Add sensitive data masking (student IDs, API keys)

**Acceptance Criteria:**
- Logs output in JSON format
- Correlation IDs propagate through function calls
- Log levels filter correctly (DEBUG in dev, INFO in prod)
- Sensitive data is masked in logs

**Files Created:**
- `src/utils/logger.py`
- `tests/unit/test_logger.py`

---

## Phase 1: Data Layer & Storage

### 1.1 DynamoDB Client & Base Repository
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 0.4

**Tasks:**
- [ ] 🧪 Write tests for `src/data/dynamodb_client.py`
- [ ] Implement DynamoDB connection wrapper
- [ ] Add connection pooling and retry logic
- [ ] Create base repository class with CRUD operations
- [ ] Add batch read/write support
- [ ] Implement local DynamoDB setup for testing
- [ ] Add error handling for throttling, not found, etc.

**Acceptance Criteria:**
- Tests use local DynamoDB (LocalStack or DynamoDB Local)
- CRUD operations work for generic items
- Batch operations handle large datasets
- Throttling errors trigger exponential backoff

**Files Created:**
- `src/data/dynamodb_client.py`
- `src/data/repositories/base_repository.py`
- `tests/unit/test_dynamodb_client.py`
- `tests/fixtures/dynamodb_setup.py`

---

### 1.2 Student Profile Data Model & Repository
**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 1.1

**Tasks:**
- [ ] 🧪 Write tests for StudentProfile model
- [ ] Create StudentProfile Pydantic model
- [ ] Implement validation rules (grade level 6-8, etc.)
- [ ] Create StudentRepository with DynamoDB operations
- [ ] Add methods: create, get, update, delete, list by grade
- [ ] Implement vocabulary list management (add words, update counts)
- [ ] Add proficiency score calculation logic
- [ ] Create DynamoDB table schema (CloudFormation)

**Acceptance Criteria:**
- StudentProfile model validates correctly
- Repository saves/retrieves profiles from DynamoDB
- Vocabulary list operations work (add, update, dedupe)
- Proficiency score recalculates on profile update
- Table creation script runs successfully

**Files Created:**
- `src/data/models/student_profile.py`
- `src/data/repositories/student_repository.py`
- `tests/unit/test_student_profile.py`
- `tests/unit/test_student_repository.py`
- `infrastructure/cloudformation/dynamodb-tables.yaml`

**DynamoDB Table Schema:**
```yaml
StudentProfiles:
  PartitionKey: student_id (String)
  SortKey: profile_version (Number)
  Attributes: vocabulary_list, grade_level, proficiency_score, etc.
  GSI: grade_level-proficiency_score-index
```

---

### 1.3 Vocabulary Recommendation Data Model & Repository
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 1.1

**Tasks:**
- [ ] 🧪 Write tests for VocabularyRecommendation model
- [ ] Create VocabularyRecommendation Pydantic model
- [ ] Implement RecommendationRepository
- [ ] Add methods: create, get by student, get by date range
- [ ] Implement TTL (30-day expiration) on recommendations
- [ ] Add status tracking (pending, assigned, learned)
- [ ] Create DynamoDB table schema

**Acceptance Criteria:**
- Recommendation model validates word lists correctly
- Repository handles CRUD operations
- TTL automatically expires old recommendations
- Status updates work correctly

**Files Created:**
- `src/data/models/recommendation.py`
- `src/data/repositories/recommendation_repository.py`
- `tests/unit/test_recommendation.py`
- `tests/unit/test_recommendation_repository.py`
- `infrastructure/cloudformation/dynamodb-tables.yaml` (updated)

---

### 1.4 S3 Client & File Operations
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 0.4

**Tasks:**
- [ ] 🧪 Write tests for `src/data/s3_client.py`
- [ ] Implement S3 client wrapper with boto3
- [ ] Add methods: upload, download, list, delete
- [ ] Implement multipart upload for large files
- [ ] Add presigned URL generation for secure downloads
- [ ] Create S3 bucket structure management
- [ ] Add error handling for access denied, not found, etc.
- [ ] Use LocalStack S3 for testing

**Acceptance Criteria:**
- Tests use LocalStack S3
- Upload/download operations work for text files
- Presigned URLs generate correctly
- File organization follows architecture.md structure

**Files Created:**
- `src/data/s3_client.py`
- `tests/unit/test_s3_client.py`
- `tests/fixtures/sample_transcripts/` (mock data)

---

### 1.5 Common Core Vocabulary Database
**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 1.1

**Tasks:**
- [ ] Research and source Common Core vocabulary lists (grades 6-8)
- [ ] Create vocabulary corpus JSON files
- [ ] 🧪 Write tests for vocabulary loader
- [ ] Implement `src/vocabulary/common_core_loader.py`
- [ ] Create grade-level mapping utilities
- [ ] Load vocabulary into DynamoDB (seed script)
- [ ] Add word family and synonym grouping
- [ ] Implement fast vocabulary lookup methods

**Acceptance Criteria:**
- At least 500 words per grade level (6, 7, 8)
- Vocabulary loads into DynamoDB successfully
- Lookup by word or grade level works
- Words include definitions and subject areas

**Files Created:**
- `src/vocabulary/corpus/common_core_grade_6.json`
- `src/vocabulary/corpus/common_core_grade_7.json`
- `src/vocabulary/corpus/common_core_grade_8.json`
- `src/vocabulary/common_core_loader.py`
- `src/vocabulary/grade_level_mapper.py`
- `tests/unit/test_common_core_loader.py`
- `scripts/seed_vocabulary_db.py`

**Sample Corpus Entry:**
```json
{
  "word": "analyze",
  "grade_level": 6,
  "definition": "examine in detail to understand",
  "subject_areas": ["math", "science", "ela"],
  "complexity_tier": 2,
  "word_family": ["analysis", "analytical", "analyzer"]
}
```

---

## Phase 2: AI/ML Layer

### 2.1 OpenAI Client Wrapper
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 0.4

**Tasks:**
- [ ] 🧪 Write tests for OpenAI client (mock API responses)
- [ ] Implement `src/ai/openai_client.py` wrapper
- [ ] Add retry logic with exponential backoff
- [ ] Implement rate limit handling
- [ ] Add request/response logging (sanitized)
- [ ] Create cost tracking per request
- [ ] Support both GPT-4o and GPT-4o-mini models
- [ ] Add timeout configuration

**Acceptance Criteria:**
- Tests use mocked OpenAI responses
- Retry logic handles transient failures
- Rate limits trigger backoff
- Cost tracking logs token usage
- Both models callable via unified interface

**Files Created:**
- `src/ai/openai_client.py`
- `src/ai/cost_tracker.py`
- `tests/unit/test_openai_client.py`
- `tests/mocks/mock_openai.py`

---

### 2.2 Vocabulary Extraction Prompts & Logic
**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 2.1

**Tasks:**
- [ ] 🧪 Write tests for vocabulary extraction (sample inputs/outputs)
- [ ] Design extraction prompt template
- [ ] Implement `src/ai/prompts/extraction.py`
- [ ] Create text preprocessing utilities (chunking, cleaning)
- [ ] Add word deduplication and normalization
- [ ] Implement context capture for each word
- [ ] Add filtering logic (exclude common words, grade-inappropriate)
- [ ] Optimize for GPT-4o-mini usage

**Acceptance Criteria:**
- Tests verify extraction from sample transcripts
- Extracted words are normalized (lowercase, lemmatized)
- Context sentences captured for each word
- Common stopwords filtered out
- Handles texts up to 10,000 words

**Files Created:**
- `src/ai/prompts/extraction.py`
- `src/processing/text_analyzer.py`
- `tests/unit/test_vocabulary_extraction.py`
- `tests/fixtures/sample_transcripts/student_001.txt`

**Sample Prompt:**
```python
system_prompt = """
You are a vocabulary extraction specialist for middle school education.

Task: Extract all academically significant words from the student text.

Exclude:
- Common function words (the, a, an, is, are, was, were)
- Words below 3rd grade level
- Proper nouns (names, places) unless academically relevant

For each word, provide:
- The word (lemmatized form)
- Number of times used
- One example sentence showing usage

Output format: JSON
"""
```

---

### 2.3 Vocabulary Gap Analysis Prompts & Logic
**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 2.2, 1.5

**Tasks:**
- [ ] 🧪 Write tests for gap analysis
- [ ] Design gap analysis prompt template
- [ ] Implement `src/ai/prompts/gap_analysis.py`
- [ ] Create `src/processing/gap_identifier.py`
- [ ] Compare student vocabulary against Common Core standards
- [ ] Implement Zone of Proximal Development (ZPD) logic
- [ ] Score word difficulty relative to student level
- [ ] Identify 10-15 target words per student

**Acceptance Criteria:**
- Gap analysis correctly identifies missing Common Core words
- Recommended words are slightly above current level
- Difficulty scoring aligns with grade levels
- Tests verify ZPD logic with sample profiles

**Files Created:**
- `src/ai/prompts/gap_analysis.py`
- `src/processing/gap_identifier.py`
- `tests/unit/test_gap_identifier.py`

**Sample Prompt:**
```python
system_prompt = """
You are a vocabulary assessment expert specializing in Zone of Proximal Development.

Student Profile:
- Grade: {grade}
- Current vocabulary size: {vocab_size}
- Recently used words: {recent_words}

Common Core Standards:
- Expected words for grade {grade}: {cc_words}

Task: Identify 10-15 words that are:
1. Missing from student's current vocabulary
2. Present in Common Core standards
3. Slightly above current level (ZPD)
4. High-utility across subjects

Output: JSON with word, rationale, difficulty_score (1-10)
"""
```

---

### 2.4 Word Recommendation Generation
**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 2.3

**Tasks:**
- [ ] 🧪 Write tests for recommendation generation
- [ ] Design recommendation prompt template
- [ ] Implement `src/ai/prompts/recommendation.py`
- [ ] Create `src/processing/recommender.py`
- [ ] Generate pedagogically sound word recommendations
- [ ] Include definitions, example sentences, usage tips
- [ ] Add difficulty progression (easiest to hardest)
- [ ] Format output for teacher consumption

**Acceptance Criteria:**
- Recommendations include 10-15 words
- Each word has definition and examples
- Words ordered by difficulty
- Output format matches DynamoDB schema

**Files Created:**
- `src/ai/prompts/recommendation.py`
- `src/processing/recommender.py`
- `tests/unit/test_recommender.py`

**Sample Output:**
```json
{
  "student_id": "STU-001",
  "recommendations": [
    {
      "word": "analyze",
      "definition": "examine in detail to understand",
      "difficulty_score": 5,
      "rationale": "High-frequency academic word across subjects",
      "example_sentences": [
        "Scientists analyze data to find patterns.",
        "Let's analyze the author's argument."
      ]
    }
  ]
}
```

---

## Phase 3: Processing Layer

### 3.1 Text Processing Pipeline
**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 2.2, 2.3, 2.4

**Tasks:**
- [ ] �� Write tests for end-to-end text processing
- [ ] Implement `src/processing/text_analyzer.py` (complete)
- [ ] Create pipeline: load → extract → analyze → recommend
- [ ] Add progress tracking for long-running jobs
- [ ] Implement error recovery (partial processing)
- [ ] Add result caching to avoid reprocessing
- [ ] Log metrics (tokens used, processing time, cost)

**Acceptance Criteria:**
- Pipeline processes sample transcript end-to-end
- Results saved to S3 and DynamoDB
- Errors are caught and logged without crashing
- Metrics logged for observability

**Files Created:**
- `src/processing/text_analyzer.py` (updated)
- `src/processing/pipeline.py`
- `tests/integration/test_text_pipeline.py`

---

### 3.2 Parallel Processing Executor
**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 3.1

**Tasks:**
- [ ] 🧪 Write tests for parallel execution
- [ ] Implement `src/processing/parallel_executor.py`
- [ ] Add Python multiprocessing for local parallel execution
- [ ] Create job queue management
- [ ] Implement worker pool with configurable size
- [ ] Add job status tracking (pending, running, completed, failed)
- [ ] Handle partial failures gracefully
- [ ] Add progress reporting

**Acceptance Criteria:**
- Processes multiple students in parallel (local testing)
- Job status updates correctly
- Failed jobs don't block successful ones
- Progress visible in logs

**Files Created:**
- `src/processing/parallel_executor.py`
- `tests/unit/test_parallel_executor.py`
- `tests/integration/test_batch_processing.py`

---

### 3.3 AWS Batch Integration
**Priority:** 🔴 P0 ⚙️
**Estimated Time:** 8-10 hours
**Dependencies:** 3.2

**Tasks:**
- [ ] Create Dockerfile for batch processing container
- [ ] Implement batch job entry point script
- [ ] Create `src/processing/batch_processor.py`
- [ ] Add AWS Batch job submission logic
- [ ] Implement job status polling
- [ ] Create CloudFormation templates for Batch resources
- [ ] Configure Fargate compute environment
- [ ] Add job completion notifications (SNS)
- [ ] Test with LocalStack or dev AWS account

**Acceptance Criteria:**
- Docker image builds successfully
- Batch job can be submitted via Python script
- Job runs on Fargate and completes
- Results written to S3 and DynamoDB
- CloudFormation creates all required resources

**Files Created:**
- `infrastructure/docker/Dockerfile.batch`
- `src/processing/batch_processor.py`
- `scripts/submit_batch_job.py`
- `infrastructure/cloudformation/batch-processing.yaml`
- `tests/integration/test_aws_batch.py`

**CloudFormation Resources:**
- AWS Batch compute environment (Fargate)
- Job queue
- Job definition
- IAM roles

---

## Phase 4: API Layer

### 4.1 FastAPI Application Setup
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 0.4

**Tasks:**
- [ ] 🧪 Write tests for FastAPI app initialization
- [ ] Create `src/api/main.py` with FastAPI app
- [ ] Configure CORS middleware
- [ ] Add request logging middleware
- [ ] Implement health check endpoint (`/health`)
- [ ] Add OpenAPI documentation customization
- [ ] Configure exception handlers
- [ ] Add request validation middleware

**Acceptance Criteria:**
- FastAPI app starts successfully
- `/docs` shows OpenAPI documentation
- `/health` returns 200 OK
- Invalid requests return 422 with clear errors

**Files Created:**
- `src/api/main.py`
- `src/api/middleware/logging.py`
- `tests/unit/test_api_main.py`

---

### 4.2 Request/Response Models
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 1.2, 1.3

**Tasks:**
- [ ] 🧪 Write tests for Pydantic models
- [ ] Create request models in `src/api/models/requests.py`
- [ ] Create response models in `src/api/models/responses.py`
- [ ] Add validation rules (student ID format, file size limits)
- [ ] Implement example values for documentation
- [ ] Add error response models
- [ ] Create model serialization helpers

**Acceptance Criteria:**
- All API models validate correctly
- OpenAPI docs show example requests/responses
- Validation errors are user-friendly

**Files Created:**
- `src/api/models/requests.py`
- `src/api/models/responses.py`
- `tests/unit/test_api_models.py`

**Sample Models:**
```python
class TranscriptUploadRequest(BaseModel):
    student_id: str = Field(..., pattern=r"^STU-\d{3}$")
    text: str = Field(..., min_length=10, max_length=50000)
    session_date: date

class StudentProfileResponse(BaseModel):
    student_id: str
    grade_level: int
    vocabulary_size: int
    proficiency_score: float
    last_updated: datetime
```

---

### 4.3 Upload Endpoints (Transcripts & Writing)
**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 4.1, 4.2, 1.4, 3.1

**Tasks:**
- [ ] 🧪 Write tests for upload endpoints
- [ ] Implement `POST /api/v1/transcripts/upload`
- [ ] Implement `POST /api/v1/writing/upload`
- [ ] Add file validation (size, format)
- [ ] Upload raw text to S3
- [ ] Trigger vocabulary extraction
- [ ] Update student profile
- [ ] Return processing status
- [ ] Add rate limiting (optional)

**Acceptance Criteria:**
- Uploads save files to S3
- Vocabulary extraction runs successfully
- Student profiles update in DynamoDB
- API returns success response with profile URL

**Files Created:**
- `src/api/routes/upload.py`
- `tests/integration/test_upload_endpoints.py`

---

### 4.4 Student Profile Endpoints
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 4.1, 4.2, 1.2

**Tasks:**
- [ ] 🧪 Write tests for profile endpoints
- [ ] Implement `GET /api/v1/students/{student_id}/profile`
- [ ] Implement `GET /api/v1/students` (list by grade, optional)
- [ ] Add pagination for list endpoints
- [ ] Add filtering and sorting options
- [ ] Return formatted profile data
- [ ] Handle not found errors

**Acceptance Criteria:**
- Profile endpoint returns complete student data
- List endpoint supports pagination
- Not found returns 404 with clear message

**Files Created:**
- `src/api/routes/profiles.py`
- `tests/integration/test_profile_endpoints.py`

---

### 4.5 Recommendation Endpoints
**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 4.1, 4.2, 1.3

**Tasks:**
- [ ] 🧪 Write tests for recommendation endpoints
- [ ] Implement `GET /api/v1/students/{student_id}/recommendations`
- [ ] Add filtering by date range
- [ ] Add filtering by status (pending, assigned, learned)
- [ ] Implement `PATCH /api/v1/recommendations/{id}/status` (update status)
- [ ] Return formatted recommendation data
- [ ] Handle expired recommendations (TTL)

**Acceptance Criteria:**
- Recommendations endpoint returns word lists
- Filtering works correctly
- Status updates persist to DynamoDB

**Files Created:**
- `src/api/routes/recommendations.py`
- `tests/integration/test_recommendation_endpoints.py`

---

### 4.6 Batch Processing Endpoints
**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 4.1, 4.2, 3.3

**Tasks:**
- [ ] 🧪 Write tests for batch endpoints
- [ ] Implement `POST /api/v1/batch/process`
- [ ] Accept list of student IDs or S3 paths
- [ ] Submit AWS Batch job
- [ ] Return job ID for tracking
- [ ] Implement `GET /api/v1/batch/{job_id}/status`
- [ ] Return job progress and results
- [ ] Add webhook support for job completion (optional)

**Acceptance Criteria:**
- Batch endpoint submits AWS Batch job
- Status endpoint returns current job state
- Completed jobs return result URLs

**Files Created:**
- `src/api/routes/batch.py`
- `tests/integration/test_batch_endpoints.py`

---

## Phase 5: Frontend Layer

### 5.1 HTML Report Templates
**Priority:** 🔴 P0
**Estimated Time:** 6-8 hours
**Dependencies:** 1.2, 1.3

**Tasks:**
- [ ] Create student profile HTML template (Jinja2)
- [ ] Create recommendations HTML template
- [ ] Add minimal CSS styling (responsive design)
- [ ] Add simple JavaScript for interactivity (optional)
- [ ] Include Chart.js for vocabulary growth visualization
- [ ] Make templates print-friendly
- [ ] Add export to PDF option (future)

**Acceptance Criteria:**
- Templates render with sample data
- Reports are readable on mobile and desktop
- Print layout looks professional

**Files Created:**
- `src/frontend/templates/student_profile.html`
- `src/frontend/templates/recommendations.html`
- `src/frontend/static/css/styles.css`
- `src/frontend/static/js/charts.js`

**Report Sections:**
- Student profile report: ID, grade, vocabulary size, proficiency score, recent words, growth chart
- Recommendations report: Word list, definitions, examples, difficulty scores

---

### 5.2 Report Generation Service
**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 5.1, 1.2, 1.3

**Tasks:**
- [ ] 🧪 Write tests for report generator
- [ ] Implement `src/frontend/generator.py`
- [ ] Fetch data from DynamoDB
- [ ] Render Jinja2 templates
- [ ] Generate static HTML files
- [ ] Upload reports to S3
- [ ] Generate presigned URLs for access
- [ ] Add report caching logic

**Acceptance Criteria:**
- Generator creates valid HTML from templates
- Reports upload to S3 successfully
- Presigned URLs allow temporary access

**Files Created:**
- `src/frontend/generator.py`
- `tests/unit/test_report_generator.py`

---

## Phase 6: Infrastructure & Deployment

### 6.1 CloudFormation Templates
**Priority:** 🔴 P0 ⚙️
**Estimated Time:** 10-12 hours
**Dependencies:** All previous phases

**Tasks:**
- [ ] Create API Gateway + Lambda CloudFormation template
- [ ] Create DynamoDB tables template (from 1.2, 1.3)
- [ ] Create S3 buckets template
- [ ] Create AWS Batch + Fargate template (from 3.3)
- [ ] Create IAM roles and policies template
- [ ] Create CloudWatch Logs and alarms template
- [ ] Create master stack template (nested stacks)
- [ ] Add parameter validation and defaults
- [ ] Document all template parameters

**Acceptance Criteria:**
- All templates validate with `aws cloudformation validate-template`
- Stacks deploy successfully to AWS dev account
- Resources are tagged appropriately
- IAM policies follow least-privilege principle

**Files Created:**
- `infrastructure/cloudformation/api-gateway.yaml`
- `infrastructure/cloudformation/lambda-functions.yaml`
- `infrastructure/cloudformation/dynamodb-tables.yaml`
- `infrastructure/cloudformation/s3-buckets.yaml`
- `infrastructure/cloudformation/batch-processing.yaml`
- `infrastructure/cloudformation/iam-roles.yaml`
- `infrastructure/cloudformation/monitoring.yaml`
- `infrastructure/cloudformation/master-stack.yaml`

---

### 6.2 Lambda Deployment Package
**Priority:** 🔴 P0 ⚙️
**Estimated Time:** 4-5 hours
**Dependencies:** 4.1-4.6

**Tasks:**
- [ ] Create Lambda Dockerfile (if using container images)
- [ ] Or create deployment script for zip packages
- [ ] Include all Python dependencies
- [ ] Configure Lambda handler entry points
- [ ] Add environment variable configuration
- [ ] Optimize package size (exclude dev dependencies)
- [ ] Test Lambda locally with SAM CLI (optional)

**Acceptance Criteria:**
- Lambda deployment package < 50MB
- Lambda functions execute successfully in AWS
- Environment variables load correctly

**Files Created:**
- `infrastructure/docker/Dockerfile.lambda` (or)
- `scripts/build_lambda_package.sh`
- `src/api/lambda_handler.py`

---

### 6.3 CI/CD Pipeline (GitHub Actions)
**Priority:** 🟡 P1 ⚙️
**Estimated Time:** 6-8 hours
**Dependencies:** 6.1, 6.2

**Tasks:**
- [ ] Create GitHub Actions workflow for tests
- [ ] Add linting step (black, ruff, mypy)
- [ ] Add test coverage reporting (pytest-cov)
- [ ] Create deployment workflow for staging
- [ ] Create deployment workflow for production
- [ ] Add manual approval gate for production
- [ ] Configure AWS credentials securely (OIDC)
- [ ] Add deployment status badges to README

**Acceptance Criteria:**
- Tests run automatically on every PR
- Deployment to staging happens on merge to main
- Production deployment requires manual approval
- Failed tests block deployment

**Files Created:**
- `.github/workflows/test.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`

**Workflow Steps:**
```yaml
# test.yml
- Checkout code
- Set up Python
- Install dependencies
- Run black, ruff, mypy
- Run pytest with coverage
- Upload coverage to CodeCov
```

---

### 6.4 Monitoring & Alerting Setup
**Priority:** 🟡 P1 ⚙️
**Estimated Time:** 5-6 hours
**Dependencies:** 6.1

**Tasks:**
- [ ] Create CloudWatch dashboards
- [ ] Add custom metrics (from code)
- [ ] Configure alarms for critical metrics
- [ ] Set up SNS topics for notifications
- [ ] Configure log retention policies
- [ ] Add cost anomaly detection
- [ ] Create runbook for common issues (documentation)

**Acceptance Criteria:**
- Dashboard shows key metrics (API latency, error rate, cost)
- Alarms trigger on threshold breaches
- Notifications sent to configured email/Slack

**Files Created:**
- `infrastructure/cloudformation/monitoring.yaml` (updated)
- `_docs/runbook.md`

**Key Alarms:**
- Lambda error rate > 5%
- Batch job failure rate > 10%
- OpenAI API errors > 50/hour
- Daily AWS cost > $20

---

### 6.5 Deployment Scripts & Documentation
**Priority:** 🔴 P0 ⚙️ 📝
**Estimated Time:** 4-5 hours
**Dependencies:** 6.1, 6.2

**Tasks:**
- [ ] Create `scripts/deploy.sh` for full deployment
- [ ] Create `scripts/destroy.sh` for teardown
- [ ] Add deployment pre-flight checks
- [ ] Document deployment process in README
- [ ] Add rollback instructions
- [ ] Create deployment troubleshooting guide
- [ ] Add environment-specific configuration docs

**Acceptance Criteria:**
- `scripts/deploy.sh` deploys all infrastructure
- README has clear deployment instructions
- Rollback procedure documented and tested

**Files Created:**
- `scripts/deploy.sh`
- `scripts/destroy.sh`
- `scripts/preflight_check.sh`
- `README.md` (updated)
- `_docs/deployment-guide.md`

---

## Phase 7: Testing & Quality Assurance

### 7.1 Integration Test Suite
**Priority:** 🔴 P0 🧪
**Estimated Time:** 8-10 hours
**Dependencies:** All API endpoints, processing logic

**Tasks:**
- [ ] Create end-to-end test scenarios
- [ ] Test: Upload transcript → Extract vocabulary → Generate recommendations
- [ ] Test: Batch processing workflow
- [ ] Test: Profile retrieval and updates
- [ ] Use real AWS resources (dev account) or LocalStack
- [ ] Add test data fixtures and factories
- [ ] Implement test cleanup (delete test data after)

**Acceptance Criteria:**
- All integration tests pass
- Tests cover happy path and error scenarios
- Test coverage > 60%

**Files Created:**
- `tests/integration/test_end_to_end.py`
- `tests/integration/test_api_workflows.py`
- `tests/integration/test_batch_workflows.py`

---

### 7.2 Performance Testing
**Priority:** 🟡 P1
**Estimated Time:** 5-6 hours
**Dependencies:** 7.1

**Tasks:**
- [ ] Create load test scripts (Locust or K6)
- [ ] Test API endpoint response times
- [ ] Test batch processing throughput
- [ ] Measure OpenAI API latency
- [ ] Document performance results
- [ ] Identify bottlenecks

**Acceptance Criteria:**
- API P95 latency < 500ms
- Batch processing handles 30 students in < 15 minutes
- Performance report generated

**Files Created:**
- `tests/performance/locustfile.py`
- `_docs/performance-results.md`

---

### 7.3 Security Audit & Fixes
**Priority:** 🟡 P1
**Estimated Time:** 4-5 hours
**Dependencies:** All infrastructure, API code

**Tasks:**
- [ ] Run security linters (bandit, safety)
- [ ] Review IAM policies for least privilege
- [ ] Check for hardcoded secrets in code
- [ ] Validate input sanitization in API
- [ ] Test API authentication/authorization
- [ ] Review S3 bucket policies
- [ ] Document security best practices

**Acceptance Criteria:**
- No critical security vulnerabilities found
- All secrets managed via environment variables or AWS Secrets Manager
- IAM policies follow least privilege

**Files Created:**
- `.github/workflows/security.yml`
- `_docs/security-guidelines.md`

---

## Phase 8: Documentation & Polish

### 8.1 API Documentation
**Priority:** 🔴 P0 📝
**Estimated Time:** 3-4 hours
**Dependencies:** All API endpoints

**Tasks:**
- [ ] Review and enhance OpenAPI documentation
- [ ] Add detailed descriptions for all endpoints
- [ ] Add request/response examples
- [ ] Document authentication requirements
- [ ] Add rate limiting information
- [ ] Create Postman collection (optional)

**Acceptance Criteria:**
- `/docs` endpoint shows complete API documentation
- All endpoints have clear descriptions and examples

**Files Created:**
- `_docs/api-documentation.md`
- `postman_collection.json` (optional)

---

### 8.2 Developer Onboarding Guide
**Priority:** 🟡 P1 📝
**Estimated Time:** 4-5 hours
**Dependencies:** All development phases complete

**Tasks:**
- [ ] Write step-by-step setup guide
- [ ] Document common development tasks
- [ ] Add troubleshooting section
- [ ] Document testing procedures
- [ ] Add contribution guidelines
- [ ] Create architecture diagrams (draw.io or similar)

**Acceptance Criteria:**
- New developer can set up project in < 30 minutes
- All common tasks documented
- Troubleshooting covers common issues

**Files Created:**
- `_docs/developer-guide.md`
- `CONTRIBUTING.md`
- `_docs/troubleshooting.md`

---

### 8.3 User Documentation (Teachers)
**Priority:** 🟡 P1 📝
**Estimated Time:** 3-4 hours
**Dependencies:** Frontend complete

**Tasks:**
- [ ] Write teacher user guide
- [ ] Document how to upload transcripts
- [ ] Explain vocabulary reports
- [ ] Add FAQ section
- [ ] Create video walkthrough (optional)
- [ ] Document privacy and COPPA compliance

**Acceptance Criteria:**
- Teachers can use system without technical support
- All features documented with screenshots

**Files Created:**
- `_docs/teacher-user-guide.md`
- `_docs/faq.md`
- `_docs/privacy-policy.md`

---

### 8.4 README & Project Overview
**Priority:** 🔴 P0 📝
**Estimated Time:** 2-3 hours
**Dependencies:** All phases complete

**Tasks:**
- [ ] Update README.md with project overview
- [ ] Add architecture diagram
- [ ] Add setup instructions (link to developer guide)
- [ ] Add usage examples
- [ ] Add badges (build status, coverage, license)
- [ ] Add contributing guidelines link
- [ ] Add license information

**Acceptance Criteria:**
- README provides clear project overview
- Quick start guide gets developer running quickly
- Links to detailed documentation

**Files Created:**
- `README.md` (updated)
- `LICENSE` (if not exists)

---

## Phase 9: MVP Launch Preparation

### 9.1 Test Data Generation
**Priority:** 🔴 P0
**Estimated Time:** 4-5 hours
**Dependencies:** All data models

**Tasks:**
- [ ] Create realistic mock student transcripts (50+ samples)
- [ ] Create mock writing samples (20+ samples)
- [ ] Generate mock student profiles across grades 6-8
- [ ] Seed development database with test data
- [ ] Document test data structure

**Acceptance Criteria:**
- At least 50 mock transcripts of varying quality
- Test data represents diverse vocabulary levels
- Seed script populates database successfully

**Files Created:**
- `tests/fixtures/sample_transcripts/*.txt` (50+ files)
- `tests/fixtures/sample_writing/*.txt` (20+ files)
- `scripts/seed_test_data.py`

---

### 9.2 Demo Environment Setup
**Priority:** 🟡 P1 ⚙️
**Estimated Time:** 3-4 hours
**Dependencies:** 6.1, 9.1

**Tasks:**
- [ ] Deploy to demo AWS environment
- [ ] Load test data into demo
- [ ] Create demo user accounts (if auth implemented)
- [ ] Test all workflows in demo
- [ ] Create demo walkthrough script

**Acceptance Criteria:**
- Demo environment fully functional
- Pre-loaded with realistic data
- Accessible to stakeholders

---

### 9.3 Cost Optimization Review
**Priority:** 🟡 P1
**Estimated Time:** 3-4 hours
**Dependencies:** All infrastructure deployed

**Tasks:**
- [ ] Review OpenAI API usage and optimize prompts
- [ ] Review AWS resource sizing (Lambda memory, Fargate CPU)
- [ ] Implement response caching where appropriate
- [ ] Add request batching for OpenAI API
- [ ] Set up cost budgets and alarms
- [ ] Document cost optimization strategies

**Acceptance Criteria:**
- Cost estimates validated with real usage
- Optimization strategies documented
- Cost alarms configured

**Files Created:**
- `_docs/cost-optimization.md`

---

### 9.4 Launch Checklist & Go/No-Go
**Priority:** 🔴 P0 📝
**Estimated Time:** 2-3 hours
**Dependencies:** All MVP tasks

**Tasks:**
- [ ] Create MVP launch checklist
- [ ] Verify all P0 tasks complete
- [ ] Run final end-to-end tests
- [ ] Verify monitoring and alerting works
- [ ] Confirm rollback procedure tested
- [ ] Get stakeholder sign-off
- [ ] Schedule launch date

**Acceptance Criteria:**
- All P0 requirements met
- All tests passing
- Stakeholders approve launch

**Files Created:**
- `_docs/launch-checklist.md`
- `_docs/launch-retrospective.md` (after launch)

---

## Task Summary by Priority

### 🔴 P0 (Must-Have) - 63 tasks
- Phase 0: Project Setup (4 tasks)
- Phase 1: Data Layer (5 tasks)
- Phase 2: AI/ML Layer (4 tasks)
- Phase 3: Processing Layer (3 tasks)
- Phase 4: API Layer (6 tasks)
- Phase 5: Frontend Layer (2 tasks)
- Phase 6: Infrastructure (3 tasks)
- Phase 7: Testing (1 task)
- Phase 8: Documentation (2 tasks)
- Phase 9: Launch Prep (2 tasks)

### 🟡 P1 (Should-Have) - 8 tasks
- Phase 6: CI/CD, Monitoring (2 tasks)
- Phase 7: Performance, Security (2 tasks)
- Phase 8: Documentation (2 tasks)
- Phase 9: Demo, Cost Optimization (2 tasks)

### 🟢 P2 (Could-Have) - 0 tasks
- Post-MVP enhancements (see architecture.md)

---

## Estimated Timeline

**Assumptions:**
- 1 full-time developer
- 40 hours/week
- Working in order of phases

| Phase | Duration | Total Hours |
|-------|----------|-------------|
| Phase 0: Setup | 2-3 days | 12-16 hours |
| Phase 1: Data Layer | 4-5 days | 30-36 hours |
| Phase 2: AI/ML Layer | 4-5 days | 26-32 hours |
| Phase 3: Processing | 3-4 days | 22-28 hours |
| Phase 4: API Layer | 4-5 days | 28-34 hours |
| Phase 5: Frontend | 2-3 days | 12-16 hours |
| Phase 6: Infrastructure | 4-5 days | 30-36 hours |
| Phase 7: Testing | 3-4 days | 20-24 hours |
| Phase 8: Documentation | 2-3 days | 12-16 hours |
| Phase 9: Launch Prep | 2-3 days | 14-18 hours |

**Total MVP Time: 6-8 weeks (200-260 hours)**

---

## Dependencies Graph

```
Phase 0 (Setup)
  └─> Phase 1 (Data Layer)
      └─> Phase 2 (AI/ML Layer)
          └─> Phase 3 (Processing Layer)
              └─> Phase 4 (API Layer)
                  └─> Phase 5 (Frontend Layer)
                      └─> Phase 6 (Infrastructure)
                          └─> Phase 7 (Testing)
                              └─> Phase 8 (Documentation)
                                  └─> Phase 9 (Launch)
```

**Parallelization Opportunities:**
- Phase 1 & Phase 2 can overlap (after 0.4 complete)
- Phase 5 can start once data models are stable (after 1.2, 1.3)
- Phase 8 documentation can be written throughout development

---

## Progress Tracking

**Recommended tools:**
- GitHub Projects for task tracking
- Memory Bank (`memory-bank/progress.md`) for feature completion
- Weekly status updates in `memory-bank/activeContext.md`

**Definition of Done (per task):**
- [ ] Tests written and passing (if 🧪 marked)
- [ ] Code reviewed (if team > 1)
- [ ] Linting passes (black, ruff, mypy)
- [ ] Documentation updated
- [ ] Memory Bank updated
- [ ] Committed to git

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OpenAI API costs higher than expected | Implement daily cost monitoring, optimize prompts early |
| Common Core vocabulary hard to source | Start with simplified corpus, enhance later |
| AWS infrastructure complex | Use AWS SAM for simpler deployment, defer advanced features |
| Test coverage insufficient | Enforce 60% coverage gate in CI/CD |
| Timeline slips | Focus on P0 tasks only for MVP, defer P1/P2 |

---

## Post-MVP Roadmap

After MVP launch, consider these enhancements (see architecture.md Phase 2/3):
- Real-time speech-to-text integration
- React-based teacher dashboard
- Advanced analytics and predictive models
- Gamified student vocabulary challenges
- Mobile app development

---

**Document Status:** Ready for Development
**Next Review Date:** After Phase 3 completion (mid-sprint review)
**Owner:** Technical Lead
**Last Updated:** 2025-11-10
