# Git Workflow

**Part of:** [Vocabulator Best Practices Guide](../best-practices.md)

---

## Commit Messages

**Write clear, descriptive commit messages:**

```bash
# ✅ Good commit messages
git commit -m "feat: add vocabulary extraction with GPT-4o-mini"
git commit -m "fix: handle rate limit errors in OpenAI client"
git commit -m "test: add integration tests for batch processing"
git commit -m "docs: update API documentation with examples"
git commit -m "refactor: extract common DynamoDB logic to base repository"

# ❌ Bad commit messages
git commit -m "updates"
git commit -m "fix bug"
git commit -m "WIP"
```

**Commit message format:**
```
<type>: <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `style`: Code style changes (formatting)

---

## Branch Strategy

**Use feature branches:**

```bash
# Create feature branch
git checkout -b feat/vocabulary-extraction

# Make changes and commit
git add src/processing/text_analyzer.py tests/unit/test_text_analyzer.py
git commit -m "feat: implement vocabulary extraction with GPT-4o-mini"

# Push to remote
git push origin feat/vocabulary-extraction

# Create pull request on GitHub
# After review and approval, merge to main
```

**Branch naming:**
- `feat/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `test/test-description` - Test additions
- `docs/doc-description` - Documentation updates

---

## Pull Request Guidelines

**PR checklist:**
- [ ] Tests written and passing (for code changes)
- [ ] Code coverage maintained or improved
- [ ] Linting passes (black, ruff, mypy)
- [ ] Documentation updated (if needed)
- [ ] PR description explains what and why
- [ ] Self-reviewed code for obvious issues
- [ ] Breaking changes documented
- [ ] Memory Bank updated (if relevant)

**PR description template:**
```markdown
## What
Brief description of changes

## Why
Reason for the changes (link to issue/task)

## How
Technical approach and design decisions

## Testing
How was this tested? Manual testing steps if applicable

## Screenshots
(If UI changes)

## Checklist
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Reviewed by self
```

---

## Cross-References

- **Testing Standards**: See [testing-standards.md](testing-standards.md) for test requirements
- **Documentation**: See [documentation.md](documentation.md) for documentation standards
- **Phase 6 Tasks**: See [../task-list/phases-3-to-9-summary.md](../task-list/phases-3-to-9-summary.md#phase-6-infrastructure--deployment) for CI/CD setup

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Master Best Practices Guide](../best-practices.md)
- [Testing Standards](testing-standards.md)
- [Documentation](documentation.md)
