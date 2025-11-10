# Phase 0: Project Setup & Foundation

**Total Estimated Time:** 8-12 hours (2-3 days)
**Priority:** 🔴 P0 (All tasks)
**Dependencies:** None

---

## Overview

Phase 0 establishes the foundational development environment and project structure. All subsequent phases depend on successful completion of these tasks.

**Key Deliverables:**
- Working Python 3.11+ development environment
- Complete project directory structure
- Configuration management system
- Structured logging utilities

---

## 0.1 Development Environment Setup

**Priority:** 🔴 P0
**Estimated Time:** 2-3 hours
**Dependencies:** None

### Tasks
- [ ] Create Python virtual environment (Python 3.11+)
- [ ] Install core dependencies (FastAPI, pytest, boto3, openai)
- [ ] Set up `.env.example` and `.env` files
- [ ] Install development tools (black, ruff, mypy, pytest-cov)
- [ ] Configure pre-commit hooks for code quality
- [ ] Set up LocalStack for AWS emulation
- [ ] Create Docker Compose file for local services
- [ ] Verify setup with hello-world test

### Acceptance Criteria
- `pytest --version` runs successfully
- `pip list` shows all required packages
- LocalStack starts without errors
- Sample test passes

### Files Created
- `requirements.txt`
- `requirements-dev.txt`
- `.env.example`
- `docker-compose.yml`
- `.pre-commit-config.yaml`
- `tests/test_setup.py`

### Related Documentation
- See [best-practices.md](../best-practices.md) - Python Development Standards
- See [architecture.md](../architecture.md) - Technology Stack section

---

## 0.2 Project Structure Creation

**Priority:** 🔴 P0
**Estimated Time:** 1 hour
**Dependencies:** 0.1

### Tasks
- [ ] Create all directories per architecture.md structure
- [ ] Add `__init__.py` files to all Python packages
- [ ] Create placeholder README.md files for major directories
- [ ] Set up pytest configuration (`pytest.ini`, `conftest.py`)
- [ ] Create `pyproject.toml` for project metadata
- [ ] Initialize git repository (if not already done)
- [ ] Configure `.gitignore` for Python, AWS, IDE files

### Acceptance Criteria
- All directories from architecture.md exist
- `pytest tests/` discovers test directory
- Import statements work: `from src.api import main`

### Files Created
- Complete directory structure (see architecture.md)
- `pytest.ini`
- `pyproject.toml`
- `tests/conftest.py`
- `.gitignore` (updated)

### Directory Structure Reference
```
vocabulator/
├── src/
│   ├── api/
│   ├── processing/
│   ├── ai/
│   ├── data/
│   ├── vocabulary/
│   ├── utils/
│   └── frontend/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── mocks/
├── infrastructure/
├── scripts/
└── _docs/
```

### Related Documentation
- See [architecture.md](../architecture.md) - Complete Directory Structure section
- See [best-practices.md](../best-practices.md) - Code Organization section

---

## 0.3 Configuration Management System

**Priority:** 🔴 P0 🧪
**Estimated Time:** 3-4 hours
**Dependencies:** 0.2

### Tasks
- [ ] 🧪 Write tests for `src/utils/config.py`
- [ ] Implement configuration loader (environment variables)
- [ ] Add validation for required config values
- [ ] Support multiple environments (dev, staging, prod)
- [ ] Create configuration dataclasses with Pydantic
- [ ] Add secrets management integration (AWS Secrets Manager stub)
- [ ] Document all configuration options

### Acceptance Criteria
- Tests pass for config loading and validation
- Missing required config raises clear error
- Config values accessible via type-safe objects
- Environment switching works correctly

### Files Created
- `src/utils/config.py`
- `tests/unit/test_config.py`
- `.env.example` (updated with all variables)

### Environment Variables Required
```bash
ENVIRONMENT=development
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
OPENAI_API_KEY=sk-...
S3_BUCKET_NAME=vocabulator-data-dev
DYNAMODB_TABLE_PREFIX=vocabulator-dev
LOG_LEVEL=INFO
```

### Related Documentation
- See [best-practices.md](../best-practices.md) - Configuration Management section
- See [best-practices.md](../best-practices.md) - Security & Privacy (Secrets Management)

---

## 0.4 Logging Utility Setup

**Priority:** 🔴 P0 🧪
**Estimated Time:** 2-3 hours
**Dependencies:** 0.3

### Tasks
- [ ] 🧪 Write tests for `src/utils/logger.py`
- [ ] Implement structured JSON logging
- [ ] Add correlation ID support for request tracing
- [ ] Configure log levels per environment
- [ ] Add CloudWatch Logs integration (stub for local)
- [ ] Create logger factory for different components
- [ ] Add sensitive data masking (student IDs, API keys)

### Acceptance Criteria
- Logs output in JSON format
- Correlation IDs propagate through function calls
- Log levels filter correctly (DEBUG in dev, INFO in prod)
- Sensitive data is masked in logs

### Files Created
- `src/utils/logger.py`
- `tests/unit/test_logger.py`

### Related Documentation
- See [best-practices.md](../best-practices.md) - Logging & Monitoring section
- See [architecture.md](../architecture.md) - Monitoring & Observability section

---

## Phase 0 Completion Checklist

Before proceeding to Phase 1, verify:

- [ ] All Phase 0 tasks completed (0.1-0.4)
- [ ] All tests passing (pytest shows green)
- [ ] Code formatted and linted (black, ruff, mypy pass)
- [ ] LocalStack running and accessible
- [ ] Configuration loads successfully for all environments
- [ ] Logging outputs structured JSON
- [ ] Git repository initialized with initial commit
- [ ] Memory Bank updated with Phase 0 completion

### Next Phase
**Proceed to:** [Phase 1: Data Layer & Storage](phase-1-data-layer.md)

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Phase 1: Data Layer](phase-1-data-layer.md)
- [architecture.md](../architecture.md)
- [best-practices.md](../best-practices.md)
