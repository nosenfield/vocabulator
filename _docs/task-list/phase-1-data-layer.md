# Phase 1: Data Layer & Storage

**Total Estimated Time:** 22-29 hours (4-5 days)
**Priority:** 🔴 P0 (All tasks)
**Dependencies:** Phase 0 (tasks 0.3, 0.4)

---

## Overview

Phase 1 implements the data persistence layer, including DynamoDB and S3 clients, data models, and the Common Core vocabulary database. This layer provides the foundation for all data operations in the application.

**Key Deliverables:**
- DynamoDB client with base repository pattern
- Student profile and recommendation data models
- S3 client for file operations
- Common Core vocabulary database (grades 6-8)

**Cross-References:**
- Uses configuration from [Phase 0](phase-0-project-setup.md) (task 0.3)
- Uses logging from [Phase 0](phase-0-project-setup.md) (task 0.4)
- Required for [Phase 2: AI/ML Layer](phase-2-ai-ml-layer.md)

---

## 1.1 DynamoDB Client & Base Repository

**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** Phase 0 (0.4)

### Tasks
- [ ] 🧪 Write tests for `src/data/dynamodb_client.py`
- [ ] Implement DynamoDB connection wrapper
- [ ] Add connection pooling and retry logic
- [ ] Create base repository class with CRUD operations
- [ ] Add batch read/write support
- [ ] Implement local DynamoDB setup for testing
- [ ] Add error handling for throttling, not found, etc.

### Acceptance Criteria
- Tests use local DynamoDB (LocalStack or DynamoDB Local)
- CRUD operations work for generic items
- Batch operations handle large datasets
- Throttling errors trigger exponential backoff

### Files Created
- `src/data/dynamodb_client.py`
- `src/data/repositories/base_repository.py`
- `tests/unit/test_dynamodb_client.py`
- `tests/fixtures/dynamodb_setup.py`

### Related Documentation
- See [best-practices.md](../best-practices.md) - DynamoDB Patterns section
- See [architecture.md](../architecture.md) - DynamoDB Tables section

---

## 1.2 Student Profile Data Model & Repository

**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 1.1

### Tasks
- [ ] 🧪 Write tests for StudentProfile model
- [ ] Create StudentProfile Pydantic model
- [ ] Implement validation rules (grade level 6-8, etc.)
- [ ] Create StudentRepository with DynamoDB operations
- [ ] Add methods: create, get, update, delete, list by grade
- [ ] Implement vocabulary list management (add words, update counts)
- [ ] Add proficiency score calculation logic
- [ ] Create DynamoDB table schema (CloudFormation)

### Acceptance Criteria
- StudentProfile model validates correctly
- Repository saves/retrieves profiles from DynamoDB
- Vocabulary list operations work (add, update, dedupe)
- Proficiency score recalculates on profile update
- Table creation script runs successfully

### Files Created
- `src/data/models/student_profile.py`
- `src/data/repositories/student_repository.py`
- `tests/unit/test_student_profile.py`
- `tests/unit/test_student_repository.py`
- `infrastructure/cloudformation/dynamodb-tables.yaml`

### DynamoDB Table Schema
```yaml
StudentProfiles:
  PartitionKey: student_id (String)
  SortKey: profile_version (Number)
  Attributes: vocabulary_list, grade_level, proficiency_score, etc.
  GSI: grade_level-proficiency_score-index
```

### Related Documentation
- See [architecture.md](../architecture.md) - Data Layer section
- See [best-practices.md](../best-practices.md) - Pydantic V2 section
- Required for [Phase 4: API Layer](phase-4-api-layer.md) (task 4.4)

---

## 1.3 Vocabulary Recommendation Data Model & Repository

**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** 1.1

### Tasks
- [ ] 🧪 Write tests for VocabularyRecommendation model
- [ ] Create VocabularyRecommendation Pydantic model
- [ ] Implement RecommendationRepository
- [ ] Add methods: create, get by student, get by date range
- [ ] Implement TTL (30-day expiration) on recommendations
- [ ] Add status tracking (pending, assigned, learned)
- [ ] Create DynamoDB table schema

### Acceptance Criteria
- Recommendation model validates word lists correctly
- Repository handles CRUD operations
- TTL automatically expires old recommendations
- Status updates work correctly

### Files Created
- `src/data/models/recommendation.py`
- `src/data/repositories/recommendation_repository.py`
- `tests/unit/test_recommendation.py`
- `tests/unit/test_recommendation_repository.py`
- `infrastructure/cloudformation/dynamodb-tables.yaml` (updated)

### Related Documentation
- See [architecture.md](../architecture.md) - Data Layer section
- Required for [Phase 2: AI/ML Layer](phase-2-ai-ml-layer.md) (task 2.4)
- Required for [Phase 4: API Layer](phase-4-api-layer.md) (task 4.5)

---

## 1.4 S3 Client & File Operations

**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** Phase 0 (0.4)

### Tasks
- [ ] 🧪 Write tests for `src/data/s3_client.py`
- [ ] Implement S3 client wrapper with boto3
- [ ] Add methods: upload, download, list, delete
- [ ] Implement multipart upload for large files
- [ ] Add presigned URL generation for secure downloads
- [ ] Create S3 bucket structure management
- [ ] Add error handling for access denied, not found, etc.
- [ ] Use LocalStack S3 for testing

### Acceptance Criteria
- Tests use LocalStack S3
- Upload/download operations work for text files
- Presigned URLs generate correctly
- File organization follows architecture.md structure

### Files Created
- `src/data/s3_client.py`
- `tests/unit/test_s3_client.py`
- `tests/fixtures/sample_transcripts/` (mock data)

### S3 Bucket Structure
```
vocabulator-data-{env}/
├── transcripts/
│   ├── raw/{student_id}/{date}-{session_id}.txt
│   └── processed/{student_id}/{date}-{session_id}.json
├── writing-samples/
│   ├── raw/{student_id}/{assignment_id}.txt
│   └── processed/{student_id}/{assignment_id}.json
└── reports/
    └── {student_id}/profile.html
```

### Related Documentation
- See [best-practices.md](../best-practices.md) - S3 Operations section
- See [architecture.md](../architecture.md) - S3 Structure section
- Required for [Phase 4: API Layer](phase-4-api-layer.md) (task 4.3)

---

## 1.5 Common Core Vocabulary Database

**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 1.1

### Tasks
- [ ] Research and source Common Core vocabulary lists (grades 6-8)
- [ ] Create vocabulary corpus JSON files
- [ ] 🧪 Write tests for vocabulary loader
- [ ] Implement `src/vocabulary/common_core_loader.py`
- [ ] Create grade-level mapping utilities
- [ ] Load vocabulary into DynamoDB (seed script)
- [ ] Add word family and synonym grouping
- [ ] Implement fast vocabulary lookup methods

### Acceptance Criteria
- At least 500 words per grade level (6, 7, 8)
- Vocabulary loads into DynamoDB successfully
- Lookup by word or grade level works
- Words include definitions and subject areas

### Files Created
- `src/vocabulary/corpus/common_core_grade_6.json`
- `src/vocabulary/corpus/common_core_grade_7.json`
- `src/vocabulary/corpus/common_core_grade_8.json`
- `src/vocabulary/common_core_loader.py`
- `src/vocabulary/grade_level_mapper.py`
- `tests/unit/test_common_core_loader.py`
- `scripts/seed_vocabulary_db.py`

### Sample Corpus Entry
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

### DynamoDB Table Schema
```yaml
CommonCoreVocabulary:
  PartitionKey: grade_level (Number)
  SortKey: word (String)
  Attributes: definition, subject_areas, complexity_tier, word_family
```

### Vocabulary Sourcing Resources
- Common Core State Standards website
- Academic Word List (AWL)
- COCA (Corpus of Contemporary American English)
- Can start with simplified corpus and enhance iteratively

### Related Documentation
- See [required-reading.md](../required-reading.md) - Vocabulary Development section
- Required for [Phase 2: AI/ML Layer](phase-2-ai-ml-layer.md) (task 2.3)

---

## Phase 1 Completion Checklist

Before proceeding to Phase 2, verify:

- [ ] All Phase 1 tasks completed (1.1-1.5)
- [ ] All unit tests passing for data layer
- [ ] DynamoDB tables created (locally via LocalStack)
- [ ] S3 buckets created and accessible
- [ ] Common Core vocabulary seeded (at least 1500 total words)
- [ ] Code formatted and linted (black, ruff, mypy pass)
- [ ] Integration smoke test: Create student, add vocabulary, retrieve profile
- [ ] Memory Bank updated with Phase 1 completion

### Data Layer Integration Test

Create end-to-end test verifying:
```python
# Create student profile
student = StudentProfile(student_id="STU-001", grade_level=7)
repo.create(student)

# Add vocabulary to profile
repo.add_vocabulary(student_id="STU-001", words=["analyze", "evaluate"])

# Retrieve and verify
profile = repo.get("STU-001")
assert len(profile.vocabulary_list) == 2

# Query Common Core vocabulary
cc_words = vocab_loader.get_by_grade(7)
assert len(cc_words) >= 500
```

### Next Phase
**Proceed to:** [Phase 2: AI/ML Layer](phase-2-ai-ml-layer.md)

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Phase 0: Project Setup](phase-0-project-setup.md) (prerequisite)
- [Phase 2: AI/ML Layer](phase-2-ai-ml-layer.md) (next phase)
- [Phase 4: API Layer](phase-4-api-layer.md) (consumer)
- [architecture.md](../architecture.md)
- [best-practices.md](../best-practices.md)
