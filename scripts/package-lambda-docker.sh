#!/bin/bash
# Package FastAPI application for AWS Lambda deployment using Docker
# Creates a deployment-ready zip file with Linux-compatible dependencies

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ZIP_FILE="$PROJECT_ROOT/vocabulator-lambda.zip"

echo "📦 Packaging Vocabulator Lambda deployment package (Docker)"
echo "=========================================================="

# Clean up previous builds
if [ -f "$ZIP_FILE" ]; then
    echo "🧹 Removing old zip file..."
    rm -f "$ZIP_FILE"
fi

# Use Docker to build the package in a Linux x86_64 environment (Lambda's architecture)
echo "🐳 Building Lambda package in Docker container (x86_64)..."
docker run --rm \
    --platform linux/amd64 \
    --entrypoint="" \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace \
    public.ecr.aws/lambda/python:3.11 \
    /bin/bash -c "
        set -e
        PACKAGE_DIR=/tmp/lambda-package
        rm -rf \$PACKAGE_DIR
        mkdir -p \$PACKAGE_DIR
        
        # Copy application code
        echo '📋 Copying application code...'
        cp -r src/ \$PACKAGE_DIR/
        cp -r scripts/ \$PACKAGE_DIR/ 2>/dev/null || true
        cp lambda_handler.py \$PACKAGE_DIR/
        cp pyproject.toml \$PACKAGE_DIR/ 2>/dev/null || true
        
        # Create __init__.py in root if it doesn't exist
        if [ ! -f \$PACKAGE_DIR/__init__.py ]; then
            touch \$PACKAGE_DIR/__init__.py
        fi
        
        # Install dependencies into package directory
        echo '📥 Installing dependencies...'
        cd \$PACKAGE_DIR
        pip install --target . --no-cache-dir -r /workspace/requirements.txt
        
        # Remove unnecessary files to reduce package size
        echo '🧹 Removing unnecessary files...'
        find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name '*.dist-info' -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name '*.pyc' -delete 2>/dev/null || true
        find . -type f -name '*.pyo' -delete 2>/dev/null || true
        find . -type f -name '*.pyd' -delete 2>/dev/null || true
        find . -type f -name '*.a' -delete 2>/dev/null || true
        find . -type f -name '*.h' -delete 2>/dev/null || true
        find . -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name 'test' -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name '*.md' -delete 2>/dev/null || true
        find . -type f -name '*.txt' -not -name 'requirements.txt' -delete 2>/dev/null || true
        
        # Install zip if not available
        if ! command -v zip &> /dev/null; then
            echo '📦 Installing zip...'
            yum install -y zip 2>/dev/null || apt-get update && apt-get install -y zip 2>/dev/null || true
        fi
        
        # Create zip file
        echo '📦 Creating zip file...'
        cd \$PACKAGE_DIR
        zip -r /workspace/vocabulator-lambda.zip . -q || python3 -m zipfile -c /workspace/vocabulator-lambda.zip .
        
        echo '✅ Package created successfully'
    "

# Calculate package size
PACKAGE_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "✅ Package created: $ZIP_FILE"
echo "📊 Package size: $PACKAGE_SIZE"

# Check if package exceeds Lambda limits
UNCOMPRESSED_SIZE=$(unzip -l "$ZIP_FILE" | tail -1 | awk '{print $1}' | awk '{print int($1/1024/1024)}')
COMPRESSED_SIZE=$(du -sm "$ZIP_FILE" | cut -f1)

if [ "$COMPRESSED_SIZE" -gt 50 ]; then
    echo "⚠️  WARNING: Package exceeds Lambda's 50MB compressed limit!"
    echo "   Consider using Lambda Layers or reducing dependencies"
fi

if [ "$UNCOMPRESSED_SIZE" -gt 250 ]; then
    echo "⚠️  WARNING: Package exceeds Lambda's 250MB uncompressed limit!"
    echo "   Consider using Lambda Layers or reducing dependencies"
fi

echo ""
echo "✅ Lambda deployment package ready (Linux-compatible)!"
echo "📦 File: $ZIP_FILE"
echo ""
echo "💡 Next steps:"
echo "   1. Upload to S3:"
echo "      aws s3 cp $ZIP_FILE s3://your-lambda-bucket/vocabulator-api.zip"
echo ""
echo "   2. Update CloudFormation stack with new S3 key"
echo "   3. Or use AWS CLI to update Lambda function:"
echo "      aws lambda update-function-code \\"
echo "        --function-name vocabulator-dev-api \\"
echo "        --zip-file fileb://$ZIP_FILE"

