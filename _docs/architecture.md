# Vocabulator System Architecture

**Project:** Personalized Vocabulary Recommendation Engine for Middle School Students
**Organization:** Flourish Schools
**Version:** 1.0.0 (MVP)
**Last Updated:** 2025-11-10

---

## Executive Summary

This document defines the technical architecture for Vocabulator, an AI-powered system that analyzes student transcripts and writing samples to identify vocabulary gaps and generate personalized word recommendations for middle school students. The architecture prioritizes simplicity for MVP while enabling future scalability.

---

## Architecture Principles

1. **Serverless-First**: Minimize infrastructure management using AWS managed services
2. **Privacy-by-Design**: Anonymous student identifiers, no PII collection
3. **Cost-Conscious**: Pay-per-use model with OpenAI API cost optimization
4. **Test-Driven**: All components built using test-first development workflow
5. **Modular**: Clear separation between data ingestion, processing, analysis, and presentation layers

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Static HTML/CSS Reports (S3 + CloudFront)              │  │
│  │  - Student vocabulary profiles                           │  │
│  │  - Recommended word lists                                │  │
│  │  - Progress tracking visualizations                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AWS Lambda + API Gateway                                │  │
│  │  - Upload transcripts/writing samples                    │  │
│  │  - Retrieve student vocabulary profiles                  │  │
│  │  - Get word recommendations                              │  │
│  │  - Trigger batch processing jobs                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AWS Batch + Fargate                                     │  │
│  │  - Parallel processing of full-day transcripts           │  │
│  │  - Batch vocabulary extraction                           │  │
│  │  - Gap analysis across multiple students                │  │
│  │  - Recommendation generation                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI/ML LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  OpenAI API Integration                                  │  │
│  │  - GPT-4o-mini: Vocabulary extraction & tokenization    │  │
│  │  - GPT-4o: Gap analysis & personalized recommendations  │  │
│  │  - Prompt templates for consistent analysis             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Amazon S3         │  │  Amazon DynamoDB                 │  │
│  │  - Raw transcripts │  │  - Student vocab profiles        │  │
│  │  - Writing samples │  │  - Word recommendations          │  │
│  │  - Processed texts │  │  - Progress tracking             │  │
│  │  - Static reports  │  │  - Common Core vocabulary DB     │  │
│  └────────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies
| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Runtime** | Python | 3.11+ | Specified in PRD, excellent ML/AI ecosystem |
| **AI/ML** | OpenAI SDK | Latest | Strong text analysis, per stakeholder selection |
| **API Framework** | FastAPI | 0.104+ | Modern, async-capable, auto-documentation |
| **Testing** | pytest | 7.4+ | Industry standard, extensive plugin ecosystem |
| **Data Validation** | Pydantic | 2.5+ | Type safety, data validation, FastAPI integration |

### AWS Infrastructure
| Service | Purpose | Configuration |
|---------|---------|---------------|
| **API Gateway** | REST API endpoint | Regional, request validation enabled |
| **Lambda** | API handlers | Python 3.11, 512MB-1GB memory, 30s timeout |
| **AWS Batch** | Parallel processing orchestration | Fargate compute environment |
| **Fargate** | Containerized ML workloads | 2-4 vCPU, 4-8GB memory per job |
| **S3** | Object storage | Versioning enabled, lifecycle policies |
| **DynamoDB** | NoSQL database | On-demand billing, point-in-time recovery |
| **CloudFront** | Static content CDN | S3 origin for HTML reports |
| **CloudWatch** | Logging & monitoring | Log retention: 30 days |
| **IAM** | Access control | Least-privilege policies |

### Development & Deployment
| Tool | Purpose | Version |
|------|---------|---------|
| **Docker** | Container runtime | 24.0+ |
| **AWS SAM/CDK** | Infrastructure as Code | Latest |
| **pytest-cov** | Test coverage | 4.1+ |
| **black** | Code formatting | 23.0+ |
| **ruff** | Linting | 0.1+ |
| **mypy** | Static type checking | 1.7+ |

### Python Libraries
| Library | Purpose | Version |
|---------|---------|---------|
| **openai** | OpenAI API client | 1.3+ |
| **boto3** | AWS SDK | 1.28+ |
| **spacy** | NLP preprocessing (optional) | 3.7+ |
| **pandas** | Data manipulation | 2.1+ |
| **httpx** | Async HTTP client | 0.25+ |

---

## Directory Structure

```
vocabulator/
├── .github/
│   └── workflows/
│       ├── test.yml                    # CI/CD pipeline
│       └── deploy.yml                  # Deployment automation
├── _docs/
│   ├── architecture.md                 # This file
│   ├── task-list.md                    # MVP task breakdown
│   ├── best-practices.md               # Development guidelines
│   ├── required-reading.md             # Developer onboarding
│   ├── PRD_*.md                        # Product requirements
│   └── guides/
│       ├── test-first-workflow.md      # TDD process
│       └── multi-agent-workflow.md     # AI development workflow
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py               # File upload endpoints
│   │   │   ├── profiles.py             # Student profile endpoints
│   │   │   └── recommendations.py      # Word recommendation endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── requests.py             # Pydantic request models
│   │   │   └── responses.py            # Pydantic response models
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py                 # API authentication
│   │       └── logging.py              # Request logging
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── batch_processor.py          # AWS Batch job coordinator
│   │   ├── text_analyzer.py            # Core vocabulary analysis
│   │   ├── gap_identifier.py           # Identifies vocabulary gaps
│   │   ├── recommender.py              # Generates recommendations
│   │   └── parallel_executor.py        # Parallel processing utilities
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── openai_client.py            # OpenAI API wrapper
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── extraction.py           # Vocabulary extraction prompts
│   │   │   ├── gap_analysis.py         # Gap identification prompts
│   │   │   └── recommendation.py       # Word recommendation prompts
│   │   └── cost_tracker.py             # API cost monitoring
│   ├── data/
│   │   ├── __init__.py
│   │   ├── s3_client.py                # S3 operations
│   │   ├── dynamodb_client.py          # DynamoDB operations
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── student_profile.py      # Student vocabulary profile
│   │   │   ├── vocabulary_item.py      # Individual word entry
│   │   │   └── recommendation.py       # Recommendation record
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── student_repository.py   # Student data access
│   │       └── vocab_repository.py     # Vocabulary data access
│   ├── vocabulary/
│   │   ├── __init__.py
│   │   ├── common_core_loader.py       # Load Common Core vocab lists
│   │   ├── grade_level_mapper.py       # Map words to grade levels
│   │   └── corpus/
│   │       └── common_core_*.json      # Vocabulary corpus files
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py                   # Configuration management
│   │   ├── logger.py                   # Logging utilities
│   │   └── validators.py               # Input validation
│   └── frontend/
│       ├── templates/
│       │   ├── student_profile.html    # Student profile report
│       │   └── recommendations.html    # Recommendations list
│       ├── static/
│       │   ├── css/
│       │   │   └── styles.css          # Minimal styling
│       │   └── js/
│       │       └── charts.js           # Simple visualizations
│       └── generator.py                # Static report generator
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   ├── unit/
│   │   ├── test_text_analyzer.py
│   │   ├── test_gap_identifier.py
│   │   ├── test_recommender.py
│   │   ├── test_openai_client.py
│   │   └── test_repositories.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_batch_processing.py
│   │   └── test_end_to_end.py
│   ├── fixtures/
│   │   ├── sample_transcripts/         # Mock student transcripts
│   │   └── sample_profiles.json        # Mock student data
│   └── mocks/
│       ├── mock_openai.py              # OpenAI API mocks
│       └── mock_aws.py                 # AWS service mocks
├── infrastructure/
│   ├── cloudformation/
│   │   ├── api-gateway.yaml
│   │   ├── lambda-functions.yaml
│   │   ├── batch-processing.yaml
│   │   ├── storage.yaml
│   │   └── iam-roles.yaml
│   └── docker/
│       ├── Dockerfile.batch            # Batch processing container
│       └── Dockerfile.lambda           # Lambda deployment package
├── scripts/
│   ├── setup_dev_env.sh                # Local development setup
│   ├── deploy.sh                       # Deployment script
│   ├── seed_vocabulary_db.py           # Load Common Core vocabulary
│   └── run_local_tests.sh              # Local test runner
├── memory-bank/
│   ├── activeContext.md                # Current development context
│   ├── progress.md                     # Feature completion tracking
│   ├── systemPatterns.md               # Reusable patterns
│   └── techContext.md                  # Technical decisions log
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore rules
├── requirements.txt                    # Python dependencies
├── requirements-dev.txt                # Development dependencies
├── pytest.ini                          # Pytest configuration
├── pyproject.toml                      # Python project metadata
└── README.md                           # Project overview
```

---

## Core Components

### 1. API Layer (AWS Lambda + API Gateway)

**Responsibilities:**
- Accept transcript/writing sample uploads
- Retrieve student vocabulary profiles
- Return word recommendations
- Trigger batch processing jobs

**Endpoints:**
```
POST   /api/v1/transcripts/upload
POST   /api/v1/writing/upload
GET    /api/v1/students/{student_id}/profile
GET    /api/v1/students/{student_id}/recommendations
POST   /api/v1/batch/process
GET    /api/v1/batch/{job_id}/status
```

**Key Design Decisions:**
- FastAPI for async performance and auto-generated OpenAPI docs
- Pydantic for request/response validation
- 30-second Lambda timeout (lightweight operations only)
- API Gateway request validation to reduce invalid invocations
- JWT or API key authentication (configurable)

### 2. Processing Layer (AWS Batch + Fargate)

**Responsibilities:**
- Process full-day classroom transcripts in parallel
- Extract vocabulary from multiple student samples simultaneously
- Perform batch gap analysis
- Generate recommendations for entire classrooms

**Processing Pipeline:**
```
1. Job Submission
   └─> Lambda receives batch request
   └─> Submits AWS Batch job with student IDs

2. Parallel Processing (Fargate containers)
   └─> Each container processes N students
   └─> Vocabulary extraction (GPT-4o-mini)
   └─> Profile updates (DynamoDB)

3. Gap Analysis
   └─> Compare student vocab against Common Core
   └─> Identify appropriate challenge words

4. Recommendation Generation
   └─> GPT-4o for personalized recommendations
   └─> Store results in DynamoDB
   └─> Generate static HTML reports → S3
```

**Key Design Decisions:**
- AWS Batch for job orchestration (handles queuing, retries, scaling)
- Fargate for compute (no EC2 management)
- Container image includes: Python app + dependencies
- Job parallelism: configurable (default: 10 concurrent jobs)
- Timeout: 30 minutes per job (sufficient for classroom processing)

### 3. AI/ML Layer (OpenAI Integration)

**Responsibilities:**
- Vocabulary extraction from raw text
- Semantic understanding of word usage context
- Gap identification based on proficiency level
- Personalized word recommendations

**OpenAI API Strategy:**

| Task | Model | Rationale | Est. Cost* |
|------|-------|-----------|-----------|
| Vocabulary Extraction | GPT-4o-mini | Fast, cheap, sufficient for extraction | $0.15 per 1M input tokens |
| Context Analysis | GPT-4o-mini | Simple semantic understanding | $0.15 per 1M input tokens |
| Gap Analysis | GPT-4o | Complex reasoning about proficiency | $2.50 per 1M input tokens |
| Recommendations | GPT-4o | Personalized, pedagogically sound | $2.50 per 1M input tokens |

*Approximate 2025 pricing

**Prompt Engineering Patterns:**
```python
# Vocabulary Extraction Prompt Template
system_prompt = """
You are a vocabulary extraction expert for middle school education.
Extract all unique words from the provided text, excluding:
- Common function words (the, a, an, is, are)
- Words below 3rd grade level
Output: JSON list of words with usage count
"""

# Gap Analysis Prompt Template
system_prompt = """
You are a vocabulary assessment expert.
Student current vocabulary: {student_vocab}
Grade level: {grade}
Common Core standards: {cc_vocab}

Identify 10-15 words that are:
1. Slightly above current level (ZPD - Zone of Proximal Development)
2. Relevant to grade-level Common Core standards
3. High-utility across subjects
Output: JSON with word, rationale, difficulty score
"""
```

**Cost Optimization:**
- Batch requests where possible (up to 50 students per API call)
- Cache Common Core vocabulary lookups
- Use embeddings for similarity search (reduce GPT-4o calls)
- Implement request deduplication
- Monitor daily spending with CloudWatch alarms

### 4. Data Layer

#### Amazon S3 Structure
```
vocabulator-data-{env}/
├── transcripts/
│   ├── raw/{student_id}/{date}-{session_id}.txt
│   └── processed/{student_id}/{date}-{session_id}.json
├── writing-samples/
│   ├── raw/{student_id}/{assignment_id}.txt
│   └── processed/{student_id}/{assignment_id}.json
├── reports/
│   └── {student_id}/
│       ├── profile.html
│       └── recommendations-{date}.html
└── backups/
    └── dynamodb/{table_name}/{timestamp}/
```

#### DynamoDB Tables

**Table: StudentProfiles**
```
Partition Key: student_id (String)
Sort Key: profile_version (Number)

Attributes:
- student_id: string (anonymous ID)
- grade_level: number (6-8)
- vocabulary_list: list<map>
  - word: string
  - first_seen: timestamp
  - usage_count: number
  - contexts: list<string>
- proficiency_score: number (0-100)
- last_updated: timestamp
- created_at: timestamp

Indexes:
- GSI: grade_level-proficiency_score-index
```

**Table: VocabularyRecommendations**
```
Partition Key: student_id (String)
Sort Key: recommendation_date (String)

Attributes:
- student_id: string
- recommendation_date: string (ISO 8601)
- words: list<map>
  - word: string
  - definition: string
  - grade_level: number
  - difficulty_score: number
  - rationale: string
  - example_sentences: list<string>
- status: string (pending|assigned|learned)
- generated_by: string (batch_job_id)
- expires_at: number (TTL)

Indexes:
- GSI: status-recommendation_date-index
```

**Table: CommonCoreVocabulary**
```
Partition Key: grade_level (Number)
Sort Key: word (String)

Attributes:
- grade_level: number (6-8)
- word: string
- definition: string
- subject_areas: list<string>
- complexity_tier: number (1-3)
- synonym_group: string
- word_family: list<string>
```

**Table: ProcessingJobs**
```
Partition Key: job_id (String)

Attributes:
- job_id: string (UUID)
- job_type: string (batch_transcript|single_writing)
- status: string (pending|running|completed|failed)
- student_ids: list<string>
- started_at: timestamp
- completed_at: timestamp
- error_message: string
- cost_estimate: number
- results_location: string (S3 URI)
```

### 5. Frontend Layer (Static HTML Reports)

**Responsibilities:**
- Display student vocabulary profiles
- Show recommended words with definitions
- Visualize vocabulary growth over time
- Export-friendly format for teachers

**Technology:**
- Pure HTML/CSS (no JavaScript frameworks)
- Chart.js for simple visualizations
- Responsive design (mobile-friendly)
- Hosted on S3 + CloudFront

**Report Types:**

**Student Profile Report:**
- Current vocabulary size
- Grade-level comparison
- Proficiency score
- Recent word acquisitions
- Usage patterns

**Recommendations Report:**
- 10-15 recommended words
- Definitions and example sentences
- Difficulty progression
- Practice activities (future enhancement)

**Generation Process:**
```python
# After batch processing completes
1. Fetch student profile from DynamoDB
2. Fetch recommendations from DynamoDB
3. Render HTML from Jinja2 template
4. Upload to S3: s3://bucket/reports/{student_id}/profile.html
5. Return CloudFront URL to teacher
```

---

## Data Flow

### Scenario 1: Upload Single Writing Sample

```
1. Teacher uploads writing sample via web form
   └─> POST /api/v1/writing/upload
       Body: { student_id, text, assignment_id }

2. Lambda handler validates request
   └─> Pydantic validation
   └─> Check student exists (DynamoDB query)

3. Store raw text in S3
   └─> s3://bucket/writing-samples/raw/{student_id}/{assignment_id}.txt

4. Extract vocabulary (GPT-4o-mini)
   └─> Send text to OpenAI API
   └─> Parse response (JSON list of words)

5. Update student profile (DynamoDB)
   └─> Add new words to vocabulary_list
   └─> Update usage_count for existing words
   └─> Recalculate proficiency_score

6. Return response
   └─> { success: true, words_added: 15, profile_url: "..." }
```

### Scenario 2: Batch Process Full-Day Transcripts

```
1. Teacher uploads CSV with student transcripts
   └─> POST /api/v1/batch/process
       Body: { classroom_id, transcript_urls[] }

2. Lambda submits AWS Batch job
   └─> Job definition: vocabulator-batch-processor
   └─> Environment: student_ids, s3_paths, grade_level
   └─> Returns job_id

3. AWS Batch provisions Fargate containers
   └─> Parallel processing: 10 students per container
   └─> Each container runs text_analyzer.py

4. For each student (parallel):
   a. Fetch transcript from S3
   b. Extract vocabulary (GPT-4o-mini)
   c. Update profile (DynamoDB)
   d. Identify gaps vs. Common Core (GPT-4o)
   e. Generate recommendations (GPT-4o)
   f. Store recommendations (DynamoDB)
   g. Generate HTML report (Jinja2)
   h. Upload report to S3

5. Job completion callback
   └─> Lambda receives completion event
   └─> Send email/notification to teacher
   └─> Update ProcessingJobs table

6. Teacher accesses results
   └─> GET /api/v1/batch/{job_id}/status
   └─> Returns report URLs for all students
```

---

## Security & Privacy

### COPPA Compliance Strategy

**Core Principle:** Anonymous Processing - No PII Collection

**Implementation:**
1. **Schools assign anonymous student IDs** (e.g., "STU-2024-6A-001")
2. **System never requests or stores:**
   - Student names
   - Birthdates
   - Email addresses
   - Photos
   - Any other PII

3. **Vocabulary profiles are educational records** under FERPA
   - Handled by school's existing FERPA policies
   - Schools retain control of student data
   - System is a "school official" service provider

4. **Data retention:**
   - Transcripts: 90 days (S3 lifecycle policy)
   - Profiles: Active student period + 1 year
   - Recommendations: 30 days (DynamoDB TTL)

5. **Documentation:**
   - Privacy policy clearly states anonymous processing
   - Data Processing Agreement (DPA) with schools
   - FERPA compliance attestation

### AWS Security Best Practices

1. **IAM Policies:**
   - Least-privilege access
   - Separate roles for Lambda, Batch, developers
   - No long-term credentials (use IAM roles)

2. **Data Encryption:**
   - S3: Server-side encryption (SSE-S3)
   - DynamoDB: Encryption at rest enabled
   - API Gateway: HTTPS only, TLS 1.2+
   - Lambda environment variables: AWS KMS encryption

3. **Network Security:**
   - API Gateway: Request throttling, API keys
   - Lambda: VPC deployment (optional for production)
   - S3: Bucket policies restricting access
   - CloudFront: AWS WAF integration (optional)

4. **Monitoring:**
   - CloudWatch Logs: All API requests logged
   - CloudTrail: All AWS API calls logged
   - Alarms: Failed authentication, unusual API usage
   - Cost alarms: Daily spending thresholds

---

## Performance & Scalability

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time | < 500ms | P95 latency |
| Single Writing Sample Processing | < 10 seconds | End-to-end |
| Batch Job (30 students) | < 15 minutes | Total job time |
| Report Generation | < 5 seconds | Per student |
| DynamoDB Read Latency | < 10ms | P99 |

### Scalability Design

**API Layer:**
- Lambda: Auto-scales to 1000 concurrent invocations
- API Gateway: 10,000 requests per second (default regional limit)
- Can handle 100+ schools without configuration changes

**Processing Layer:**
- AWS Batch: Scales to 100+ concurrent jobs
- Fargate: Each job can process 10-50 students
- Theoretical limit: 5,000+ students processed simultaneously

**Data Layer:**
- S3: Unlimited storage, 5,500 GET/3,500 PUT per second per prefix
- DynamoDB: On-demand mode auto-scales to workload
- No performance tuning needed for MVP scale

**OpenAI API:**
- Rate limit: 10,000 requests per minute (Tier 4)
- Batch API: 50,000 requests per batch file
- Implement exponential backoff for rate limit errors

### Cost Estimates (Monthly)

**Assumptions:** 500 students, 20 transcripts/student/month, 5 writing samples/student/month

| Service | Usage | Est. Cost |
|---------|-------|-----------|
| OpenAI API (GPT-4o-mini) | ~10M tokens | $1.50 |
| OpenAI API (GPT-4o) | ~2M tokens | $5.00 |
| Lambda | 50,000 invocations @ 512MB | $1.00 |
| AWS Batch + Fargate | 100 hours @ 2vCPU/4GB | $40.00 |
| S3 Storage | 50GB | $1.15 |
| DynamoDB | 5M reads, 1M writes | $1.50 |
| CloudFront | 10GB transfer | $0.85 |
| **Total** | | **~$51/month** |

**Scaling:** At 5,000 students: ~$450/month

---

## Monitoring & Observability

### CloudWatch Metrics

**Custom Metrics:**
- `VocabularyExtractionLatency`: Time to extract vocabulary per text
- `OpenAICostPerStudent`: Running cost tracker
- `BatchJobSuccessRate`: Percentage of successful jobs
- `RecommendationGenerationErrors`: Failed recommendation attempts
- `StudentProfileUpdateRate`: Updates per minute

**Standard Metrics:**
- Lambda: Invocations, Errors, Duration, Throttles
- API Gateway: Request count, 4xx/5xx errors, Latency
- DynamoDB: ConsumedReadCapacity, ConsumedWriteCapacity
- S3: NumberOfObjects, BucketSizeBytes

### Logging Strategy

**Log Levels:**
- `DEBUG`: Development only (detailed OpenAI requests/responses)
- `INFO`: Normal operations (job started, completed, API calls)
- `WARNING`: Recoverable errors (rate limits, retries)
- `ERROR`: Unrecoverable errors (validation failures, job crashes)
- `CRITICAL`: System-wide issues (AWS service unavailable)

**Log Aggregation:**
- All logs → CloudWatch Logs
- Structured logging (JSON format)
- Correlation IDs for request tracing
- 30-day retention (configurable)

### Alerting

**Critical Alarms:**
- Lambda error rate > 5%
- Batch job failure rate > 10%
- OpenAI API errors > 50/hour
- Daily AWS cost > $20
- DynamoDB throttling events > 0

**Notification Channels:**
- SNS topic → Email/Slack
- PagerDuty integration for production

---

## Deployment Strategy

### Environments

| Environment | Purpose | Infrastructure |
|-------------|---------|----------------|
| **Development** | Local testing | LocalStack (AWS emulation) + mock APIs |
| **Staging** | Pre-production validation | Full AWS stack (lower limits) |
| **Production** | Live system | Full AWS stack (production limits) |

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
on: [push, pull_request]

jobs:
  test:
    - Run pytest with coverage (>60% required)
    - Run black, ruff, mypy
    - Upload coverage reports to CodeCov

# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    - Build Docker images
    - Push to ECR
    - Deploy CloudFormation stacks
    - Run smoke tests
    - Manual approval gate

  deploy-production:
    - Deploy CloudFormation stacks
    - Run integration tests
    - Monitor for errors (1 hour)
    - Rollback on failure
```

### Rollback Strategy

1. **Infrastructure:** CloudFormation stack update rollback
2. **Application Code:**
   - Lambda: Version aliases + weighted routing
   - Batch: Previous Docker image tag
3. **Database:** DynamoDB point-in-time recovery (PITR)
4. **Recovery Time Objective (RTO):** < 15 minutes

---

## Development Workflow

### Local Development Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd vocabulator

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with OpenAI API key, AWS credentials

# 5. Start LocalStack (AWS emulation)
docker-compose up -d localstack

# 6. Initialize local database
python scripts/seed_vocabulary_db.py --local

# 7. Run tests
pytest tests/ -v --cov=src

# 8. Start local API server
uvicorn src.api.main:app --reload --port 8000
```

### Test-First Development Cycle

Following the established test-first workflow:

```
1. Write failing tests (RED)
   └─> Define expected behavior in tests/
   └─> Run: pytest tests/unit/test_new_feature.py
   └─> Verify: All tests fail

2. Implement feature (GREEN)
   └─> Write minimal code to pass tests
   └─> Run: pytest tests/unit/test_new_feature.py
   └─> Verify: All tests pass

3. Refactor (REFACTOR)
   └─> Improve code quality
   └─> Run: pytest tests/ (all tests)
   └─> Verify: All tests still pass

4. Commit (only when green)
   └─> git commit -m "feat: add new feature"
   └─> Pre-commit hook runs tests automatically
```

### Code Review Standards

- All PRs require 1 approval
- Must pass all tests (60%+ coverage)
- Must pass linting (black, ruff, mypy)
- Must include tests for new features
- Must update relevant documentation

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| OpenAI API outage | High | Low | Cache responses, implement retry logic, fallback to basic NLP |
| OpenAI cost overrun | High | Medium | Daily spending alarms, request quotas, cost dashboards |
| AWS service limits | Medium | Low | Request limit increases proactively, implement throttling |
| Poor recommendation quality | High | Medium | Human-in-the-loop validation, teacher feedback mechanism |
| Data loss | High | Very Low | S3 versioning, DynamoDB backups, PITR enabled |

### Operational Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Incorrect student data | Medium | Medium | Input validation, data quality checks, audit logs |
| Privacy breach | Critical | Very Low | Anonymous IDs, encryption, regular security audits |
| Slow adoption | Medium | Medium | Simple UI, clear value proposition, teacher training |

---

## Future Enhancements (Post-MVP)

### Phase 2 Features
1. **Real-time speech-to-text:** Integrate AWS Transcribe for live classroom transcription
2. **Gamified learning:** Interactive vocabulary challenges for students
3. **Teacher dashboard:** React-based admin panel with analytics
4. **Multi-language support:** Spanish/English bilingual vocabulary development
5. **Integration APIs:** Connect with Google Classroom, Canvas, Schoology

### Phase 3 Features
1. **Adaptive learning:** Machine learning models for personalized pacing
2. **Collaborative features:** Peer vocabulary sharing, classroom word walls
3. **Parent portal:** Family engagement with vocabulary practice at home
4. **Advanced analytics:** Predictive models for vocabulary growth trajectories
5. **Mobile app:** Native iOS/Android apps for students

---

## Glossary

| Term | Definition |
|------|------------|
| **Common Core** | Educational standards defining grade-level vocabulary expectations |
| **COPPA** | Children's Online Privacy Protection Act (under-13 privacy law) |
| **FERPA** | Family Educational Rights and Privacy Act (student records law) |
| **GPT-4o** | OpenAI's optimized GPT-4 model (2024 release) |
| **GPT-4o-mini** | Smaller, faster, cheaper variant of GPT-4o |
| **PII** | Personally Identifiable Information |
| **Zone of Proximal Development (ZPD)** | Learning theory concept - optimal challenge level for students |
| **Vocabulary Gap** | Difference between student's current vocabulary and grade-level expectations |

---

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [AWS Batch Best Practices](https://docs.aws.amazon.com/batch/latest/userguide/best-practices.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [COPPA Compliance Guide](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)
- [Common Core State Standards](http://www.corestandards.org/)

---

**Document Status:** Draft for Review
**Next Review Date:** After MVP completion
**Owner:** Technical Lead
**Last Updated:** 2025-11-10
