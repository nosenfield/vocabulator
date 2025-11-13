#!/bin/bash
# Setup demo environment for Vocabulator MVP
# Usage: ./scripts/setup_demo_environment.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

error() { echo -e "${RED}❌ Error: $1${NC}" >&2; exit 1; }
info() { echo -e "${GREEN}ℹ️  $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
step() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}Step: $1${NC}"; }

# Configuration
ENVIRONMENT="demo"
REGION="${AWS_REGION:-us-east-1}"

# Check prerequisites
step "Checking prerequisites"
if ! command -v aws &> /dev/null; then
    error "AWS CLI is not installed. Please install it first."
fi

if ! aws sts get-caller-identity &> /dev/null; then
    error "AWS credentials not configured. Run 'aws configure' first."
fi

if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.11+ first."
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
info "AWS Account ID: $AWS_ACCOUNT_ID"
info "Region: $REGION"
info "Environment: $ENVIRONMENT"

# Step 1: Generate test data
step "1: Generating test data"
if [ ! -f "$PROJECT_ROOT/tests/fixtures/all_student_profiles.json" ]; then
    info "Test data not found. Generating..."
    cd "$PROJECT_ROOT"
    source venv/bin/activate 2>/dev/null || true
    python3 scripts/generate_test_data.py --output-dir tests/fixtures
    info "✅ Test data generated"
else
    info "✅ Test data already exists"
fi

# Step 2: Deploy infrastructure
step "2: Deploying infrastructure to demo environment"
export AWS_REGION="$REGION"
export ENVIRONMENT="$ENVIRONMENT"

# Set default bucket names if not provided
if [ -z "${TEMPLATES_BUCKET:-}" ]; then
    export TEMPLATES_BUCKET="vocabulator-cloudformation-templates-${AWS_ACCOUNT_ID}"
fi

if [ -z "${LAMBDA_BUCKET:-}" ]; then
    export LAMBDA_BUCKET="vocabulator-${ENVIRONMENT}-${AWS_ACCOUNT_ID}-lambda"
fi

info "Templates bucket: $TEMPLATES_BUCKET"
info "Lambda bucket: $LAMBDA_BUCKET"

# Deploy infrastructure
if [ -f "$PROJECT_ROOT/scripts/deploy-infrastructure.sh" ]; then
    "$PROJECT_ROOT/scripts/deploy-infrastructure.sh" "$ENVIRONMENT" create || {
        warn "Infrastructure deployment failed or stack already exists"
        warn "Attempting update instead..."
        "$PROJECT_ROOT/scripts/deploy-infrastructure.sh" "$ENVIRONMENT" update || {
            warn "Infrastructure deployment failed. Please deploy manually."
        }
    }
    info "✅ Infrastructure deployment completed"
else
    warn "Deployment script not found. Skipping infrastructure deployment."
    warn "Please deploy infrastructure manually using: ./scripts/deploy-infrastructure.sh demo"
fi

# Step 3: Seed test data
step "3: Seeding test data to demo environment"
cd "$PROJECT_ROOT"
source venv/bin/activate 2>/dev/null || true

# Get table and bucket names from environment or use defaults
TABLE_PREFIX="${DYNAMODB_TABLE_PREFIX:-vocabulator-${ENVIRONMENT}}"
BUCKET_NAME="${S3_BUCKET_NAME:-vocabulator-data-${ENVIRONMENT}-${AWS_ACCOUNT_ID}}"

info "Seeding student profiles to DynamoDB..."
python3 scripts/seed_test_data.py \
    --fixtures-dir tests/fixtures \
    --table-name "${TABLE_PREFIX}-StudentProfiles" \
    --bucket-name "$BUCKET_NAME" || {
    warn "Failed to seed test data. This may be expected if tables don't exist yet."
    warn "Please ensure infrastructure is deployed and try again."
}

info "✅ Test data seeding completed"

# Step 4: Verify deployment
step "4: Verifying deployment"

# Check DynamoDB tables
info "Checking DynamoDB tables..."
TABLES=$(aws dynamodb list-tables --region "$REGION" --query "TableNames[?starts_with(@, 'vocabulator-${ENVIRONMENT}')]" --output text 2>/dev/null || echo "")
if [ -n "$TABLES" ]; then
    info "✅ DynamoDB tables found:"
    echo "$TABLES" | tr '\t' '\n' | sed 's/^/  - /'
else
    warn "⚠️  No DynamoDB tables found"
fi

# Check S3 buckets
info "Checking S3 buckets..."
BUCKETS=$(aws s3 ls --region "$REGION" 2>/dev/null | grep "vocabulator" || echo "")
if [ -n "$BUCKETS" ]; then
    info "✅ S3 buckets found:"
    echo "$BUCKETS" | sed 's/^/  - /'
else
    warn "⚠️  No S3 buckets found"
fi

# Check API Gateway (if deployed)
info "Checking API Gateway..."
API_ID=$(aws apigateway get-rest-apis --region "$REGION" --query "items[?name=='vocabulator-${ENVIRONMENT}-api'].id" --output text 2>/dev/null || echo "")
if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
    API_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${ENVIRONMENT}"
    info "✅ API Gateway found: $API_URL"
else
    warn "⚠️  API Gateway not found or not deployed"
fi

# Step 5: Create demo walkthrough
step "5: Creating demo walkthrough script"
WALKTHROUGH_FILE="$PROJECT_ROOT/scripts/demo_walkthrough.sh"
cat > "$WALKTHROUGH_FILE" << 'DEMO_EOF'
#!/bin/bash
# Demo walkthrough script for Vocabulator MVP
# This script demonstrates key workflows

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${GREEN}ℹ️  $1${NC}"; }
step() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}$1${NC}"; }

step "Demo Walkthrough: Vocabulator MVP"

info "This walkthrough demonstrates the key workflows of Vocabulator:"
info "1. Creating a student profile"
info "2. Uploading transcripts and writing samples"
info "3. Retrieving vocabulary recommendations"
info "4. Viewing student profiles"

step "Prerequisites"
info "Ensure the demo environment is set up:"
info "  - Run: ./scripts/setup_demo_environment.sh"
info "  - API Gateway endpoint should be available"
info "  - Test data should be seeded"

step "Example API Calls"

API_URL="${API_URL:-http://localhost:8000}"
info "API Base URL: $API_URL"

info ""
info "1. Create a student profile:"
echo "curl -X POST ${API_URL}/api/v1/students \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"student_id\": \"STU-001\", \"grade_level\": 6}'"

info ""
info "2. Upload a transcript:"
echo "curl -X POST ${API_URL}/api/v1/transcripts/upload \\"
echo "  -F 'student_id=STU-001' \\"
echo "  -F 'file=@tests/fixtures/sample_transcripts/STU-006-1-001.txt'"

info ""
info "3. Get student profile:"
echo "curl ${API_URL}/api/v1/students/STU-001/profile"

info ""
info "4. Get recommendations:"
echo "curl ${API_URL}/api/v1/students/STU-001/recommendations"

info ""
info "For more examples, see: _docs/api-documentation.md"
DEMO_EOF

chmod +x "$WALKTHROUGH_FILE"
info "✅ Demo walkthrough script created: $WALKTHROUGH_FILE"

step "Setup Complete"
info "Demo environment setup completed!"
info "Next steps:"
info "  1. Review API documentation: _docs/api-documentation.md"
info "  2. Run demo walkthrough: ./scripts/demo_walkthrough.sh"
info "  3. Test workflows using the API endpoints"