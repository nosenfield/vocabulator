# FastAPI Best Practices

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [Testing Standards](testing-standards.md), [Error Handling](error-handling.md)

---

## Application Structure

**Organize by feature, not by type:**

```python
# Good - Feature-based organization
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

# Bad - Type-based organization (hard to scale)
src/api/
├── routes.py            # All routes in one file
├── models.py            # All models in one file
└── utils.py             # Grab bag of functions
```

---

## Dependency Injection

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

## Request/Response Models

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
- Use `Field()` for validation constraints and documentation
- Add `description` and `examples` for OpenAPI docs
- Use custom validators for complex logic
- Define `Config.json_schema_extra` for clear examples
- Don't put business logic in models (keep them data-only)

---

## Error Handling

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

## Testing FastAPI Applications

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

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for async patterns
- **Error Handling**: See [error-handling.md](error-handling.md) for custom exceptions
- **Testing Standards**: See [testing-standards.md](testing-standards.md) for test organization
- **Documentation Standards**: See [documentation.md](documentation.md) for API docs
- **Code Organization**: See [code-organization.md](code-organization.md) for dependency injection

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [Testing Standards](testing-standards.md)
- [Error Handling](error-handling.md)
