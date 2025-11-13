#!/bin/bash
# Deploy Vocabulator infrastructure using CloudFormation
# Usage: ./scripts/deploy-infrastructure.sh <environment> [action]
#   environment: development, staging, or production
#   action: create, update, delete (default: create)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infrastructure/cloudformation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Parse arguments
ENVIRONMENT="${1:-}"
ACTION="${2:-create}"

if [[ -z "$ENVIRONMENT" ]]; then
    error "Usage: $0 <environment> [action]
  environment: development, staging, or production
  action: create, update, delete (default: create)"
fi

if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    error "Environment must be one of: development, staging, production"
fi

if [[ ! "$ACTION" =~ ^(create|update|delete)$ ]]; then
    error "Action must be one of: create, update, delete"
fi

# Configuration
STACK_NAME="vocabulator-${ENVIRONMENT}"
REGION="${AWS_REGION:-us-east-1}"
TEMPLATES_BUCKET="${TEMPLATES_BUCKET:-}"
LAMBDA_BUCKET="${LAMBDA_BUCKET:-}"
LAMBDA_KEY="${LAMBDA_KEY:-vocabulator-api.zip}"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    error "AWS CLI is not installed. Please install it first."
fi

if ! aws sts get-caller-identity &> /dev/null; then
    error "AWS credentials not configured. Run 'aws configure' first."
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
info "AWS Account ID: $AWS_ACCOUNT_ID"
info "Region: $REGION"
info "Stack Name: $STACK_NAME"

# Set default templates bucket if not provided
if [[ -z "$TEMPLATES_BUCKET" ]]; then
    TEMPLATES_BUCKET="vocabulator-cloudformation-templates-${AWS_ACCOUNT_ID}"
    warn "TEMPLATES_BUCKET not set, using default: $TEMPLATES_BUCKET"
fi

# Set default Lambda bucket if not provided
if [[ -z "$LAMBDA_BUCKET" ]]; then
    LAMBDA_BUCKET="vocabulator-${ENVIRONMENT}-${AWS_ACCOUNT_ID}-lambda"
    warn "LAMBDA_BUCKET not set, using default: $LAMBDA_BUCKET"
fi

# Upload templates to S3 (required for nested stacks)
info "Uploading CloudFormation templates to S3..."
if ! aws s3 ls "s3://${TEMPLATES_BUCKET}" &> /dev/null; then
    info "Creating templates bucket: $TEMPLATES_BUCKET"
    if [[ "$REGION" == "us-east-1" ]]; then
        # us-east-1 doesn't require LocationConstraint
        aws s3 mb "s3://${TEMPLATES_BUCKET}" --region "$REGION" || true
    else
        aws s3 mb "s3://${TEMPLATES_BUCKET}" --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION" || true
    fi
fi

aws s3 sync "$INFRA_DIR" "s3://${TEMPLATES_BUCKET}/" \
    --exclude "*" \
    --include "*.yaml" \
    --region "$REGION" \
    --delete

info "Templates uploaded successfully"

# Check if Lambda package exists
if [[ "$ACTION" != "delete" ]]; then
    if ! aws s3 ls "s3://${LAMBDA_BUCKET}/${LAMBDA_KEY}" &> /dev/null; then
        warn "Lambda package not found at s3://${LAMBDA_BUCKET}/${LAMBDA_KEY}"
        warn "Run './scripts/package-lambda.sh' and './scripts/upload-lambda.sh' first"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Prepare parameters
PARAMETERS=(
    "ParameterKey=Environment,ParameterValue=${ENVIRONMENT}"
    "ParameterKey=TemplatesBucket,ParameterValue=${TEMPLATES_BUCKET}"
    "ParameterKey=LambdaCodeS3Bucket,ParameterValue=${LAMBDA_BUCKET}"
    "ParameterKey=LambdaCodeS3Key,ParameterValue=${LAMBDA_KEY}"
)

# Add optional parameters if provided
if [[ -n "${ECR_IMAGE_URI:-}" ]]; then
    PARAMETERS+=("ParameterKey=EcrImageUri,ParameterValue=${ECR_IMAGE_URI}")
    if [[ -z "${SUBNET_IDS:-}" ]] || [[ -z "${SECURITY_GROUP_ID:-}" ]]; then
        error "ECR_IMAGE_URI provided but SUBNET_IDS and SECURITY_GROUP_ID are required for Batch"
    fi
    PARAMETERS+=("ParameterKey=SubnetIds,ParameterValue=${SUBNET_IDS}")
    PARAMETERS+=("ParameterKey=SecurityGroupId,ParameterValue=${SECURITY_GROUP_ID}")
fi

if [[ -n "${EMAIL_ADDRESS:-}" ]]; then
    PARAMETERS+=("ParameterKey=EmailAddress,ParameterValue=${EMAIL_ADDRESS}")
fi

if [[ -n "${SNS_TOPIC_ARN:-}" ]]; then
    PARAMETERS+=("ParameterKey=SnsTopicArn,ParameterValue=${SNS_TOPIC_ARN}")
fi

# Execute action
case "$ACTION" in
    create)
        info "Creating CloudFormation stack: $STACK_NAME"
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-url "https://s3.${REGION}.amazonaws.com/${TEMPLATES_BUCKET}/master-stack.yaml" \
            --parameters "${PARAMETERS[@]}" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION" \
            --tags \
                Key=Environment,Value="$ENVIRONMENT" \
                Key=Project,Value=Vocabulator
        
        info "Stack creation initiated. Waiting for completion..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        info "Stack created successfully!"
        
        # Display outputs
        info "Stack outputs:"
        aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output table
        ;;
    
    update)
        info "Updating CloudFormation stack: $STACK_NAME"
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-url "https://s3.${REGION}.amazonaws.com/${TEMPLATES_BUCKET}/master-stack.yaml" \
            --parameters "${PARAMETERS[@]}" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        info "Stack update initiated. Waiting for completion..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        info "Stack updated successfully!"
        
        # Display outputs
        info "Stack outputs:"
        aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs' \
            --output table
        ;;
    
    delete)
        warn "This will delete the entire stack: $STACK_NAME"
        warn "This action cannot be undone!"
        read -p "Are you sure? (yes/NO) " -r
        if [[ ! $REPLY == "yes" ]]; then
            info "Deletion cancelled"
            exit 0
        fi
        
        info "Deleting CloudFormation stack: $STACK_NAME"
        aws cloudformation delete-stack \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        info "Stack deletion initiated. Waiting for completion..."
        aws cloudformation wait stack-delete-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        info "Stack deleted successfully!"
        ;;
esac

info "Deployment complete!"

