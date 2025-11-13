# System Patterns: vocabulator

**Last Updated**: 2025-11-12

## Architecture Overview

### System Design

Vocabulator follows a layered serverless architecture:

```
┌─────────────────────────────────────────────────────────┐
│              Frontend Layer (S3 + CloudFront)          │
│              Static HTML/CSS Reports                    │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────┐
│              API Layer (Lambda + API Gateway)          │
│              FastAPI endpoints                         │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         Processing Layer (AWS Batch + Fargate)         │
│         Parallel text processing                        │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              AI/ML Layer (OpenAI API)                  │
│              GPT-4o-mini + GPT-4o                      │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         Data Layer (DynamoDB + S3)                      │
│         Student profiles, recommendations, corpus      │
└─────────────────────────────────────────────────────────┘
```

### Module Structure
```
src/
├── data/              # Data layer (DynamoDB, S3 clients)
│   ├── dynamodb_client.py
│   ├── s3_client.py
│   ├── models/        # Pydantic data models
│   └── repositories/  # Repository pattern implementations
├── ai/                # AI/ML layer (OpenAI integration)
├── processing/        # Text processing pipeline
│   ├── text_processing_pipeline.py  # End-to-end orchestrator
│   ├── parallel_executor.py         # Async parallel processing
│   └── batch_client.py              # AWS Batch integration
├── api/               # FastAPI application
│   ├── main.py        # Application setup and route registration
│   ├── dependencies.py # Dependency injection functions
│   ├── routes/         # API endpoint routes
│   │   ├── upload.py
│   │   ├── profiles.py
│   │   ├── recommendations.py
│   │   └── batch.py
│   ├── models/         # Request/response models
│   │   ├── requests.py
│   │   └── responses.py
│   └── utils/         # API utilities
│       ├── errors.py   # Standardized error responses
│       ├── s3_paths.py # Safe S3 path construction
│       └── validation.py # Shared validation utilities
├── vocabulary/        # Vocabulary corpus and utilities
├── frontend/          # Frontend layer (HTML report generation)
│   ├── templates.py   # Jinja2 template rendering functions
│   ├── report_generator.py  # Report generation and S3 upload service
│   └── templates/     # Jinja2 HTML templates
│       ├── base.html
│       ├── profile_report.html
│       └── recommendations_report.html
└── utils/             # Shared utilities (config, logger)
```

---

## Design Patterns

### Pattern 1: Repository Pattern
**When to use**: Data access layer abstraction
**Implementation**: BaseRepository with generic type support
**Example**:
```python
class BaseRepository(Generic[T]):
    def __init__(self, table_name: str):
        self.client = DynamoDBClient(table_name=table_name)
    
    def get(self, partition_value: Any, sort_value: Optional[Any] = None) -> Optional[T]:
        # Implementation
        pass

class StudentRepository(BaseRepository[StudentProfile]):
    def _item_to_model(self, item: Dict) -> StudentProfile:
        return StudentProfile.from_dict(item)
```

**Benefits**:
- Clean separation of data access logic
- Easy to mock for testing
- Consistent CRUD operations across repositories

### Pattern 2: Pydantic Models for Data Validation
**When to use**: All data structures (models, config, API requests/responses)
**Implementation**: Pydantic BaseModel with Field validators
**Example**:
```python
class StudentProfile(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=255)
    grade_level: int = Field(..., ge=6, le=8)
    vocabulary_list: List[VocabularyEntry] = Field(default_factory=list)
    
    @validator('vocabulary_list', pre=True, always=True)
    def sort_vocabulary_list(cls, v):
        if isinstance(v, list):
            return sorted(v, key=lambda x: x.word)
        return v
```

**Benefits**:
- Automatic validation
- Type safety
- Clear error messages
- Serialization/deserialization

### Pattern 3: Retry Logic with Exponential Backoff
**When to use**: All AWS service calls (DynamoDB, S3, OpenAI)
**Implementation**: Decorator/wrapper with jitter
**Example**:
```python
def _retry_with_backoff(self, operation, *args, **kwargs):
    max_retries = 3
    base_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            return operation(*args, **kwargs)
        except ClientError as e:
            if e.response['Error']['Code'] in RETRYABLE_ERRORS:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.random()
                    time.sleep(delay)
                    continue
            raise DynamoDBError(...) from e
```

**Benefits**:
- Handles transient failures
- Prevents thundering herd (jitter)
- Configurable retry attempts

### Pattern 4: Processing Pipeline Orchestration
**When to use**: End-to-end workflows requiring multiple steps
**Implementation**: Pipeline class coordinating multiple components
**Example**:
```python
class TextProcessingPipeline:
    def __init__(self, extractor, gap_identifier, recommender, ...):
        self.extractor = extractor
        self.gap_identifier = gap_identifier
        self.recommender = recommender
        # ...
    
    async def process_text(self, student_id: str, text: str, ...):
        # Step 1: Extract vocabulary
        words = await self._extract_vocabulary(text)
        # Step 2: Update profile
        profile = await self._update_profile_with_words(student_id, words)
        # Step 3: Identify gaps
        gaps = await self._identify_gaps(profile)
        # Step 4: Generate recommendations
        recommendations = await self._generate_recommendations(gaps)
        # Step 5: Persist
        await self._persist_recommendations(recommendations)
        return recommendations
```

**Benefits**:
- Clear separation of concerns
- Easy to test individual steps
- Error handling at each stage
- Can be extended with additional steps

### Pattern 5: Parallel Execution with Concurrency Control
**When to use**: Processing multiple items concurrently with resource limits
**Implementation**: Async executor with semaphore
**Example**:
```python
class ParallelExecutor:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute(self, tasks: List[ProcessingTask]):
        async def run_task(task: ProcessingTask):
            async with self.semaphore:
                try:
                    result = await task.callable(*task.args, **task.kwargs)
                    return ProcessingResult(task_id=task.task_id, success=True, result=result)
                except Exception as e:
                    return ProcessingResult(task_id=task.task_id, success=False, error=str(e))
        
        results = await asyncio.gather(*[run_task(task) for task in tasks])
        return results
```

**Benefits**:
- Controlled concurrency (prevents resource exhaustion)
- Graceful error handling (one failure doesn't stop others)
- Progress tracking support
- Request ID propagation for correlation

### Pattern 6: FastAPI Dependency Injection
**When to use**: Shared resources and logic across endpoints
**Implementation**: FastAPI Depends with generator functions
**Example**:
```python
from fastapi import Depends
from typing import Annotated

def get_student_repository() -> Generator[StudentRepository, None, None]:
    """Dependency injection for StudentRepository."""
    repo = StudentRepository(table_name=get_config().get_dynamodb_table_name("StudentProfiles"))
    try:
        yield repo
    finally:
        logger.debug("Cleaning up StudentRepository")

@router.get("/students/{student_id}/profile")
async def get_profile(
    student_id: str,
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
):
    # Use student_repo
    pass
```

**Benefits**:
- Clean separation of concerns
- Easy to mock for testing (app.dependency_overrides)
- Automatic resource cleanup
- Type-safe dependency injection

### Pattern 7: Standardized Error Responses
**When to use**: Consistent error handling across all API endpoints
**Implementation**: Helper functions creating structured error responses
**Example**:
```python
from src.api.utils.errors import (
    create_not_found_error_response,
    create_validation_error_response,
    create_internal_error_response,
)

# In endpoint
if not profile:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=create_not_found_error_response(
            resource_type="student",
            resource_id=student_id,
            request_id=request_id,
        ),
    )
```

**Benefits**:
- Consistent error format across API
- Request ID correlation for debugging
- Clear error messages for clients
- Easy to extend with new error types

### Pattern 8: Template-Based Report Generation
**When to use**: Generating HTML reports from structured data
**Implementation**: Jinja2 templates with autoescape enabled
**Example**:
```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

def render_profile_report(profile: StudentProfile) -> str:
    template = env.get_template("profile_report.html")
    context = {
        "student_id": profile.student_id,
        "grade_level": profile.grade_level,
        "vocabulary_list": [...],
    }
    return template.render(**context)
```

**Benefits**:
- XSS protection via autoescape
- Separation of presentation from logic
- Reusable template structure (base template)
- Responsive design support (CSS in templates)

### Pattern 9: Report Generation Service Pattern
**When to use**: Generating and uploading static reports to S3
**Implementation**: Service class with S3 integration
**Example**:
```python
class ReportGenerator:
    def __init__(self, s3_client: Optional[S3Client] = None):
        self.s3_client = s3_client or S3Client()
    
    def generate_profile_report(self, profile: StudentProfile, ...) -> str:
        # Generate HTML
        html_content = render_profile_report(profile)
        html_bytes = html_content.encode("utf-8")
        
        # Upload to S3
        s3_key = f"reports/{profile.student_id}/profile_{timestamp}.html"
        self.s3_client.upload(key=s3_key, content=html_bytes, content_type="text/html")
        
        # Generate presigned URL
        return self.s3_client.generate_presigned_url(key=s3_key, expiration_hours=168)
```

**Benefits**:
- Centralized report generation logic
- S3 integration with presigned URLs
- Error handling with custom exceptions
- Testable with mock S3 clients

### Pattern 10: Conditional Credential Handling
**When to use**: Local development vs production
**Implementation**: Check for endpoint_url (LocalStack)
**Example**:
```python
if endpoint_url:
    # LocalStack requires explicit credentials
    self.dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
    )
else:
    # Production: Use IAM roles (no explicit credentials)
    self.dynamodb = boto3.resource("dynamodb")
```

**Benefits**:
- Security: No hardcoded credentials in production
- Flexibility: Works with LocalStack for testing
- Follows AWS best practices

---

## Key Invariants

### Invariant 1: Anonymous Student IDs Only
- No PII (Personally Identifiable Information) is collected
- Student IDs are anonymous identifiers (e.g., "STU-001")
- COPPA-compliant design (no collection of student names, emails, etc.)

### Invariant 2: Test-First Development
- All features implemented using TDD (Test-Driven Development)
- Tests written before implementation
- Target: 60-80% code coverage

### Invariant 3: Serverless-First Architecture
- Prefer AWS managed services (Lambda, DynamoDB, S3)
- Minimize infrastructure management overhead
- Pay-per-use cost model

---

## Data Flow

### Request/Response Cycle

**Single Writing Sample Upload:**
1. Teacher uploads writing sample via API
2. Lambda handler validates request (Pydantic)
3. Store raw text in S3 (`writing-samples/raw/{student_id}/{assignment_id}.txt`)
4. Extract vocabulary using GPT-4o-mini
5. Update student profile in DynamoDB (add words, recalculate proficiency)
6. Return response with words added

**Batch Processing:**
1. Teacher uploads CSV with transcripts
2. Lambda submits AWS Batch job
3. Batch provisions Fargate containers (parallel processing)
4. Each container processes multiple students:
   - Fetch transcript from S3
   - Extract vocabulary (GPT-4o-mini)
   - Update profile (DynamoDB)
   - Identify gaps vs Common Core (GPT-4o)
   - Generate recommendations (GPT-4o)
   - Store recommendations (DynamoDB)
   - Generate HTML report (Jinja2 templates)
   - Upload report to S3 (via ReportGenerator)
   - Generate presigned URL for report access
5. Job completion callback updates ProcessingJobs table
6. Teacher accesses results via API or S3 presigned URLs

### State Management

**Student Profile State:**
- Stored in DynamoDB (StudentProfiles table)
- Partition key: student_id, Sort key: profile_version
- Vocabulary list maintained as list of VocabularyEntry objects
- Proficiency score recalculated on each update

**Recommendation State:**
- Stored in DynamoDB (VocabularyRecommendations table)
- Partition key: student_id, Sort key: recommendation_date
- Status: pending → assigned → learned
- TTL: 30 days (automatic expiration)

---

## Integration Points

### OpenAI API
- **Purpose**: Vocabulary extraction, gap analysis, recommendation generation
- **How we use it**: 
  - GPT-4o-mini for vocabulary extraction (cost-effective, ~$0.15 per 1M tokens)
  - GPT-4o for gap analysis and recommendations (higher quality, ~$2.50 per 1M tokens)
- **Failure handling**: Retry logic with exponential backoff, rate limit handling with retry-after headers
- **Cost tracking**: CostTracker with Decimal precision, OperationType enum (EXTRACTION, ANALYSIS, RECOMMENDATION)
- **Model validation**: Configurable strict mode (default: warn but proceed for unknown models)

### AWS DynamoDB
- **Purpose**: Structured data storage (profiles, recommendations, vocabulary corpus)
- **How we use it**: 
  - Repository pattern for data access
  - Batch operations for efficiency
  - GSI for queries (grade level, status)
- **Failure handling**: Retry logic, error wrapping (DynamoDBError)

### AWS S3
- **Purpose**: File storage (transcripts, writing samples, reports)
- **How we use it**: 
  - Multipart upload for large files
  - Presigned URLs for secure temporary access
  - Organized bucket structure (transcripts/, writing-samples/, reports/)
- **Failure handling**: Retry logic, error wrapping (S3Error)

### AWS Batch
- **Purpose**: Scalable batch processing for multiple students
- **How we use it**: 
  - BatchClient wrapper for job submission and status tracking
  - Job configuration with environment variables (student_ids, s3_paths, grade_level)
  - Fargate containers process students in parallel using ParallelExecutor
  - Batch job handler script orchestrates TextProcessingPipeline for each student
  - Resource requirement validation (Fargate limits: memory 512-30720 MB, vCPUs 0.25-4)
- **Failure handling**: 
  - Retry logic for job submission
  - Individual student failures don't stop batch (graceful degradation)
  - Job status tracking with BatchJobInfo dataclass
  - Job cancellation support

---

## Performance Considerations

### Optimization Strategy
- **Batch Operations**: Use DynamoDB batch_get_items/batch_write_items (up to 25 items)
- **Parallel Processing**: AWS Batch with multiple Fargate containers
- **Caching**: Common Core vocabulary lookups (future enhancement)
- **Pagination**: All query/scan operations support pagination

### Caching Strategy
- **Future Enhancement**: Cache Common Core vocabulary lookups
- **Current**: No caching (acceptable for MVP scale)

### Scaling Approach
- **DynamoDB**: PAY_PER_REQUEST billing (auto-scaling)
- **Lambda**: Auto-scaling based on request volume
- **AWS Batch**: Parallel processing with configurable container count
- **S3**: Unlimited storage, no scaling concerns
