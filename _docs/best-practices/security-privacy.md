# Security & Privacy

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [AWS Services](aws-services.md), [FastAPI Patterns](fastapi-patterns.md)

---

## COPPA Compliance

**Implement anonymous processing:**

```python
from typing import Pattern
import re

STUDENT_ID_PATTERN: Pattern = re.compile(r"^STU-\d{3}$")

def validate_anonymous_student_id(student_id: str) -> bool:
    """Ensure student ID is anonymous (no PII)."""
    if not STUDENT_ID_PATTERN.match(student_id):
        raise ValueError("Invalid student ID format")

    # Reject IDs that look like names
    if any(char.isalpha() and char.isupper() for char in student_id[4:]):
        raise ValueError("Student ID appears to contain name")

    return True

# Never log or store PII
logger.info(f"Processing student: {mask_student_id(student_id)}")

def mask_student_id(student_id: str) -> str:
    """Mask student ID for logging."""
    return f"STU-***{student_id[-2:]}"
```

**Data retention policies:**

```python
# DynamoDB TTL for auto-expiration
recommendation_item = {
    "student_id": "STU-001",
    "recommendation_date": "2025-11-10",
    "words": [...],
    "expires_at": int(time.time()) + (30 * 24 * 3600)  # 30 days
}

# S3 lifecycle policy (in CloudFormation)
# Automatically delete transcripts after 90 days
```

---

## Secrets Management

**Never hardcode secrets:**

```python
import os
from typing import Optional

# Good - Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable required")

# Better - AWS Secrets Manager (production)
import boto3
import json

def get_secret(secret_name: str) -> dict:
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

# Bad - Hardcoded secrets
# OPENAI_API_KEY = "sk-proj-abcd1234..."  # NEVER DO THIS!
```

**.env for development:**
```bash
# .env (gitignored)
OPENAI_API_KEY=sk-proj-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

**.env.example for documentation:**
```bash
# .env.example (committed to git)
OPENAI_API_KEY=your_openai_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
```

---

## Input Validation

**Sanitize all user inputs:**

```python
from typing import Optional
import bleach

def sanitize_text_input(text: str, max_length: int = 50000) -> str:
    """Sanitize user-provided text input."""
    # Remove potential XSS
    text = bleach.clean(text, tags=[], strip=True)

    # Limit length
    if len(text) > max_length:
        raise ValueError(f"Text exceeds maximum length of {max_length}")

    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char == "\n")

    return text.strip()

# Use in API endpoints
@app.post("/api/v1/transcripts/upload")
async def upload_transcript(request: TranscriptUploadRequest):
    sanitized_text = sanitize_text_input(request.text)
    # Process sanitized text...
```

---

## IAM Least Privilege

**Grant minimum permissions required:**

```yaml
# CloudFormation IAM policy
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    Policies:
      - PolicyName: StudentProfileAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            # Specific table access only
            - Effect: Allow
              Action:
                - dynamodb:GetItem
                - dynamodb:PutItem
                - dynamodb:UpdateItem
              Resource: !GetAtt StudentProfilesTable.Arn

            # Specific S3 prefix only
            - Effect: Allow
              Action:
                - s3:GetObject
                - s3:PutObject
              Resource: !Sub "${TranscriptsBucket.Arn}/transcripts/*"

            # CloudWatch Logs (standard)
            - Effect: Allow
              Action:
                - logs:CreateLogGroup
                - logs:CreateLogStream
                - logs:PutLogEvents
              Resource: !Sub "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*"
```

---

## Cross-References

- **AWS Services**: See [aws-services.md](aws-services.md) for IAM configuration
- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for input validation
- **Architecture**: See [../architecture.md](../architecture.md) for COPPA compliance strategy
- **Phase 0 Tasks**: See [../task-list/phase-0-project-setup.md](../task-list/phase-0-project-setup.md) for secrets setup

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [AWS Services](aws-services.md)
- [FastAPI Patterns](fastapi-patterns.md)
- [Architecture](../architecture.md)
