# Python Development Standards

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [FastAPI Patterns](fastapi-patterns.md), [Testing Standards](testing-standards.md)

---

## Code Style & Formatting

**Use automated formatters and linters:**

```bash
# Format code with black (line length: 88)
black src/ tests/

# Lint with ruff (replaces flake8, isort, pylint)
ruff check src/ tests/

# Type checking with mypy
mypy src/ --strict
```

**Configuration (pyproject.toml):**
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "N", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

**Style Guidelines:**
- Use type hints for all function signatures
- Write docstrings for all public functions (Google or NumPy style)
- Use descriptive variable names (no single letters except loop counters)
- Prefer f-strings over `.format()` or `%` formatting
- Use `pathlib.Path` instead of `os.path` for file operations
- Avoid `import *` (explicit imports only)
- Avoid mutable default arguments (`def func(items=[]): ...`)

**Example:**
```python
from typing import List, Optional
from pathlib import Path

def extract_vocabulary(
    text: str,
    min_word_length: int = 3,
    exclude_stopwords: bool = True
) -> List[str]:
    """Extract unique vocabulary words from text.

    Args:
        text: Input text to analyze
        min_word_length: Minimum word length to include
        exclude_stopwords: Whether to exclude common stopwords

    Returns:
        List of unique vocabulary words, lowercase and sorted

    Raises:
        ValueError: If text is empty or min_word_length < 1
    """
    if not text:
        raise ValueError("Text cannot be empty")
    # Implementation...
```

---

## Dependency Management

**Pin dependencies for reproducibility:**

```txt
# requirements.txt - Production dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
openai==1.3.5
boto3==1.28.85
httpx==0.25.1

# requirements-dev.txt - Development dependencies
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
black==23.11.0
ruff==0.1.5
mypy==1.7.0
```

**Best practices:**
- Use exact version pins for production (`==`)
- Separate dev dependencies from production
- Update dependencies regularly (monthly security review)
- Use `pip-tools` or `poetry` for dependency resolution
- Don't commit virtual environment (`venv/` in `.gitignore`)

---

## Virtual Environments

**Always use virtual environments:**

```bash
# Create virtual environment
python -m venv venv

# Activate (Unix/MacOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Freeze dependencies
pip freeze > requirements-freeze.txt
```

---

## Async/Await Patterns

**Use async for I/O-bound operations:**

```python
import asyncio
from typing import List
import httpx

# Good - Async for I/O operations
async def fetch_multiple_definitions(words: List[str]) -> List[str]:
    """Fetch definitions for multiple words concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_definition(client, word) for word in words]
        return await asyncio.gather(*tasks)

async def fetch_definition(client: httpx.AsyncClient, word: str) -> str:
    response = await client.get(f"https://api.dictionary.com/{word}")
    return response.json()["definition"]

# Bad - Sync in async function (blocks event loop)
async def bad_fetch():
    import time
    time.sleep(5)  # Blocks event loop!
    # Use: await asyncio.sleep(5) instead
```

**When to use async:**
- API calls (OpenAI, external services)
- Database queries (DynamoDB, S3)
- Multiple I/O operations that can run concurrently
- CPU-bound tasks (use multiprocessing instead)
- Simple CRUD operations with no concurrency benefit

---

## Cross-References

- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for async endpoint patterns
- **Testing Standards**: See [testing-standards.md](testing-standards.md) for async test patterns
- **Performance Optimization**: See [performance.md](performance.md) for parallel processing
- **AWS Services**: See [aws-services.md](aws-services.md) for boto3 async patterns

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [FastAPI Patterns](fastapi-patterns.md)
- [Testing Standards](testing-standards.md)
