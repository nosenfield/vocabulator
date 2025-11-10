# Infrastructure (`infrastructure/`)

This directory contains Infrastructure as Code (IaC) templates and deployment configurations for the Vocabulator MVP.

## Directory Structure

- **`cloudformation/`** - AWS CloudFormation templates
  - `api-gateway.yaml` - API Gateway configuration
  - `lambda-functions.yaml` - Lambda function definitions
  - `batch-processing.yaml` - AWS Batch compute environment
  - `storage.yaml` - DynamoDB tables and S3 buckets
  - `iam-roles.yaml` - IAM roles and policies
- **`docker/`** - Docker configurations
  - `Dockerfile.batch` - Batch processing container
  - `Dockerfile.lambda` - Lambda deployment package

## Deployment

See deployment documentation in `_docs/` for detailed instructions.

## Local Development

For local development, use LocalStack to emulate AWS services:

```bash
# Start LocalStack
docker-compose up -d localstack

# Verify services
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Infrastructure Principles

- **Serverless-First**: Use managed AWS services (Lambda, Fargate, DynamoDB, S3)
- **Least Privilege**: IAM roles with minimal required permissions
- **Cost-Conscious**: On-demand billing, auto-scaling
- **Infrastructure as Code**: All infrastructure defined in CloudFormation

## Related Documentation

- `_docs/architecture.md` - System architecture
- `_docs/best-practices/aws-services.md` - AWS service patterns

