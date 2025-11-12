#!/bin/bash
# Upload Lambda deployment package to S3
# Usage: ./scripts/upload-lambda.sh <s3-bucket> [s3-key] [region]

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ZIP_FILE="$PROJECT_ROOT/vocabulator-lambda.zip"

# Check if package exists
if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ Error: Lambda package not found: $ZIP_FILE"
    echo "   Run './scripts/package-lambda.sh' first to create the package"
    exit 1
fi

# Parse arguments
S3_BUCKET="${1:-}"
S3_KEY="${2:-vocabulator-api.zip}"
AWS_REGION="${3:-us-east-1}"

if [ -z "$S3_BUCKET" ]; then
    echo "❌ Error: S3 bucket name required"
    echo "Usage: $0 <s3-bucket> [s3-key] [region]"
    echo "Example: $0 my-lambda-bucket vocabulator-api.zip us-east-1"
    exit 1
fi

echo "📤 Uploading Lambda deployment package to S3"
echo "============================================="
echo "Bucket: $S3_BUCKET"
echo "Key: $S3_KEY"
echo "Region: $AWS_REGION"
echo ""

# Upload to S3
echo "⬆️  Uploading package..."
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY" \
    --region "$AWS_REGION" \
    --metadata "package-version=$(date +%Y%m%d-%H%M%S),source=vocabulator"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Package uploaded successfully!"
    echo "📦 S3 URI: s3://$S3_BUCKET/$S3_KEY"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Update CloudFormation stack with LambdaCodeS3Key=$S3_KEY"
    echo "   2. Or update Lambda function code:"
    echo "      aws lambda update-function-code \\"
    echo "        --function-name vocabulator-dev-api \\"
    echo "        --s3-bucket $S3_BUCKET \\"
    echo "        --s3-key $S3_KEY"
else
    echo "❌ Error: Failed to upload package"
    exit 1
fi

