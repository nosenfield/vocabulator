# Error Handling

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [FastAPI Patterns](fastapi-patterns.md), [Logging & Monitoring](logging-monitoring.md)

---

## Exception Hierarchy

**Create custom exceptions:**

```python
class VocabulatorError(Exception):
    """Base exception for Vocabulator."""
    pass

class StudentNotFoundError(VocabulatorError):
    """Student profile not found."""
    pass

class VocabularyExtractionError(VocabulatorError):
    """Failed to extract vocabulary."""
    pass

class OpenAIAPIError(VocabulatorError):
    """OpenAI API request failed."""
    pass

# Usage
def get_student_profile(student_id: str) -> dict:
    profile = student_repo.get(student_id)
    if not profile:
        raise StudentNotFoundError(f"No profile for student {student_id}")
    return profile
```

---

## Error Context

**Provide rich error context:**

```python
import traceback
from typing import Optional

class ErrorContext:
    """Capture error context for debugging."""

    def __init__(
        self,
        operation: str,
        student_id: Optional[str] = None,
        **kwargs
    ):
        self.operation = operation
        self.student_id = student_id
        self.context = kwargs

    def log_error(self, error: Exception):
        """Log error with full context."""
        logger.error(
            f"Error in {self.operation}",
            extra={
                "student_id": self.student_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": self.context,
                "traceback": traceback.format_exc()
            }
        )

# Usage
try:
    ctx = ErrorContext(
        operation="vocabulary_extraction",
        student_id="STU-001",
        text_length=1500,
        model="gpt-4o-mini"
    )
    result = await extract_vocabulary(text)
except Exception as e:
    ctx.log_error(e)
    raise
```

---

## Cross-References

- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for HTTPException patterns
- **Logging & Monitoring**: See [logging-monitoring.md](logging-monitoring.md) for error logging
- **OpenAI Integration**: See [openai-integration.md](openai-integration.md) for retry patterns
- **Testing Standards**: See [testing-standards.md](testing-standards.md) for testing error handling

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [FastAPI Patterns](fastapi-patterns.md)
- [Logging & Monitoring](logging-monitoring.md)
