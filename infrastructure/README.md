# Infrastructure Documentation

This directory contains infrastructure-as-code templates and deployment scripts for the Vocabulator MVP.

## Directory Structure

```
infrastructure/
├── cloudformation/          # CloudFormation templates
│   ├── master-stack.yaml    # Master stack orchestrating all resources
│   ├── dynamodb-tables.yaml # DynamoDB tables
│   ├── s3-buckets.yaml     # S3 buckets
│   ├── iam-roles.yaml      # IAM roles and policies
│   ├── batch-resources.yaml # AWS Batch resources
│   ├── api-gateway-lambda.yaml # API Gateway + Lambda
│   └── cloudwatch-logs.yaml # CloudWatch Logs and alarms
├── docker/                  # Dockerfiles for containerized deployments
│   ├── Dockerfile.batch     # Batch processing container
│   └── Dockerfile.lambda    # Lambda deployment package builder
└── README.md               # This file
```

## Lambda Deployment

### Creating a Deployment Package

The Lambda deployment package includes the FastAPI application and all dependencies.

#### Option 1: Using the Packaging Script (Recommended)

```bash
# Create the deployment package
./scripts/package-lambda.sh

# This creates: vocabulator-lambda.zip
```

#### Option 2: Using Docker

```bash
# Build Lambda package using Docker (matches Lambda runtime)
docker build -f infrastructure/docker/Dockerfile.lambda -t vocabulator-lambda .
docker run --rm -v $(pwd):/output vocabulator-lambda \
  zip -r /output/vocabulator-lambda.zip /var/task/*
```

### Uploading to S3

```bash
# Upload package to S3
./scripts/upload-lambda.sh <s3-bucket> [s3-key] [region]

# Example:
./scripts/upload-lambda.sh my-lambda-bucket vocabulator-api.zip us-east-1
```

### Manual Upload

```bash
# Upload using AWS CLI
aws s3 cp vocabulator-lambda.zip s3://your-lambda-bucket/vocabulator-api.zip \
  --region us-east-1
```

### Updating Lambda Function

After uploading to S3, update the Lambda function:

```bash
# Option 1: Update via CloudFormation (recommended)
# Update the stack with new LambdaCodeS3Key parameter

# Option 2: Update directly via AWS CLI
aws lambda update-function-code \
  --function-name vocabulator-dev-api \
  --s3-bucket your-lambda-bucket \
  --s3-key vocabulator-api.zip
```

## Batch Deployment

### Building Batch Container Image

```bash
# Build Docker image
docker build -f infrastructure/docker/Dockerfile.batch -t vocabulator-batch .

# Tag for ECR
docker tag vocabulator-batch:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest
```

### Updating Batch Job Definition

After pushing a new image, update the CloudFormation stack with the new ECR image URI:

```bash
aws cloudformation update-stack \
  --stack-name vocabulator-dev \
  --use-previous-template \
  --parameters \
    ParameterKey=EcrImageUri,ParameterValue=123456789012.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest
```

## CloudFormation Deployment

See [cloudformation/README.md](cloudformation/README.md) for detailed CloudFormation deployment instructions.

## Package Size Considerations

Lambda has the following limits:
- **Compressed**: 50 MB
- **Uncompressed**: 250 MB

If your package exceeds these limits:
1. Use Lambda Layers for large dependencies
2. Remove unnecessary files from the package
3. Consider using container images (up to 10 GB)

## Troubleshooting

### Package Too Large

If the Lambda package exceeds size limits:

```bash
# Check package size
du -sh vocabulator-lambda.zip
du -sh .lambda-package/

# Remove unnecessary dependencies
# Edit requirements.txt to remove unused packages
```

### Import Errors in Lambda

If Lambda fails with import errors:

1. Verify all dependencies are in requirements.txt
2. Check that package includes all Python files
3. Ensure PYTHONPATH is set correctly (handled by lambda_handler.py)

### Cold Start Performance

To reduce cold start times:

1. Use Lambda Provisioned Concurrency
2. Minimize package size
3. Initialize clients outside handler function (already done in dependencies.py)

## Security Notes

- Never commit `.lambda-package/` or `*.zip` files to git
- Store deployment packages in S3 with versioning enabled
- Use IAM roles for Lambda execution (not access keys)
- Rotate secrets regularly (use AWS Secrets Manager)
