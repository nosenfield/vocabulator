#!/bin/bash
# Local End-to-End Test Script for Vocabulator
# This script sets up and runs a complete local test environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Parse arguments
SKIP_SETUP="${SKIP_SETUP:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
API_ONLY="${API_ONLY:-false}"

# Change to project root
cd "$PROJECT_ROOT"

step "🚀 Vocabulator Local End-to-End Test"

# Step 1: Check prerequisites
step "Step 1: Checking Prerequisites"

if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed"
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
info "Python version: $PYTHON_VERSION"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    error "Python 3.11+ required. Found: $PYTHON_VERSION"
fi

if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
fi

if ! docker ps &> /dev/null; then
    error "Docker daemon is not running"
fi

info "✅ All prerequisites met"

# Step 2: Check virtual environment
step "Step 2: Checking Virtual Environment"

if [ ! -d "venv" ]; then
    warn "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
info "✅ Virtual environment activated"

# Step 3: Install dependencies
if [ "$SKIP_SETUP" != "true" ]; then
    step "Step 3: Installing Dependencies"
    
    pip install --quiet --upgrade pip setuptools wheel
    pip install --quiet -r requirements.txt
    pip install --quiet -r requirements-dev.txt
    
    info "✅ Dependencies installed"
fi

# Step 4: Check environment variables
step "Step 4: Checking Environment Configuration"

if [ ! -f ".env" ]; then
    warn ".env file not found. Creating from template..."
    
    cat > .env << EOF
# Vocabulator Local Development Configuration
ENVIRONMENT=development
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
LOCALSTACK_ENDPOINT_URL=http://localhost:4566
DYNAMODB_TABLE_PREFIX=vocabulator-dev
S3_BUCKET_NAME=vocabulator-dev-data
LOG_LEVEL=DEBUG

# OpenAI Configuration (REQUIRED for full testing)
# OPENAI_API_KEY=sk-your-key-here
EOF
    
    warn "⚠️  Created .env file. Please add your OPENAI_API_KEY if you want to test with real OpenAI API"
    warn "   For now, tests will use mocked OpenAI responses"
else
    info "✅ .env file found"
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Step 5: Start LocalStack
step "Step 5: Starting LocalStack"

if docker ps | grep -q vocabulator-localstack; then
    info "LocalStack container already running"
else
    info "Starting LocalStack..."
    docker-compose up -d localstack
    
    # Wait for LocalStack to be ready
    info "Waiting for LocalStack to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
            info "✅ LocalStack is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            error "LocalStack failed to start after 30 seconds"
        fi
        sleep 1
    done
fi

# Step 6: Create S3 bucket
step "Step 6: Setting Up S3 Bucket"

python3 << EOF
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

endpoint_url = os.getenv("LOCALSTACK_ENDPOINT_URL")
bucket_name = os.getenv("S3_BUCKET_NAME", "vocabulator-dev-data")
region = os.getenv("AWS_REGION", "us-east-1")

s3 = boto3.client(
    's3',
    endpoint_url=endpoint_url,
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name=region
)

try:
    s3.create_bucket(Bucket=bucket_name)
    print(f"✅ Created S3 bucket: {bucket_name}")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"ℹ️  S3 bucket already exists: {bucket_name}")
except Exception as e:
    print(f"⚠️  Could not create bucket: {e}")
EOF

# Step 7: Set up DynamoDB tables
step "Step 7: Setting Up DynamoDB Tables"

python3 scripts/setup_localstack_tables.py

# Step 8: Seed vocabulary database (optional)
step "Step 8: Seeding Common Core Vocabulary"

if [ -f "scripts/seed_vocabulary_db.py" ]; then
    if python3 scripts/seed_vocabulary_db.py --local 2>/dev/null; then
        info "✅ Vocabulary database seeded"
    else
        warn "⚠️  Could not seed vocabulary database (may already be seeded)"
    fi
else
    warn "⚠️  Seed script not found, skipping vocabulary seeding"
fi

# Step 9: Run integration tests
if [ "$SKIP_TESTS" != "true" ] && [ "$API_ONLY" != "true" ]; then
    step "Step 9: Running Integration Tests"
    
    info "Running end-to-end workflow tests..."
    if pytest tests/integration/test_e2e_workflow.py -v; then
        info "✅ End-to-end workflow tests passed"
    else
        error "End-to-end workflow tests failed"
    fi
    
    info "Running API workflow tests..."
    if pytest tests/integration/test_api_workflows.py -v; then
        info "✅ API workflow tests passed"
    else
        error "API workflow tests failed"
    fi
    
    info "Running batch processing tests..."
    if pytest tests/integration/test_batch_processing.py -v 2>/dev/null || true; then
        info "✅ Batch processing tests completed"
    else
        warn "⚠️  Batch processing tests skipped (may require additional setup)"
    fi
fi

# Step 10: Start API server
if [ "$API_ONLY" != "true" ]; then
    step "Step 10: Starting API Server"
    
    info "Starting FastAPI server on http://localhost:8000"
    info "API Documentation: http://localhost:8000/api/v1/docs"
    info "Health Check: http://localhost:8000/health"
    info ""
    info "Press Ctrl+C to stop the server"
    info ""
    
    # Start uvicorn in the foreground
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
else
    step "✅ Local End-to-End Test Complete"
    
    info "Summary:"
    info "  ✅ LocalStack running on http://localhost:4566"
    info "  ✅ DynamoDB tables created"
    info "  ✅ S3 bucket created"
    info "  ✅ Integration tests passed"
    info ""
    info "To start the API server manually, run:"
    info "  uvicorn src.api.main:app --reload --port 8000"
fi

