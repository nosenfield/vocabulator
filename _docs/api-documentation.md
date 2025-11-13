# Vocabulator API Documentation

**Version:** 1.0.0  
**Base URL:** `https://api.vocabulator.example.com/api/v1`  
**OpenAPI Schema:** `/api/v1/openapi.json`  
**Interactive Docs:** `/api/v1/docs` (Swagger UI) or `/api/v1/redoc` (ReDoc)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Request/Response Format](#requestresponse-format)
5. [Error Handling](#error-handling)
6. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Upload Endpoints](#upload-endpoints)
   - [Student Profile Endpoints](#student-profile-endpoints)
   - [Recommendation Endpoints](#recommendation-endpoints)
   - [Batch Processing Endpoints](#batch-processing-endpoints)
7. [Data Models](#data-models)
8. [Examples](#examples)

---

## Overview

The Vocabulator API provides a RESTful interface for managing student vocabulary profiles, uploading transcripts and writing samples, and retrieving personalized vocabulary recommendations.

### Key Features

- **Anonymous Student IDs**: COPPA-compliant system using anonymous identifiers (format: `STU-XXX`)
- **Vocabulary Extraction**: AI-powered extraction from transcripts and writing samples
- **Personalized Recommendations**: Grade-level appropriate vocabulary recommendations
- **Batch Processing**: Process multiple students in parallel via AWS Batch

### API Versioning

The API uses URL-based versioning. All endpoints are prefixed with `/api/v1`. Future versions will use `/api/v2`, etc.

---

## Authentication

**Current Status:** Authentication is not implemented in MVP. API endpoints are publicly accessible.

**Future Implementation:** 
- API key authentication via header: `X-API-Key: <key>`
- IAM role-based authentication for AWS deployments
- OAuth 2.0 for teacher dashboard integration

---

## Rate Limiting

**Current Status:** Rate limiting is not implemented in MVP.

**Future Implementation:**
- 100 requests per minute per IP address
- 1000 requests per hour per API key
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- HTTP 429 (Too Many Requests) when limit exceeded

---

## Request/Response Format

### Request Format

- **Content-Type:** `application/json`
- **Accept:** `application/json`
- **Request ID:** Optional `X-Request-ID` header for correlation

### Response Format

All responses are JSON objects. Successful responses include:
- Status code: 200 (OK), 201 (Created), etc.
- Response body matching the endpoint's response model

Error responses include:
- Status code: 400 (Bad Request), 404 (Not Found), 500 (Internal Server Error), etc.
- Error details in standardized format (see [Error Handling](#error-handling))

### Student ID Format

All student IDs must follow the format: `STU-XXX` where `XXX` is a 3-digit number (e.g., `STU-001`, `STU-123`).

---

## Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "field_name",
    "request_id": "uuid",
    "student_id": "STU-001"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 500 | Internal Server Error | Server error occurred |

### Common Error Codes

- `validation_error`: Invalid request parameters or format
- `not_found`: Requested resource does not exist
- `conflict`: Resource already exists (e.g., duplicate student ID)
- `processing_error`: Error during text processing
- `s3_upload_failed`: Failed to store file in S3
- `internal_error`: Unexpected server error

---

## Endpoints

### Health Check

#### `GET /health`

Check API health status.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T10:00:00Z",
  "service": "vocabulator-api",
  "version": "1.0.0"
}
```

---

### Upload Endpoints

#### `POST /transcripts/upload`

Upload a student transcript for vocabulary extraction.

**Request Body:**

```json
{
  "student_id": "STU-001",
  "text": "Today we learned about photosynthesis and how plants convert sunlight into energy.",
  "session_date": "2025-11-10",
  "grade_level": 7
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "student_id": "STU-001",
  "words_extracted": 15,
  "profile_url": "/api/v1/students/STU-001/profile"
}
```

**Process Flow:**
1. Validates student profile exists (404 if not found)
2. Stores raw transcript in S3
3. Processes transcript through vocabulary extraction pipeline
4. Updates student profile with extracted vocabulary
5. Generates vocabulary recommendations

**Validation Rules:**
- `student_id`: Must match pattern `STU-\d{3}`
- `text`: 10-50,000 characters, must contain alphabetic characters
- `session_date`: Valid ISO 8601 date (YYYY-MM-DD)
- `grade_level`: Integer between 6-8

**Errors:**
- `400`: Invalid request parameters
- `404`: Student profile not found
- `500`: Processing or storage error

---

#### `POST /writing/upload`

Upload a student writing sample for vocabulary extraction.

**Request Body:**

```json
{
  "student_id": "STU-001",
  "text": "In my essay, I will discuss the importance of vocabulary in academic success.",
  "assignment_id": "ASSIGN-001",
  "grade_level": 7
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "student_id": "STU-001",
  "words_extracted": 12,
  "assignment_id": "ASSIGN-001"
}
```

**Validation Rules:**
- Same as transcript upload
- `assignment_id`: Optional string identifier

**Errors:**
- Same as transcript upload

---

### Student Profile Endpoints

#### `GET /students/{student_id}/profile`

Retrieve a student's vocabulary profile.

**Path Parameters:**
- `student_id`: Student identifier (format: `STU-XXX`)

**Response:** `200 OK`

```json
{
  "student_id": "STU-001",
  "grade_level": 7,
  "vocabulary_size": 150,
  "proficiency_score": 75.5,
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T15:30:00Z"
}
```

**Errors:**
- `400`: Invalid student ID format
- `404`: Student profile not found

---

#### `GET /students`

List students, optionally filtered by grade level.

**Query Parameters:**
- `grade_level` (optional): Filter by grade level (6-8)

**Example:** `GET /students?grade_level=7`

**Response:** `200 OK`

```json
{
  "students": [
    {
      "student_id": "STU-001",
      "grade_level": 7,
      "vocabulary_size": 150,
      "proficiency_score": 75.5
    }
  ],
  "total": 1
}
```

**Note:** Currently requires `grade_level` filter. Without filter, returns empty list.

---

#### `POST /students`

Create a new student profile.

**Request Body:**

```json
{
  "student_id": "STU-001",
  "grade_level": 7
}
```

**Response:** `201 Created`

```json
{
  "student_id": "STU-001",
  "grade_level": 7,
  "vocabulary_size": 0,
  "proficiency_score": 0.0,
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T10:00:00Z"
}
```

**Errors:**
- `400`: Invalid student ID format or grade level
- `409`: Student profile already exists

---

#### `PUT /students/{student_id}`

Update an existing student profile (partial updates supported).

**Path Parameters:**
- `student_id`: Student identifier (format: `STU-XXX`)

**Request Body:**

```json
{
  "grade_level": 8
}
```

**Response:** `200 OK`

```json
{
  "student_id": "STU-001",
  "grade_level": 8,
  "vocabulary_size": 150,
  "proficiency_score": 75.5,
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T16:00:00Z"
}
```

**Note:** Only provided fields are updated. Omitted fields remain unchanged.

**Errors:**
- `400`: Invalid student ID format or grade level
- `404`: Student profile not found

---

### Recommendation Endpoints

#### `GET /students/{student_id}/recommendations`

Retrieve all vocabulary recommendations for a student, ordered by date (newest first).

**Path Parameters:**
- `student_id`: Student identifier (format: `STU-XXX`)

**Response:** `200 OK`

```json
{
  "recommendations": [
    {
      "student_id": "STU-001",
      "recommendation_date": "2025-11-10",
      "words": [
        {
          "word": "photosynthesis",
          "definition": "The process by which plants convert light into energy",
          "grade_level": 7,
          "difficulty_score": 0.6,
          "rationale": "Important for science curriculum",
          "example_sentences": [
            "Plants use photosynthesis to make food.",
            "Without photosynthesis, plants cannot grow."
          ]
        }
      ],
      "status": "pending"
    }
  ],
  "total": 1
}
```

**Errors:**
- `400`: Invalid student ID format
- `404`: Student profile not found

---

#### `PATCH /recommendations/{recommendation_id}/status`

Update the status of a vocabulary recommendation.

**Path Parameters:**
- `recommendation_id`: Composite identifier (format: `STU-XXX:YYYY-MM-DD`)

**Request Body:**

```json
{
  "status": "assigned"
}
```

**Valid Status Values:**
- `pending`: Recommendation generated but not yet assigned
- `assigned`: Recommendation assigned to student
- `learned`: Student has learned the vocabulary

**Response:** `200 OK`

```json
{
  "success": true,
  "recommendation_id": "STU-001:2025-11-10",
  "status": "assigned"
}
```

**Errors:**
- `400`: Invalid recommendation ID format or status value
- `404`: Recommendation not found

---

### Batch Processing Endpoints

#### `POST /batch/process`

Submit a batch processing job to process multiple student transcripts in parallel.

**Request Body:**

```json
{
  "student_ids": ["STU-001", "STU-002"],
  "s3_paths": [
    "s3://bucket/transcripts/STU-001.txt",
    "s3://bucket/transcripts/STU-002.txt"
  ],
  "grade_level": 7
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "job_id": "job-abc123",
  "message": "Batch job submitted successfully for 2 students"
}
```

**Validation Rules:**
- `student_ids`: List of 1+ student IDs (format: `STU-XXX`)
- `s3_paths`: List of S3 paths (must match `student_ids` length)
- `grade_level`: Integer between 6-8

**Process:**
- Submits job to AWS Batch for parallel processing
- Returns job ID for status tracking
- Processing happens asynchronously

**Errors:**
- `400`: Invalid request parameters (e.g., mismatched array lengths, invalid student IDs)
- `500`: Job submission failed

---

#### `GET /batch/{job_id}/status`

Retrieve the current status of a batch processing job.

**Path Parameters:**
- `job_id`: AWS Batch job ID

**Response:** `200 OK`

```json
{
  "job_id": "job-abc123",
  "status": "RUNNING",
  "created_at": "2025-11-10T10:00:00Z",
  "started_at": "2025-11-10T10:01:00Z",
  "stopped_at": null,
  "progress": 50,
  "error_message": null
}
```

**Status Values:**
- `SUBMITTED`: Job submitted, waiting to start
- `PENDING`: Job queued, waiting for resources
- `RUNNABLE`: Job ready to run
- `RUNNING`: Job currently executing
- `SUCCEEDED`: Job completed successfully
- `FAILED`: Job failed

**Progress Calculation:**
- `SUCCEEDED`: 100%
- `FAILED`: 0%
- `RUNNING`: Estimated based on elapsed time (0-95%)

**Errors:**
- `404`: Job not found

---

## Data Models

### Student Profile

```typescript
{
  student_id: string;        // Format: STU-XXX
  grade_level: number;       // 6-8
  vocabulary_size: number;   // Count of unique words
  proficiency_score: number; // 0.0-100.0
  created_at: datetime;
  last_updated: datetime;
}
```

### Vocabulary Recommendation

```typescript
{
  student_id: string;
  recommendation_date: string;  // ISO 8601 date (YYYY-MM-DD)
  words: RecommendationWord[];
  status: "pending" | "assigned" | "learned";
}
```

### Recommendation Word

```typescript
{
  word: string;
  definition: string;
  grade_level: number;        // 6-8
  difficulty_score: number;   // 0.0-1.0 (0=easy, 1=hard)
  rationale: string;
  example_sentences: string[];
}
```

### Batch Job Status

```typescript
{
  job_id: string;
  status: "SUBMITTED" | "PENDING" | "RUNNABLE" | "RUNNING" | "SUCCEEDED" | "FAILED";
  created_at: datetime | null;
  started_at: datetime | null;
  stopped_at: datetime | null;
  progress: number | null;      // 0-100
  error_message: string | null;
}
```

---

## Examples

### Complete Workflow: Create Student → Upload Transcript → Get Recommendations

#### Step 1: Create Student Profile

```bash
curl -X POST https://api.vocabulator.example.com/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-001",
    "grade_level": 7
  }'
```

#### Step 2: Upload Transcript

```bash
curl -X POST https://api.vocabulator.example.com/api/v1/transcripts/upload \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-001",
    "text": "Today we learned about photosynthesis and how plants convert sunlight into energy.",
    "session_date": "2025-11-10",
    "grade_level": 7
  }'
```

#### Step 3: Get Recommendations

```bash
curl https://api.vocabulator.example.com/api/v1/students/STU-001/recommendations
```

#### Step 4: Update Recommendation Status

```bash
curl -X PATCH https://api.vocabulator.example.com/api/v1/recommendations/STU-001:2025-11-10/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "assigned"
  }'
```

### Batch Processing Workflow

#### Step 1: Submit Batch Job

```bash
curl -X POST https://api.vocabulator.example.com/api/v1/batch/process \
  -H "Content-Type: application/json" \
  -d '{
    "student_ids": ["STU-001", "STU-002", "STU-003"],
    "s3_paths": [
      "s3://bucket/transcripts/STU-001.txt",
      "s3://bucket/transcripts/STU-002.txt",
      "s3://bucket/transcripts/STU-003.txt"
    ],
    "grade_level": 7
  }'
```

**Response:**
```json
{
  "success": true,
  "job_id": "job-abc123",
  "message": "Batch job submitted successfully for 3 students"
}
```

#### Step 2: Check Job Status

```bash
curl https://api.vocabulator.example.com/api/v1/batch/job-abc123/status
```

**Response (while running):**
```json
{
  "job_id": "job-abc123",
  "status": "RUNNING",
  "created_at": "2025-11-10T10:00:00Z",
  "started_at": "2025-11-10T10:01:00Z",
  "progress": 50
}
```

**Response (completed):**
```json
{
  "job_id": "job-abc123",
  "status": "SUCCEEDED",
  "created_at": "2025-11-10T10:00:00Z",
  "started_at": "2025-11-10T10:01:00Z",
  "stopped_at": "2025-11-10T10:15:00Z",
  "progress": 100
}
```

---

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `/api/v1/docs` - Interactive API explorer with "Try it out" functionality
- **ReDoc:** `/api/v1/redoc` - Beautiful, responsive API documentation
- **OpenAPI Schema:** `/api/v1/openapi.json` - Machine-readable API specification

These interactive docs allow you to:
- Explore all endpoints
- View request/response schemas
- Test endpoints directly from the browser
- Download OpenAPI specification

---

## Support

For API support, issues, or feature requests:
- **Documentation:** See `_docs/` directory
- **Architecture:** See `_docs/architecture.md`
- **Best Practices:** See `_docs/best-practices.md`

---

**Last Updated:** 2025-11-12  
**API Version:** 1.0.0

