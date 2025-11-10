# Performance Optimization

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [AWS Services](aws-services.md), [OpenAI Integration](openai-integration.md)

---

## Parallel Processing

**Use multiprocessing for CPU-bound tasks:**

```python
from multiprocessing import Pool, cpu_count
from typing import List, Callable

def process_students_parallel(
    student_ids: List[str],
    processor_func: Callable,
    max_workers: int = None
) -> List[dict]:
    """Process multiple students in parallel."""
    if max_workers is None:
        max_workers = min(cpu_count(), 10)

    with Pool(processes=max_workers) as pool:
        results = pool.map(processor_func, student_ids)

    return results

# Good - Parallel processing for independent tasks
results = process_students_parallel(student_ids, analyze_transcript)

# Bad - Sequential processing (slow)
results = [analyze_transcript(sid) for sid in student_ids]
```

**Use asyncio for I/O-bound tasks:**

```python
import asyncio
from typing import List

async def process_students_async(student_ids: List[str]) -> List[dict]:
    """Process multiple students concurrently (I/O-bound)."""
    tasks = [process_student(sid) for sid in student_ids]
    return await asyncio.gather(*tasks)

async def process_student(student_id: str) -> dict:
    """Process single student (async I/O operations)."""
    # Fetch from DynamoDB
    profile = await fetch_profile(student_id)

    # Call OpenAI API
    vocab = await extract_vocabulary(profile["text"])

    # Update profile
    await update_profile(student_id, vocab)

    return {"student_id": student_id, "status": "complete"}

# Good - Async for I/O operations
results = await process_students_async(student_ids)
```

---

## Caching

**Implement response caching:**

```python
from functools import lru_cache
import hashlib
from typing import Optional

# In-memory cache for expensive computations
@lru_cache(maxsize=1000)
def get_common_core_words(grade_level: int) -> List[str]:
    """Get Common Core words for grade level (cached)."""
    # Expensive database query cached in memory
    return query_vocabulary_database(grade_level)

# Redis cache for distributed systems
import redis

class CacheClient:
    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379)

    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: int = 3600
    ) -> Optional[str]:
        """Get from cache or compute and store."""
        # Try cache first
        cached = self.redis.get(key)
        if cached:
            return cached.decode()

        # Compute and cache
        result = await compute_func()
        self.redis.setex(key, ttl, result)
        return result

# Usage
cache = CacheClient()
vocab = await cache.get_or_compute(
    f"vocab:{student_id}",
    lambda: extract_vocabulary(text),
    ttl=3600
)
```

---

## Database Query Optimization

**Optimize DynamoDB queries:**

```python
# Bad - Scan entire table (expensive)
def get_all_students_slow():
    response = table.scan()
    return response["Items"]

# Good - Query with GSI
def get_students_by_grade(grade: int):
    response = table.query(
        IndexName="grade_level-index",
        KeyConditionExpression=Key("grade_level").eq(grade)
    )
    return response["Items"]

# Good - Batch get for multiple IDs
def get_students_batch(student_ids: List[str]):
    keys = [{"student_id": sid} for sid in student_ids]
    response = dynamodb.batch_get_item(
        RequestItems={table.name: {"Keys": keys}}
    )
    return response["Responses"][table.name]
```

---

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for async patterns
- **AWS Services**: See [aws-services.md](aws-services.md) for DynamoDB optimization
- **OpenAI Integration**: See [openai-integration.md](openai-integration.md) for cost optimization
- **Architecture**: See [../architecture.md](../architecture.md) for performance targets
- **Phase 3 Tasks**: See [../task-list/phases-3-to-9-summary.md](../task-list/phases-3-to-9-summary.md#phase-3-processing-layer) for parallel processing

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [AWS Services](aws-services.md)
- [OpenAI Integration](openai-integration.md)
