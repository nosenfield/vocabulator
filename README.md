# Vocabulator

**Personalized Vocabulary Recommendation Engine for Middle School Students**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![AWS](https://img.shields.io/badge/AWS-Serverless-orange.svg)](https://aws.amazon.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

Vocabulator is an AI-powered system that analyzes student conversation transcripts and writing samples to identify vocabulary gaps and generate personalized word recommendations for middle school students (grades 6-8). The system uses OpenAI's GPT models to extract vocabulary, analyze proficiency levels, and recommend age-appropriate words aligned with Common Core standards.

### Key Features

- 🤖 **AI-Powered Analysis**: Uses GPT-4o-mini for vocabulary extraction and GPT-4o for gap analysis
- 📊 **Personalized Recommendations**: Generates 10-15 tailored words per student based on their current proficiency
- 🔒 **COPPA-Compliant**: Anonymous student IDs only, no PII collection
- ⚡ **Batch Processing**: Process entire classrooms in parallel via AWS Batch
- 📈 **Progress Tracking**: Monitor vocabulary growth over time with HTML reports
- 🎯 **Common Core Aligned**: Recommendations based on grade-level standards

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for LocalStack)
- OpenAI API key

### Installation

```bash
# Clone repository
git clone <repo-url>
cd vocabulator

# Run setup script
./scripts/setup-dev-env.sh

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Start LocalStack (AWS emulation)
docker-compose up -d localstack

# Initialize database
python scripts/setup_localstack_tables.py
python scripts/seed_vocabulary_db.py --local

# Run tests
pytest

# Start API server
uvicorn src.api.main:app --reload
```

**API will be available at:** `http://localhost:8000`  
**Interactive docs:** `http://localhost:8000/api/v1/docs`

---

## Architecture

Vocabulator is built on a serverless-first architecture using AWS services:

```
┌─────────────────────────────────────────┐
│  Frontend Layer (S3 + CloudFront)      │
│  - HTML Reports & Visualizations       │
└─────────────────────────────────────────┘
                  ▲
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────┐
│  API Layer (Lambda + API Gateway)      │
│  - RESTful endpoints                    │
└─────────────────────────────────────────┘
                  ▲
                  ▼
┌─────────────────────────────────────────┐
│  Processing Layer (AWS Batch + Fargate) │
│  - Parallel batch processing            │
└─────────────────────────────────────────┘
                  ▲
                  ▼
┌─────────────────────────────────────────┐
│  AI/ML Layer (OpenAI API)              │
│  - Vocabulary extraction               │
│  - Gap analysis & recommendations      │
└─────────────────────────────────────────┘
                  ▲
                  ▼
┌─────────────────────────────────────────┐
│  Data Layer (DynamoDB + S3)            │
│  - Student profiles                    │
│  - Recommendations                     │
│  - Raw transcripts & reports           │
└─────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **AI/ML**: OpenAI SDK (GPT-4o-mini, GPT-4o)
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Compute**: AWS Lambda, AWS Batch + Fargate
- **Infrastructure**: CloudFormation (IaC)
- **Testing**: pytest, LocalStack

---

## Documentation

### For Developers

- 📖 [Developer Onboarding Guide](_docs/developer-onboarding-guide.md) - Get started developing
- 🏗️ [Architecture Documentation](_docs/architecture.md) - System design and technical details
- 🔌 [API Documentation](_docs/api-documentation.md) - Complete API reference
- ✅ [Best Practices](_docs/best-practices.md) - Coding standards and patterns
- 📚 [Required Reading](_docs/required-reading.md) - Learning resources

### For Users

- 👩‍🏫 [Teacher User Guide](_docs/teacher-user-guide.md) - How to use Vocabulator
- 📋 [Product Requirements](_docs/PRD_Flourish_Schools_Personalized_Vocabulary_Recommendation_Engine_for_.md) - Product specifications

### Project Management

- ✅ [Task List](_docs/task-list.md) - Development roadmap
- 📊 [Task Tracker](_docs/task-tracker.md) - Progress tracking
- 🚀 [Deployment Guide](_docs/deployment-guide.md) - AWS deployment instructions

---

## Project Structure

```
vocabulator/
├── src/                    # Source code
│   ├── api/               # FastAPI application
│   ├── data/              # Data layer (DynamoDB, S3)
│   ├── ai/                # AI/ML layer (OpenAI)
│   ├── processing/        # Processing pipeline
│   ├── vocabulary/        # Common Core vocabulary
│   ├── frontend/          # Report generation
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── infrastructure/        # CloudFormation templates
├── scripts/               # Utility scripts
└── _docs/                 # Documentation
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_student_repository.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all checks
pre-commit run --all-files
```

### Test-First Development

We follow test-first development (TDD):

1. **Write failing test** (RED)
2. **Implement feature** (GREEN)
3. **Refactor** (REFACTOR)

See [Test-First Workflow Guide](_docs/guides/test-first-workflow.md) for details.

---

## API Usage

### Create Student Profile

```bash
curl -X POST http://localhost:8000/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-001",
    "grade_level": 7
  }'
```

### Upload Transcript

```bash
curl -X POST http://localhost:8000/api/v1/transcripts/upload \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-001",
    "text": "Today we learned about photosynthesis and how plants convert sunlight into energy.",
    "session_date": "2025-11-10",
    "grade_level": 7
  }'
```

### Get Recommendations

```bash
curl http://localhost:8000/api/v1/students/STU-001/recommendations
```

See [API Documentation](_docs/api-documentation.md) for complete reference.

---

## Privacy & Security

### COPPA Compliance

Vocabulator is designed to be COPPA-compliant:

- ✅ **Anonymous Student IDs**: Uses `STU-XXX` format only
- ✅ **No PII Collection**: No names, emails, or addresses
- ✅ **Secure Storage**: All data encrypted at rest and in transit
- ✅ **Data Retention**: Configurable retention policies

### Security Features

- Server-side encryption (AES256) for S3
- IAM roles with least privilege
- Input validation and sanitization
- Path traversal protection
- Request ID tracking for audit trails

---

## Cost Estimates

**Target:** $51/month for 500 students

**Cost Breakdown:**
- OpenAI API: ~$35/month (GPT-4o-mini + GPT-4o)
- AWS Services: ~$16/month (Lambda, DynamoDB, S3, Batch)
- Infrastructure: Pay-per-use model

See [Architecture Documentation](_docs/architecture.md) for detailed cost analysis.

---

## Contributing

1. Read the [Developer Onboarding Guide](_docs/developer-onboarding-guide.md)
2. Follow [Best Practices](_docs/best-practices.md)
3. Write tests first (TDD)
4. Run code quality checks before committing
5. Update documentation as needed

---

## Status

**Current Phase:** Phase 8 - Documentation & Polish ✅ COMPLETE

**Progress:** 42/71 tasks complete (59.2%)

**Completed Phases:**
- ✅ Phase 0: Project Setup & Foundation
- ✅ Phase 1: Data Layer & Storage
- ✅ Phase 2: AI/ML Layer
- ✅ Phase 3: Processing Layer
- ✅ Phase 4: API Layer
- ✅ Phase 5: Frontend Layer
- ✅ Phase 6: Infrastructure & Deployment
- ✅ Phase 7: Testing & Quality Assurance
- 🔄 Phase 8: Documentation & Polish (in progress)
- ⏳ Phase 9: MVP Launch Preparation

See [Task Tracker](_docs/task-tracker.md) for detailed progress.

---

## License

[License information to be added]

---

## Support

- **Documentation**: See `_docs/` directory
- **Issues**: [GitHub Issues URL]
- **Email**: [Support Email]

---

## Acknowledgments

- **Organization**: Flourish Schools
- **AI Provider**: OpenAI
- **Cloud Provider**: Amazon Web Services

---

**Version:** 1.0.0 (MVP)  
**Last Updated:** 2025-11-12

