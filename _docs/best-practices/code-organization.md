# Code Organization

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)
**Related:** [Python Development](python-development.md), [FastAPI Patterns](fastapi-patterns.md)

---

## Module Structure

**Organize by domain, not by layer:**

```python
# Good - Domain-driven structure
src/
├── students/              # Student domain
│   ├── models.py          # Student data models
│   ├── repository.py      # Data access
│   ├── service.py         # Business logic
│   └── validators.py      # Validation rules
├── vocabulary/            # Vocabulary domain
│   ├── models.py
│   ├── extractor.py
│   ├── recommender.py
│   └── corpus/
└── processing/            # Processing domain
    ├── pipeline.py
    └── batch.py

# Bad - Layer-based structure (doesn't scale)
src/
├── models/               # All models mixed together
├── repositories/         # All repos mixed together
└── services/             # All services mixed together
```

---

## Dependency Injection

**Inject dependencies for testability:**

```python
# Good - Dependencies injected
class VocabularyService:
    def __init__(
        self,
        openai_client: OpenAIClient,
        student_repo: StudentRepository,
        vocab_repo: VocabularyRepository
    ):
        self.openai = openai_client
        self.students = student_repo
        self.vocabulary = vocab_repo

    async def process_transcript(self, student_id: str, text: str):
        words = await self.openai.extract_vocabulary(text)
        await self.students.update_vocabulary(student_id, words)
        return words

# Easy to test with mocks
def test_process_transcript():
    mock_openai = Mock()
    mock_repo = Mock()
    service = VocabularyService(mock_openai, mock_repo, mock_vocab_repo)
    # Test with mocks...

# Bad - Hard dependencies
class VocabularyService:
    def __init__(self):
        self.openai = OpenAIClient()  # Hard to mock
        self.students = StudentRepository()  # Hard to mock
```

---

## Cross-References

- **Python Development**: See [python-development.md](python-development.md) for module patterns
- **FastAPI Patterns**: See [fastapi-patterns.md](fastapi-patterns.md) for dependency injection
- **Testing Standards**: See [testing-standards.md](testing-standards.md) for testability
- **Architecture**: See [../architecture.md](../architecture.md) for directory structure

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Python Development](python-development.md)
- [FastAPI Patterns](fastapi-patterns.md)
- [Testing Standards](testing-standards.md)
