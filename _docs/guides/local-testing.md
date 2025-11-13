# Local End-to-End Testing Guide

This guide walks you through testing Vocabulator locally using LocalStack (AWS emulation) and the FastAPI development server.

## Quick Start

### Option 1: Automated Script (Recommended)

Run the complete setup and test script:

```bash
./scripts/run-local-e2e.sh
```

This script will:
1. ✅ Check prerequisites (Python, Docker)
2. ✅ Set up virtual environment
3. ✅ Install dependencies
4. ✅ Start LocalStack
5. ✅ Create DynamoDB tables
6. ✅ Create S3 bucket
7. ✅ Seed vocabulary database
8. ✅ Run integration tests
9. ✅ Start API server

**Note:** The script will start the API server in the foreground. Press `Ctrl+C` to stop it.

### Option 2: Manual Setup

If you prefer to run steps manually:

#### 1. Start LocalStack

```bash
docker-compose up -d localstack
```

Wait for LocalStack to be ready (about 10-30 seconds).

#### 2. Set Up Environment

Create a `.env` file if it doesn't exist:

```bash
cat > .env << EOF
ENVIRONMENT=development
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
LOCALSTACK_ENDPOINT_URL=http://localhost:4566
DYNAMODB_TABLE_PREFIX=vocabulator-dev
S3_BUCKET_NAME=vocabulator-dev-data
LOG_LEVEL=DEBUG
OPENAI_API_KEY=sk-your-key-here  # Optional for mocked tests
EOF
```

#### 3. Set Up Database

```bash
# Activate virtual environment
source venv/bin/activate

# Create DynamoDB tables
python scripts/setup_localstack_tables.py

# Seed vocabulary database (optional)
python scripts/seed_vocabulary_db.py --local
```

#### 4. Start API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

#### 5. Run Tests

In a separate terminal:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test suites
pytest tests/integration/test_e2e_workflow.py -v
pytest tests/integration/test_api_workflows.py -v
```

#### 6. Manual API Testing

Run the manual test script (requires API server to be running):

```bash
python scripts/test_api_manual.py
```

## Testing Workflows

### 1. End-to-End Workflow Test

Tests the complete flow:
- Upload transcript → Extract vocabulary → Update profile → Generate recommendations

```bash
pytest tests/integration/test_e2e_workflow.py -v
```

### 2. API Workflow Test

Tests API endpoints:
- Create student → Upload samples → Retrieve reports

```bash
pytest tests/integration/test_api_workflows.py -v
```

### 3. Manual API Test

Interactive test using the running API server:

```bash
# Terminal 1: Start API server
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Run manual test
python scripts/test_api_manual.py
```

### 4. Data Layer Workflow Test

Test the data layer components directly:

```bash
python scripts/test_workflow.py
```

## API Endpoints to Test

Once the API server is running, you can test these endpoints:

### Health Check
```bash
curl http://localhost:8000/health
```

### Create Student
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
    "transcript_text": "Today we learned about photosynthesis and cellular respiration."
  }'
```

### Get Student Profile
```bash
curl http://localhost:8000/api/v1/students/STU-001/profile
```

### Get Recommendations
```bash
curl http://localhost:8000/api/v1/students/STU-001/recommendations
```

## Interactive API Documentation

The FastAPI server provides interactive documentation:

1. **Swagger UI**: http://localhost:8000/api/v1/docs
   - Interactive API explorer
   - Try endpoints directly from the browser
   - See request/response schemas

2. **ReDoc**: http://localhost:8000/api/v1/redoc
   - Alternative documentation format
   - Clean, readable API reference

## Troubleshooting

### LocalStack Not Starting

```bash
# Check if Docker is running
docker ps

# Check LocalStack logs
docker-compose logs localstack

# Restart LocalStack
docker-compose restart localstack
```

### Port Already in Use

If port 8000 is already in use:

```bash
# Use a different port
uvicorn src.api.main:app --reload --port 8001
```

### Database Tables Not Found

```bash
# Recreate tables
python scripts/setup_localstack_tables.py
```

### OpenAI API Errors

If you see OpenAI API errors:
- Tests use **mocked responses** by default (no API key needed)
- For real OpenAI testing, add `OPENAI_API_KEY` to `.env`
- Check that your API key is valid and has credits

### Import Errors

Make sure you're in the virtual environment:

```bash
source venv/bin/activate
```

## What Gets Tested

### ✅ Data Layer
- DynamoDB operations (create, read, update, query)
- S3 file operations (upload, download)
- Repository patterns
- Data models and validation

### ✅ AI/ML Layer
- Vocabulary extraction (mocked OpenAI)
- Gap analysis (mocked OpenAI)
- Recommendation generation (mocked OpenAI)

### ✅ Processing Layer
- Text processing pipeline
- Parallel execution
- Batch processing (mocked AWS Batch)

### ✅ API Layer
- All 8 REST endpoints
- Request/response validation
- Error handling
- CORS configuration

### ✅ Frontend Layer
- Report template rendering
- Report generation service
- S3 upload and presigned URLs

## Next Steps

After local testing passes:

1. **Deploy to AWS**: Use `./scripts/deploy-infrastructure.sh`
2. **Run Performance Tests**: See Phase 7 tasks
3. **Security Audit**: See Phase 7 tasks
4. **Production Deployment**: Follow deployment guide

## Resources

- **Architecture**: `_docs/architecture.md`
- **API Documentation**: http://localhost:8000/api/v1/docs (when server is running)
- **Task List**: `_docs/task-list.md`
- **Best Practices**: `_docs/best-practices.md`

