# OpenAI API Integration

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [Performance](performance.md), [Error Handling](error-handling.md)

---

## Client Configuration

**Create reusable, configured client:**

```python
from openai import AsyncOpenAI
import os
from typing import Optional

class OpenAIClient:
    """Wrapper for OpenAI API with error handling and retry logic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            max_retries=max_retries,
            timeout=timeout
        )
        self.cost_tracker = CostTracker()

    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Send completion request with error handling."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Track costs
            self.cost_tracker.log(
                model=model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
```

---

## Prompt Engineering

**Use structured prompts with templates:**

```python
from jinja2 import Template

VOCABULARY_EXTRACTION_PROMPT = Template("""
You are a vocabulary extraction specialist for middle school education.

TASK: Extract academically significant words from the student text below.

INSTRUCTIONS:
1. Extract words that demonstrate vocabulary usage
2. Exclude common function words (the, a, an, is, are)
3. Exclude words below 3rd grade reading level
4. For each word, provide:
   - Lemmatized form (base form)
   - Usage count
   - One example sentence from the text

STUDENT TEXT:
{{ text }}

OUTPUT FORMAT: Valid JSON only
{
  "words": [
    {
      "word": "analyze",
      "count": 3,
      "example": "We need to analyze the data carefully."
    }
  ]
}
""")

async def extract_vocabulary(text: str) -> list[dict]:
    """Extract vocabulary from text using GPT-4o-mini."""
    prompt = VOCABULARY_EXTRACTION_PROMPT.render(text=text)

    response = await openai_client.complete(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a vocabulary expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower temperature for consistency
        max_tokens=2000
    )

    return json.loads(response)["words"]
```

**Best practices:**
- ✅ Use templates (Jinja2) for reusable prompts
- ✅ Specify output format clearly (JSON preferred)
- ✅ Use lower temperature (0.1-0.3) for consistent extraction
- ✅ Provide clear examples in the prompt
- ✅ Include validation instructions
- ❌ Don't rely on exact output format (parse defensively)

---

## Cost Optimization

**Strategies to minimize OpenAI API costs:**

```python
class CostOptimizer:
    """Optimize OpenAI API usage for cost efficiency."""

    def __init__(self):
        self.cache = {}  # Response cache

    async def extract_vocabulary_batch(
        self,
        texts: list[str],
        batch_size: int = 50
    ) -> list[dict]:
        """Process multiple texts in batches to reduce API calls."""

        # Batch texts together
        batches = [
            texts[i:i + batch_size]
            for i in range(0, len(texts), batch_size)
        ]

        results = []
        for batch in batches:
            # Single API call for multiple texts
            combined_text = "\n---NEXT_TEXT---\n".join(batch)
            response = await self.extract_vocabulary(combined_text)
            results.extend(response)

        return results

    async def extract_with_cache(
        self,
        text: str,
        cache_ttl: int = 3600
    ) -> list[dict]:
        """Extract vocabulary with response caching."""
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < cache_ttl:
                return cached_result

        # Make API call
        result = await self.extract_vocabulary(text)
        self.cache[cache_key] = (result, time.time())
        return result
```

**Cost reduction techniques:**
- ✅ Use GPT-4o-mini for simple tasks (10x cheaper than GPT-4o)
- ✅ Batch multiple requests when possible
- ✅ Cache responses for identical inputs
- ✅ Use shorter prompts (fewer input tokens)
- ✅ Set `max_tokens` to minimum needed
- ✅ Monitor daily spending with alarms
- ❌ Don't use GPT-4o for tasks GPT-4o-mini can handle

---

## Error Handling

**Handle rate limits and transient errors:**

```python
import asyncio
from openai import RateLimitError, APIError

async def call_openai_with_retry(
    func,
    *args,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    **kwargs
):
    """Call OpenAI API with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            wait_time = backoff_factor ** attempt
            logger.warning(
                f"Rate limit hit, retrying in {wait_time}s "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            await asyncio.sleep(wait_time)

        except APIError as e:
            if attempt == max_retries - 1:
                raise

            logger.warning(f"API error: {e}, retrying...")
            await asyncio.sleep(backoff_factor ** attempt)
```

---

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for async patterns
- **Performance**: See [performance.md](performance.md) for caching strategies
- **Error Handling**: See [error-handling.md](error-handling.md) for retry patterns
- **Phase 2 Tasks**: See [../task-list/phase-2-ai-ml-layer.md](../task-list/phase-2-ai-ml-layer.md) for implementation

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [Performance](performance.md)
- [Error Handling](error-handling.md)
