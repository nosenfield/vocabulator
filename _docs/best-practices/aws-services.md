# AWS Services Best Practices

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [Performance](performance.md), [Security & Privacy](security-privacy.md)

---

## boto3 Client Management

**Use session and resource clients appropriately:**

```python
import boto3
from botocore.config import Config
from typing import Optional

class AWSClientFactory:
    """Factory for creating configured AWS clients."""

    def __init__(self, region: str = "us-east-1"):
        self.config = Config(
            region_name=region,
            retries={"max_attempts": 3, "mode": "adaptive"},
            max_pool_connections=50
        )
        self.session = boto3.Session()

    def get_dynamodb_client(self):
        """Get DynamoDB client with retry configuration."""
        return self.session.client("dynamodb", config=self.config)

    def get_s3_client(self):
        """Get S3 client with retry configuration."""
        return self.session.client("s3", config=self.config)

# Singleton instance
aws_clients = AWSClientFactory()
```

**Best practices:**
- ✅ Reuse clients (don't create new client per request)
- ✅ Configure retries explicitly
- ✅ Use connection pooling for high throughput
- ✅ Use resource for higher-level operations, client for low-level
- ❌ Don't hardcode credentials (use IAM roles)

---

## DynamoDB Patterns

**Efficient query and scan patterns:**

```python
from typing import List, Optional
from boto3.dynamodb.conditions import Key, Attr

class StudentRepository:
    """Repository for student profile operations."""

    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    async def get_by_id(self, student_id: str) -> Optional[dict]:
        """Get student profile by ID (efficient query)."""
        try:
            response = self.table.get_item(
                Key={"student_id": student_id},
                ConsistentRead=False  # Eventually consistent (cheaper)
            )
            return response.get("Item")
        except ClientError as e:
            logger.error(f"Error fetching student {student_id}: {e}")
            return None

    async def get_by_grade(
        self,
        grade_level: int,
        limit: int = 100
    ) -> List[dict]:
        """Get students by grade level (GSI query)."""
        response = self.table.query(
            IndexName="grade_level-proficiency_score-index",
            KeyConditionExpression=Key("grade_level").eq(grade_level),
            Limit=limit
        )
        return response.get("Items", [])

    async def batch_get(self, student_ids: List[str]) -> List[dict]:
        """Get multiple students in one request (batch operation)."""
        response = boto3.resource("dynamodb").batch_get_item(
            RequestItems={
                self.table.name: {
                    "Keys": [{"student_id": sid} for sid in student_ids]
                }
            }
        )
        return response["Responses"][self.table.name]

    async def update_vocabulary(
        self,
        student_id: str,
        new_words: List[dict]
    ):
        """Update student vocabulary list atomically."""
        self.table.update_item(
            Key={"student_id": student_id},
            UpdateExpression="SET vocabulary_list = list_append(vocabulary_list, :words)",
            ExpressionAttributeValues={":words": new_words},
            ReturnValues="UPDATED_NEW"
        )
```

**Best practices:**
- ✅ Use `get_item` for single-item retrieval (not `query`)
- ✅ Use GSI for queries on non-key attributes
- ✅ Use batch operations for multiple items (up to 25)
- ✅ Use eventually consistent reads when possible (50% cheaper)
- ✅ Use `UpdateExpression` for atomic updates
- ❌ Avoid `scan` operations (expensive and slow)
- ❌ Don't use strongly consistent reads unless necessary

---

## S3 Operations

**Efficient file operations:**

```python
import boto3
from pathlib import Path
from typing import BinaryIO, Optional

class S3Client:
    """Client for S3 operations with best practices."""

    def __init__(self, bucket_name: str):
        self.s3 = boto3.client("s3")
        self.bucket = bucket_name

    async def upload_file(
        self,
        file_path: Path,
        s3_key: str,
        content_type: Optional[str] = None
    ):
        """Upload file to S3 with metadata."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        # Server-side encryption by default
        extra_args["ServerSideEncryption"] = "AES256"

        self.s3.upload_file(
            str(file_path),
            self.bucket,
            s3_key,
            ExtraArgs=extra_args
        )

    async def upload_large_file(
        self,
        file_path: Path,
        s3_key: str,
        part_size: int = 10 * 1024 * 1024  # 10MB parts
    ):
        """Upload large file using multipart upload."""
        config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=part_size,
            multipart_chunksize=part_size
        )

        self.s3.upload_file(
            str(file_path),
            self.bucket,
            s3_key,
            Config=config
        )

    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> str:
        """Generate temporary download URL."""
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expiration
        )

    async def list_files(self, prefix: str) -> List[str]:
        """List all files with given prefix (handles pagination)."""
        files = []
        paginator = self.s3.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if "Contents" in page:
                files.extend([obj["Key"] for obj in page["Contents"]])

        return files
```

**Best practices:**
- ✅ Use multipart upload for files > 5MB
- ✅ Enable server-side encryption by default
- ✅ Use presigned URLs for temporary access (not public buckets)
- ✅ Use pagination for listing large directories
- ✅ Set lifecycle policies for automatic cleanup
- ❌ Don't store sensitive data without encryption
- ❌ Don't make buckets public

---

## Lambda Best Practices

**Optimize for cold starts and performance:**

```python
import os
import boto3
from typing import Any, Dict

# ✅ Initialize clients outside handler (reused across invocations)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STUDENT_TABLE"])
openai_client = OpenAIClient()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler."""

    # ✅ Extract environment variables once
    log_level = os.getenv("LOG_LEVEL", "INFO")

    try:
        # Business logic
        student_id = event["pathParameters"]["student_id"]
        profile = table.get_item(Key={"student_id": student_id})

        return {
            "statusCode": 200,
            "body": json.dumps(profile["Item"])
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing parameter: {e}"})
        }

    except Exception as e:
        logger.exception("Unexpected error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

**Best practices:**
- ✅ Initialize clients outside handler (cold start optimization)
- ✅ Use environment variables for configuration
- ✅ Set appropriate memory (512MB-1GB for most workloads)
- ✅ Use Lambda layers for shared dependencies
- ✅ Keep deployment package small (< 50MB)
- ✅ Use provisioned concurrency for latency-sensitive functions
- ❌ Don't initialize clients inside handler
- ❌ Don't use recursion (risk of runaway costs)

---

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for async patterns
- **Performance**: See [performance.md](performance.md) for optimization strategies
- **Security & Privacy**: See [security-privacy.md](security-privacy.md) for IAM best practices
- **Phase 1 Tasks**: See [../task-list/phase-1-data-layer.md](../task-list/phase-1-data-layer.md) for implementation

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [Performance](performance.md)
- [Security & Privacy](security-privacy.md)
