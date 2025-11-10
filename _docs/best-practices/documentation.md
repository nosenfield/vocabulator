# Documentation Standards

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [FastAPI Patterns](fastapi-patterns.md)

---

## Docstring Format

**Use Google-style docstrings:**

```python
def generate_recommendations(
    student_id: str,
    grade_level: int,
    num_words: int = 10
) -> List[dict]:
    """Generate vocabulary recommendations for student.

    Analyzes student's current vocabulary profile and identifies
    appropriate challenge words from Common Core standards.

    Args:
        student_id: Anonymous student identifier (format: STU-###)
        grade_level: Student's current grade level (6-8)
        num_words: Number of words to recommend (default: 10)

    Returns:
        List of recommendation dictionaries containing:
            - word (str): The recommended word
            - definition (str): Word definition
            - difficulty_score (int): Difficulty rating 1-10
            - rationale (str): Why this word was recommended

    Raises:
        StudentNotFoundError: If student profile doesn't exist
        ValueError: If grade_level not in range 6-8

    Example:
        >>> recommendations = generate_recommendations("STU-001", 7, num_words=5)
        >>> len(recommendations)
        5
        >>> recommendations[0]["word"]
        'analyze'

    Note:
        This function makes OpenAI API calls and may be slow for
        large vocabulary profiles. Consider caching results.
    """
    # Implementation...
```

---

## API Documentation

**Document API endpoints thoroughly:**

```python
from fastapi import FastAPI, Path, Query
from typing import Annotated

@app.get(
    "/api/v1/students/{student_id}/profile",
    response_model=StudentProfileResponse,
    summary="Get student vocabulary profile",
    description="""
    Retrieve complete vocabulary profile for a student including:
    - Current vocabulary size and proficiency score
    - Recently acquired words
    - Vocabulary growth trend

    This endpoint returns eventually consistent data (may be delayed by up to 5 seconds).
    """,
    responses={
        200: {
            "description": "Student profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "student_id": "STU-001",
                        "grade_level": 7,
                        "vocabulary_size": 1250,
                        "proficiency_score": 75.5
                    }
                }
            }
        },
        404: {
            "description": "Student not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "student_not_found",
                        "message": "No profile found for student STU-999"
                    }
                }
            }
        }
    },
    tags=["Students"]
)
async def get_student_profile(
    student_id: Annotated[str, Path(description="Student identifier (format: STU-###)")],
    include_vocabulary: Annotated[bool, Query(description="Include full vocabulary list")] = False
):
    """Get student profile endpoint."""
    # Implementation...
```

---

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for docstring standards
- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for API documentation
- **Phase 8 Tasks**: See [../task-list/phases-3-to-9-summary.md](../task-list/phases-3-to-9-summary.md#phase-8-documentation--polish) for documentation deliverables

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [FastAPI Patterns](fastapi-patterns.md)
