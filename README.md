# Vocabulator

**Personalized Vocabulary Recommendation Engine for Middle School Students**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.0+-red.svg)](https://kit.svelte.dev/)
[![AWS](https://img.shields.io/badge/AWS-Serverless-orange.svg)](https://aws.amazon.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Live Dashboard**: [https://dashboard-three-mu-74.vercel.app](https://dashboard-three-mu-74.vercel.app)  
**API Endpoint**: [https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1](https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1)

---

## Overview

Vocabulator is an AI-powered system that analyzes student conversation transcripts and writing samples to identify vocabulary gaps and generate personalized word recommendations for middle school students (grades 6-8). The system uses OpenAI's GPT models to extract vocabulary, analyze proficiency levels, and recommend age-appropriate words aligned with Common Core standards.

### Key Features

- 🤖 **AI-Powered Analysis**: Uses GPT-4o-mini for vocabulary extraction and gap analysis, GPT-4o for recommendations
- 📊 **Personalized Recommendations**: Generates 10-15 tailored words per student based on their current proficiency
- 🎨 **Interactive Dashboard**: Modern web dashboard for teachers to view student profiles, vocabulary growth, and recommendations
- 🔒 **COPPA-Compliant**: Anonymous student IDs only, no PII collection
- ⚡ **Optimized Processing**: Fast vocabulary extraction (~3 seconds) with background recommendation generation
- 📈 **Progress Tracking**: Monitor vocabulary growth over time with interactive charts
- 🎯 **Common Core Aligned**: Recommendations based on grade-level standards
- ☁️ **Serverless Architecture**: Fully deployed on AWS Lambda, API Gateway, and DynamoDB

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)
- Docker & Docker Compose (for LocalStack - optional for local dev)
- OpenAI API key
- AWS Account (for deployment)

### Local Development Setup

#### Backend (FastAPI)

```bash
# Clone repository
git clone <repo-url>
cd vocabulator

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key and AWS credentials

# Start LocalStack (AWS emulation) - optional
docker-compose up -d localstack

# Initialize database (if using LocalStack)
python scripts/setup_localstack_tables.py
python scripts/seed_vocabulary_db.py --local

# Run tests
pytest

# Start API server
uvicorn src.api.main:app --reload --port 8000
```

**API will be available at:** `http://localhost:8000`  
**Interactive docs:** `http://localhost:8000/api/v1/docs`

#### Frontend Dashboard (SvelteKit)

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Create .env file
echo "VITE_API_BASE=http://localhost:8000/api/v1" > .env

# Start development server
npm run dev

# Or open in browser automatically
npm run dev -- --open
```

**Dashboard will be available at:** `http://localhost:5173`

### Production Deployment

See [Deployment Guide](_docs/deployment-guide.md) for complete AWS deployment instructions.

**Quick Deploy:**

1. **Backend (AWS Lambda + API Gateway)**
   ```bash
   # Package Lambda function
   ./scripts/package-lambda-docker.sh
   
   # Upload and deploy
   ./scripts/deploy-infrastructure.sh
   ```

2. **Frontend (Vercel)**
   ```bash
   cd dashboard
   vercel --prod
   # Set VITE_API_BASE environment variable in Vercel dashboard
   ```

---

## Architecture

Vocabulator is built on a serverless-first architecture using AWS services:

```
┌─────────────────────────────────────────┐
│  Frontend Layer                         │
│  - SvelteKit Dashboard (Vercel)        │
│  - HTML Reports (S3 + CloudFront)      │
└─────────────────────────────────────────┘
                  ▲
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────┐
│  API Layer (Lambda + API Gateway)      │
│  - RESTful endpoints                    │
│  - FastAPI application                  │
└─────────────────────────────────────────┘
                  ▲
                  ▼
┌─────────────────────────────────────────┐
│  Processing Layer                       │
│  - Fast vocabulary extraction (~3s)    │
│  - Background recommendation generation │
│  - AWS Batch (optional, for large jobs) │
└─────────────────────────────────────────┘
                  ▲
                  ▼
┌─────────────────────────────────────────┐
│  AI/ML Layer (OpenAI API)              │
│  - Vocabulary extraction (GPT-4o-mini) │
│  - Gap analysis (GPT-4o-mini)          │
│  - Recommendations (GPT-4o)             │
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

**Backend:**
- Python 3.11+, FastAPI
- AWS Lambda, API Gateway
- Amazon DynamoDB, S3
- CloudFormation (IaC)

**Frontend:**
- SvelteKit with TypeScript
- Bootstrap 5
- Chart.js
- Vercel (deployment)

**AI/ML:**
- OpenAI SDK (GPT-4o-mini, GPT-4o)
- Custom prompts for vocabulary analysis

**Testing & Development:**
- pytest, LocalStack
- Docker for Lambda packaging

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
- 🎨 [Dashboard README](dashboard/README.md) - Dashboard setup and deployment
- 🚀 [Dashboard Deployment Guide](dashboard/DEPLOYMENT.md) - Vercel deployment instructions

### Project Management

- ✅ [Task List](_docs/task-list.md) - Development roadmap
- 📊 [Task Tracker](_docs/task-tracker.md) - Progress tracking
- 🚀 [Deployment Guide](_docs/deployment-guide.md) - AWS deployment instructions

---

## Project Structure

```
vocabulator/
├── src/                    # Backend source code
│   ├── api/               # FastAPI application
│   ├── data/              # Data layer (DynamoDB, S3)
│   ├── ai/                # AI/ML layer (OpenAI)
│   ├── processing/        # Processing pipeline
│   ├── vocabulary/        # Common Core vocabulary
│   ├── frontend/          # HTML report generation
│   └── utils/             # Utilities
├── dashboard/              # Frontend dashboard (SvelteKit)
│   ├── src/               # SvelteKit source code
│   │   ├── routes/        # Page routes
│   │   ├── lib/           # Components, stores, utilities
│   │   └── data/          # Mock data
│   └── static/            # Static assets
├── tests/                 # Test suite
├── infrastructure/        # CloudFormation templates
│   ├── cloudformation/   # AWS infrastructure as code
│   └── docker/            # Dockerfiles for Lambda/Batch
├── scripts/               # Utility scripts
│   ├── package-lambda-docker.sh  # Lambda packaging (Docker)
│   ├── deploy-infrastructure.sh  # AWS deployment
│   └── seed_mock_dashboard_data.py  # Mock data seeding
├── memory-bank/           # Project context and progress tracking
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

## Usage

### Using the Dashboard

1. **Access the Dashboard**: Navigate to [https://dashboard-three-mu-74.vercel.app](https://dashboard-three-mu-74.vercel.app)
2. **Sync Students**: Click "Sync with Google Classroom" to load mock student data
3. **View Students**: Browse the student table, filter by class, and sort by various columns
4. **View Student Profile**: Click on a student to see their vocabulary profile, growth chart, and recommendations
5. **Submit Assignments**: Use the assignment selector to submit writing samples and see vocabulary updates in real-time

### API Usage

#### Create Student Profile

```bash
curl -X POST https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1/students \
  -H "Content-Type: application/json" \
  -H "Origin: https://dashboard-three-mu-74.vercel.app" \
  -d '{
    "student_id": "STU-001",
    "grade_level": 7,
    "first_name": "Alex",
    "last_initial": "S"
  }'
```

#### Upload Writing Sample

```bash
curl -X POST https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1/writing/upload \
  -H "Content-Type: application/json" \
  -H "Origin: https://dashboard-three-mu-74.vercel.app" \
  -d '{
    "student_id": "STU-001",
    "text": "Today we learned about photosynthesis and how plants convert sunlight into energy.",
    "grade_level": 7
  }'
```

#### Get Recommendations

```bash
curl https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1/students/STU-001/recommendations \
  -H "Origin: https://dashboard-three-mu-74.vercel.app"
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

**Current Phase:** MVP Complete ✅

**Deployment Status:**
- ✅ **Backend API**: Deployed to AWS (Lambda + API Gateway)
- ✅ **Dashboard**: Deployed to Vercel
- ✅ **Database**: DynamoDB tables configured
- ✅ **CORS**: Configured for dashboard access

**Completed Features:**
- ✅ Student profile management
- ✅ Vocabulary extraction from transcripts and writing samples
- ✅ Gap analysis using ZPD principles
- ✅ Personalized recommendation generation
- ✅ Interactive teacher dashboard
- ✅ Vocabulary growth tracking with charts
- ✅ Fast processing pipeline (optimized for UX)
- ✅ COPPA-compliant anonymous student IDs
- ✅ Common Core vocabulary alignment

**Live URLs:**
- **Dashboard**: https://dashboard-three-mu-74.vercel.app
- **API**: https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1
- **API Docs**: https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1/docs

See [Task Tracker](_docs/task-tracker.md) for detailed progress.

---

## License

[License information to be added]

---

## Troubleshooting

### Dashboard Issues

**CORS Errors:**
- Ensure the backend Lambda function has `CORS_ALLOWED_ORIGINS` environment variable set
- Include your Vercel domain in the allowed origins list
- Check that API Gateway has OPTIONS method configured for CORS preflight

**Environment Variables:**
- Dashboard requires `VITE_API_BASE` to be set in production
- Set this in Vercel project settings → Environment Variables
- Format: `https://your-api-gateway-url/api/v1`

**SSR Errors:**
- Dashboard uses client-side rendering (SSR disabled)
- If you see 500 errors, check Vercel build logs
- Ensure all API calls are made in `onMount` or user-triggered events

### Backend Issues

**Lambda Import Errors:**
- Use `scripts/package-lambda-docker.sh` to build Linux-compatible packages
- Ensure all dependencies are included in the package
- Check CloudWatch logs for specific import errors

**DynamoDB Access:**
- Verify IAM role has `dynamodb:DescribeTable` permission
- Check table names match environment configuration
- Ensure tables exist in the correct AWS region

See [Dashboard README](dashboard/README.md) and [Deployment Guide](_docs/deployment-guide.md) for more troubleshooting tips.

---

## Support

- **Documentation**: See `_docs/` directory
- **Dashboard Documentation**: See `dashboard/README.md`
- **Issues**: [GitHub Issues URL]
- **Email**: [Support Email]

---

## Acknowledgments

- **Organization**: Flourish Schools
- **AI Provider**: OpenAI
- **Cloud Provider**: Amazon Web Services

---

**Version:** 1.0.0 (MVP)  
**Last Updated:** 2025-11-13  
**Status:** Production Ready ✅

