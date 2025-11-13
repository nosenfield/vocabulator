# GitHub Actions Workflows

This directory contains CI/CD workflows for the Vocabulator project.

## ⚠️ Prerequisites

Before using these workflows, ensure the following are set up:

1. **Lambda Packaging Script**: `scripts/package-lambda.sh` must exist
2. **CloudFormation Templates**: Templates in `infrastructure/cloudformation/` must be created
3. **ECR Repository**: Create `vocabulator-batch` repository in ECR
4. **S3 Buckets**: Create buckets for Lambda packages and CloudFormation templates (staging + production)
5. **VPC Configuration**: Subnets and security groups configured for Batch/Fargate
6. **GitHub Secrets**: All required secrets configured (see below)

**Status**: These workflows are ready for use. Prerequisites (Lambda packaging script and CloudFormation templates) have been created as part of Phase 6 tasks 6.1 and 6.2. You still need to configure AWS resources (ECR, S3 buckets, VPC) and GitHub secrets before running deployments.

## Workflows

### test.yml

Runs on every push and pull request to `main` or `develop` branches.

**Jobs:**
1. **test** - Runs pytest with coverage (60% threshold)
   - Tests on Python 3.11 and 3.12
   - Uploads coverage reports to Codecov
   - Generates HTML coverage reports

2. **lint** - Code quality checks
   - Black (formatting check)
   - Ruff (linting)
   - MyPy (type checking, non-blocking)

3. **security** - Security scanning
   - Safety (dependency vulnerability check)
   - Bandit (security linter)

### deploy.yml

Runs on pushes to `main` branch or manual workflow dispatch.

**Jobs:**
1. **build-lambda** - Creates Lambda deployment package
   - Packages FastAPI app with dependencies
   - Uploads as artifact for deployment jobs

2. **build-batch-image** - Builds and pushes Docker image to ECR
   - Builds batch processing container
   - Tags with commit SHA and `latest`
   - Pushes to Amazon ECR

3. **deploy-staging** - Deploys to staging environment
   - Uploads Lambda package to S3
   - Uploads CloudFormation templates to S3
   - Deploys CloudFormation stack
   - Runs smoke tests

4. **deploy-production** - Deploys to production environment
   - Requires manual approval (GitHub environment protection)
   - Uploads Lambda package to S3
   - Deploys CloudFormation stack
   - Runs integration tests
   - Monitors for errors

## Required Secrets

Configure these secrets in GitHub repository settings:

### AWS Credentials
- `AWS_ACCESS_KEY_ID` - AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for deployment

### Staging Environment
- `STAGING_LAMBDA_BUCKET` - S3 bucket for Lambda packages
- `STAGING_TEMPLATES_BUCKET` - S3 bucket for CloudFormation templates
- `STAGING_SUBNET_IDS` - Comma-separated subnet IDs (e.g., "subnet-123,subnet-456")
- `STAGING_SECURITY_GROUP_ID` - Security group ID for Fargate tasks

### Production Environment
- `PRODUCTION_LAMBDA_BUCKET` - S3 bucket for Lambda packages
- `PRODUCTION_TEMPLATES_BUCKET` - S3 bucket for CloudFormation templates
- `PRODUCTION_SUBNET_IDS` - Comma-separated subnet IDs
- `PRODUCTION_SECURITY_GROUP_ID` - Security group ID for Fargate tasks

### Additional Secrets (Optional)
- `OPENAI_API_KEY` - OpenAI API key (if not using Secrets Manager)
- `ECR_REPOSITORY` - ECR repository name (defaults to `vocabulator-batch`)

## Environment Protection

Configure GitHub environments (`staging` and `production`) with:
- **Required reviewers** for production deployments
- **Deployment branches** (only `main` for production)
- **Wait timer** (optional, e.g., 5 minutes for production)

## Manual Deployment

To manually trigger a deployment:

1. Go to Actions → Deploy workflow
2. Click "Run workflow"
3. Select environment (staging or production)
4. Click "Run workflow"

## Troubleshooting

### Tests Fail

- Check test output in Actions tab
- Verify all dependencies are in `requirements-dev.txt`
- Check Python version compatibility

### Deployment Fails

- Verify AWS credentials are correct
- Check that S3 buckets exist and are accessible
- Verify CloudFormation templates are valid
- Check CloudFormation stack events for specific errors

### Lambda Package Too Large

- Review package size in build-lambda job output
- Consider using Lambda Layers for large dependencies
- Remove unnecessary files from package

### ECR Push Fails

- Verify ECR repository exists
- Check AWS credentials have ECR permissions
- Verify repository name matches workflow configuration

