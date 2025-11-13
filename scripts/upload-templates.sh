#!/bin/bash
# Upload CloudFormation templates to S3
# Usage: ./scripts/upload-templates.sh [bucket-name] [region]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infrastructure/cloudformation"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Parse arguments
BUCKET="${1:-}"
REGION="${2:-${AWS_REGION:-us-east-1}}"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first." >&2
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured. Run 'aws configure' first." >&2
    exit 1
fi

# Get AWS account ID and set default bucket
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [[ -z "$BUCKET" ]]; then
    BUCKET="vocabulator-cloudformation-templates-${AWS_ACCOUNT_ID}"
    warn "Bucket not specified, using default: $BUCKET"
fi

info "Uploading CloudFormation templates to S3"
info "Bucket: $BUCKET"
info "Region: $REGION"

# Create bucket if it doesn't exist
if ! aws s3 ls "s3://${BUCKET}" &> /dev/null; then
    info "Creating bucket: $BUCKET"
    if [[ "$REGION" == "us-east-1" ]]; then
        # us-east-1 doesn't require LocationConstraint
        aws s3 mb "s3://${BUCKET}" --region "$REGION"
    else
        aws s3 mb "s3://${BUCKET}" --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET" \
        --versioning-configuration Status=Enabled \
        --region "$REGION"
    
    info "Bucket created with versioning enabled"
fi

# Validate templates before upload
info "Validating CloudFormation templates..."
VALIDATION_ERRORS=0
for template in "$INFRA_DIR"/*.yaml; do
    if [[ -f "$template" ]]; then
        template_name=$(basename "$template")
        if ! aws cloudformation validate-template \
            --template-body "file://${template}" \
            --region "$REGION" &> /dev/null; then
            warn "Template validation failed: $template_name"
            VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
        else
            info "✓ Validated: $template_name"
        fi
    fi
done

if [[ $VALIDATION_ERRORS -gt 0 ]]; then
    warn "${VALIDATION_ERRORS} template(s) failed validation. Check output above for details."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Upload cancelled. Please fix validation errors and try again."
        exit 1
    fi
fi

# Upload templates
info "Syncing templates to S3..."
aws s3 sync "$INFRA_DIR" "s3://${BUCKET}/" \
    --exclude "*" \
    --include "*.yaml" \
    --region "$REGION" \
    --delete

info "Templates uploaded successfully!"
info "Template URLs:"
echo "  Master Stack: https://s3.${REGION}.amazonaws.com/${BUCKET}/master-stack.yaml"
echo "  DynamoDB: https://s3.${REGION}.amazonaws.com/${BUCKET}/dynamodb-tables.yaml"
echo "  S3 Buckets: https://s3.${REGION}.amazonaws.com/${BUCKET}/s3-buckets.yaml"
echo "  IAM Roles: https://s3.${REGION}.amazonaws.com/${BUCKET}/iam-roles.yaml"
echo "  Batch: https://s3.${REGION}.amazonaws.com/${BUCKET}/batch-resources.yaml"
echo "  API Gateway: https://s3.${REGION}.amazonaws.com/${BUCKET}/api-gateway-lambda.yaml"
echo "  CloudWatch Logs: https://s3.${REGION}.amazonaws.com/${BUCKET}/cloudwatch-logs.yaml"
echo "  CloudWatch Dashboard: https://s3.${REGION}.amazonaws.com/${BUCKET}/cloudwatch-dashboard.yaml"
echo "  SNS Topics: https://s3.${REGION}.amazonaws.com/${BUCKET}/sns-topics.yaml"

