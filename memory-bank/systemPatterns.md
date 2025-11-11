# System Patterns: vocabulator

**Last Updated**: 2025-11-10

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
├── api/               # FastAPI application
├── vocabulary/        # Vocabulary corpus and utilities
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

### Pattern 4: Conditional Credential Handling
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
   - Generate HTML report (Jinja2)
   - Upload report to S3
5. Job completion callback updates ProcessingJobs table
6. Teacher accesses results via API

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
