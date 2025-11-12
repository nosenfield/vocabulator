#!/bin/bash
# Package FastAPI application for AWS Lambda deployment
# Creates a deployment-ready zip file with all dependencies

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_DIR="$PROJECT_ROOT/.lambda-package"
ZIP_FILE="$PROJECT_ROOT/vocabulator-lambda.zip"

echo "📦 Packaging Vocabulator Lambda deployment package"
echo "=================================================="

# Clean up previous builds
if [ -d "$PACKAGE_DIR" ]; then
    echo "🧹 Cleaning up previous build..."
    rm -rf "$PACKAGE_DIR"
fi

if [ -f "$ZIP_FILE" ]; then
    echo "🧹 Removing old zip file..."
    rm -f "$ZIP_FILE"
fi

# Create package directory
echo "📁 Creating package directory..."
mkdir -p "$PACKAGE_DIR"

# Copy application code
echo "📋 Copying application code..."
cp -r "$PROJECT_ROOT/src" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/lambda_handler.py" "$PACKAGE_DIR/"
cp "$PROJECT_ROOT/pyproject.toml" "$PACKAGE_DIR/" 2>/dev/null || true

# Create __init__.py in root if it doesn't exist (for Python path)
if [ ! -f "$PACKAGE_DIR/__init__.py" ]; then
    touch "$PACKAGE_DIR/__init__.py"
fi

# Install dependencies into package directory
echo "📥 Installing dependencies..."
cd "$PACKAGE_DIR"

# Install dependencies with their dependencies
pip install --target . --no-cache-dir -r "$PROJECT_ROOT/requirements.txt"

# Remove unnecessary files to reduce package size
echo "🧹 Removing unnecessary files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
# Note: Keeping .so files as some packages (e.g., cryptography) require them
# Lambda runtime includes common libraries but not all package-specific ones
find . -type f -name "*.a" -delete 2>/dev/null || true
find . -type f -name "*.h" -delete 2>/dev/null || true

# Remove test files and documentation
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.md" -delete 2>/dev/null || true
find . -type f -name "*.txt" -not -name "requirements.txt" -delete 2>/dev/null || true

# Create zip file
echo "📦 Creating zip file..."
cd "$PACKAGE_DIR"
zip -r "$ZIP_FILE" . -q
cd "$PROJECT_ROOT"

# Calculate package size
PACKAGE_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "✅ Package created: $ZIP_FILE"
echo "📊 Package size: $PACKAGE_SIZE"

# Check if package exceeds Lambda limits (50MB compressed, 250MB uncompressed)
UNCOMPRESSED_SIZE=$(du -sm "$PACKAGE_DIR" | cut -f1)
COMPRESSED_SIZE=$(du -sm "$ZIP_FILE" | cut -f1)

if [ "$COMPRESSED_SIZE" -gt 50 ]; then
    echo "⚠️  WARNING: Package exceeds Lambda's 50MB compressed limit!"
    echo "   Consider using Lambda Layers or reducing dependencies"
fi

if [ "$UNCOMPRESSED_SIZE" -gt 250 ]; then
    echo "⚠️  WARNING: Package exceeds Lambda's 250MB uncompressed limit!"
    echo "   Consider using Lambda Layers or reducing dependencies"
fi

# Clean up package directory (keep zip file)
echo "🧹 Cleaning up temporary files..."
rm -rf "$PACKAGE_DIR"

echo ""
echo "✅ Lambda deployment package ready!"
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

