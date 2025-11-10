# Logging & Monitoring

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Error Handling](error-handling.md), [AWS Services](aws-services.md)

---

## Structured Logging

**Use JSON for machine-readable logs:**

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields
        if hasattr(record, "student_id"):
            log_data["student_id"] = record.student_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("vocabulator")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("Processing transcript", extra={"student_id": "STU-001"})
```

---

## Correlation IDs

**Track requests across services:**

```python
import uuid
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id")

def set_correlation_id(cid: str = None):
    """Set correlation ID for current context."""
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid

def get_correlation_id() -> str:
    """Get correlation ID for current context."""
    try:
        return correlation_id.get()
    except LookupError:
        return set_correlation_id()

# Middleware to set correlation ID
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(cid)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response

# Use in logging
logger.info("Processing request", extra={"correlation_id": get_correlation_id()})
```

---

## Cross-References

- **Error Handling**: See [error-handling.md](error-handling.md) for error context
- **AWS Services**: See [aws-services.md](aws-services.md) for CloudWatch integration
- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for middleware
- **Phase 0 Tasks**: See [../task-list/phase-0-project-setup.md](../task-list/phase-0-project-setup.md#04-logging-utility-setup) for logging setup

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Error Handling](error-handling.md)
- [AWS Services](aws-services.md)
- [FastAPI Patterns](fastapi-patterns.md)
