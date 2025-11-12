# Deployment Guide

This guide provides step-by-step instructions for deploying the Vocabulator MVP to AWS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Deployment Process](#deployment-process)
4. [Environment-Specific Configuration](#environment-specific-configuration)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **AWS CLI** (v2.x recommended)
  ```bash
  aws --version
  ```
- **Docker** (for building Batch container images)
  ```bash
  docker --version
  ```
- **Python 3.11+** (for running deployment scripts)
- **Git** (for cloning the repository)

### AWS Account Setup

1. **AWS Account**: Access to an AWS account with appropriate permissions
2. **IAM Permissions**: Your AWS credentials must have permissions for:
   - CloudFormation (create/update/delete stacks)
   - S3 (create buckets, upload files)
   - Lambda (create/update functions)
   - API Gateway (create/update APIs)
   - DynamoDB (create tables)
   - IAM (create roles and policies)
   - CloudWatch (create log groups and alarms)
   - Batch (if deploying Batch resources)
   - ECR (if deploying Batch resources)

   **Sample IAM Policy** (minimum required permissions):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "cloudformation:*",
           "s3:*",
           "lambda:*",
           "apigateway:*",
           "dynamodb:*",
           "iam:CreateRole",
           "iam:CreatePolicy",
           "iam:AttachRolePolicy",
           "iam:PutRolePolicy",
           "iam:PassRole",
           "logs:*",
           "cloudwatch:*",
           "batch:*",
           "ecr:*"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
   
   **⚠️ SECURITY WARNING**: This example policy uses wildcards (`"Resource": "*"`) for simplicity and demonstration purposes. 
   **DO NOT use this policy in production**. For production deployments, scope permissions to specific resources 
   (e.g., specific S3 buckets, DynamoDB tables, Lambda functions) following the least privilege principle. 
   Consider using AWS managed policies or creating scoped custom policies based on your specific needs.

3. **AWS CLI Configuration**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Enter default region (e.g., us-east-1)
   # Enter default output format (json)
   ```

### Network Configuration (for Batch/Fargate)

If deploying Batch resources, you need:

1. **VPC**: A VPC with at least 2 subnets in different availability zones
2. **Subnets**: Subnet IDs (comma-separated, e.g., `subnet-12345,subnet-67890`)
3. **Security Group**: Security group ID that allows outbound HTTPS traffic

### Optional Resources

- **ECR Repository**: For Batch container images (create if deploying Batch)
- **SNS Topic**: For alarm notifications (can be created automatically)

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vocabulator
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Create S3 Buckets

Create buckets for:
- CloudFormation templates
- Lambda deployment packages
- (Optional) ECR repository for Batch images

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create templates bucket
aws s3 mb s3://vocabulator-cloudformation-templates-${AWS_ACCOUNT_ID} --region us-east-1

# Create Lambda bucket (environment-specific)
aws s3 mb s3://vocabulator-development-${AWS_ACCOUNT_ID}-lambda --region us-east-1
```

### 4. Upload CloudFormation Templates

CloudFormation nested stacks require templates to be in S3:

```bash
# Upload all templates
./scripts/upload-templates.sh

# Or specify bucket and region
./scripts/upload-templates.sh my-templates-bucket us-east-1
```

### 5. Build and Upload Lambda Package

```bash
# Build Lambda deployment package
./scripts/package-lambda.sh

# Upload to S3
./scripts/upload-lambda.sh vocabulator-development-<account-id>-lambda vocabulator-api.zip us-east-1
```

### 6. (Optional) Build and Push Batch Container Image

If deploying Batch resources:

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository (if it doesn't exist)
aws ecr create-repository \
  --repository-name vocabulator-batch \
  --region us-east-1

# Build and push image
docker build -f infrastructure/docker/Dockerfile.batch -t vocabulator-batch .
docker tag vocabulator-batch:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest
```

## Deployment Process

### Automated Deployment (Recommended)

Use the deployment script for automated deployment:

```bash
# Deploy to development
./scripts/deploy-infrastructure.sh development

# Deploy to staging
./scripts/deploy-infrastructure.sh staging

# Deploy to production
./scripts/deploy-infrastructure.sh production
```

### Environment Variables

You can customize deployment using environment variables:

```bash
# Required
export AWS_REGION=us-east-1
export TEMPLATES_BUCKET=vocabulator-cloudformation-templates-<account-id>
export LAMBDA_BUCKET=vocabulator-<env>-<account-id>-lambda

# Optional (for Batch)
export ECR_IMAGE_URI=<account-id>.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest
export SUBNET_IDS=subnet-12345,subnet-67890
export SECURITY_GROUP_ID=sg-12345

# Optional (for monitoring)
export EMAIL_ADDRESS=alerts@example.com
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:<account-id>:vocabulator-alarms
```

### Manual Deployment

If you prefer manual deployment:

```bash
# 1. Upload templates (if not already done)
./scripts/upload-templates.sh

# 2. Create stack
aws cloudformation create-stack \
  --stack-name vocabulator-development \
  --template-url https://s3.us-east-1.amazonaws.com/<templates-bucket>/master-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=TemplatesBucket,ParameterValue=<templates-bucket> \
    ParameterKey=LambdaCodeS3Bucket,ParameterValue=<lambda-bucket> \
    ParameterKey=LambdaCodeS3Key,ParameterValue=vocabulator-api.zip \
    ParameterKey=EcrImageUri,ParameterValue=<ecr-image-uri> \
    ParameterKey=SubnetIds,ParameterValue=subnet-12345,subnet-67890 \
    ParameterKey=SecurityGroupId,ParameterValue=sg-12345 \
    ParameterKey=EmailAddress,ParameterValue=alerts@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# 3. Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name vocabulator-development \
  --region us-east-1

# 4. Get stack outputs
aws cloudformation describe-stacks \
  --stack-name vocabulator-development \
  --region us-east-1 \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Environment-Specific Configuration

### Development

- **Purpose**: Local development and testing
- **Cost**: Minimal (use free tier where possible)
- **Monitoring**: Basic alarms only
- **Deployment**: Frequent, automated via CI/CD

```bash
./scripts/deploy-infrastructure.sh development
```

### Staging

- **Purpose**: Pre-production testing
- **Cost**: Similar to production (for accurate testing)
- **Monitoring**: Full monitoring and alerting
- **Deployment**: Automated on merge to main

```bash
./scripts/deploy-infrastructure.sh staging
```

### Production

- **Purpose**: Live production environment
- **Cost**: Optimized for cost efficiency
- **Monitoring**: Full monitoring with SNS notifications
- **Deployment**: Manual approval required

```bash
# Production deployments require manual approval
./scripts/deploy-infrastructure.sh production
```

## Post-Deployment Verification

### 1. Verify Stack Creation

```bash
aws cloudformation describe-stacks \
  --stack-name vocabulator-<environment> \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'
```

Expected output: `"CREATE_COMPLETE"`

### 2. Get API Endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name vocabulator-<environment> \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

### 3. Test API Health Endpoint

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name vocabulator-<environment> \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text)

curl "${API_URL}/health"
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

### 4. Verify Lambda Function

```bash
aws lambda get-function \
  --function-name vocabulator-<environment>-api \
  --region us-east-1 \
  --query 'Configuration.[FunctionName,LastModified,Runtime,MemorySize,Timeout]' \
  --output table
```

### 5. Verify DynamoDB Tables

```bash
aws dynamodb list-tables \
  --region us-east-1 \
  --query 'TableNames[?contains(@, `vocabulator-<environment>`)]' \
  --output table
```

### 6. Verify S3 Buckets

```bash
aws s3 ls | grep vocabulator-<environment>
```

### 7. Verify CloudWatch Dashboard

1. Open AWS Console → CloudWatch → Dashboards
2. Find dashboard: `Vocabulator-<environment>-Dashboard`
3. Verify metrics are displaying

### 8. Verify Alarms (if SNS configured)

1. Open AWS Console → CloudWatch → Alarms
2. Filter by: `vocabulator-<environment>-*`
3. Verify alarms are in `OK` state

## Updating Deployment

### Update Lambda Code

```bash
# 1. Build new package
./scripts/package-lambda.sh

# 2. Upload to S3
./scripts/upload-lambda.sh <lambda-bucket> vocabulator-api.zip us-east-1

# 3. Update stack
./scripts/deploy-infrastructure.sh <environment> update
```

### Update Infrastructure

```bash
# 1. Update templates in code
# 2. Upload templates
./scripts/upload-templates.sh

# 3. Update stack
./scripts/deploy-infrastructure.sh <environment> update
```

### Update Batch Image

```bash
# 1. Build new image
docker build -f infrastructure/docker/Dockerfile.batch -t vocabulator-batch .
docker tag vocabulator-batch:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/vocabulator-batch:latest

# 2. Update stack with new image URI
aws cloudformation update-stack \
  --stack-name vocabulator-<environment> \
  --use-previous-template \
  --parameters \
    ParameterKey=EcrImageUri,ParameterValue=<new-image-uri> \
    ... # other parameters
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## Deleting Deployment

⚠️ **Warning**: This will delete all resources in the stack, including data!

```bash
# Delete stack
./scripts/deploy-infrastructure.sh <environment> delete
```

## Troubleshooting

### Stack Creation Fails

1. **Check CloudFormation Events**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name vocabulator-<environment> \
     --region us-east-1 \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]' \
     --output table
   ```

2. **Common Issues**:
   - **S3 bucket doesn't exist**: Create bucket before deployment
   - **IAM permissions insufficient**: Check IAM policies
   - **Template URL incorrect**: Verify templates are uploaded to S3
   - **Parameter validation failed**: Check parameter values

### Lambda Function Errors

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/vocabulator-<environment>-api \
     --follow \
     --region us-east-1
   ```

2. **Common Issues**:
   - **Import errors**: Verify all dependencies in requirements.txt
   - **Environment variables missing**: Check Lambda configuration
   - **Timeout errors**: Increase Lambda timeout in CloudFormation

### API Gateway Errors

1. **Check API Gateway Logs**:
   ```bash
   aws apigateway get-rest-apis \
     --region us-east-1 \
     --query 'items[?name==`vocabulator-<environment>-api`]'
   ```

2. **Test API Endpoint**:
   ```bash
   curl -v https://<api-id>.execute-api.us-east-1.amazonaws.com/health
   ```

### Batch Job Failures

1. **Check Batch Job Logs**:
   ```bash
   aws batch describe-jobs \
     --jobs <job-id> \
     --region us-east-1
   ```

2. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/batch/vocabulator-<environment> \
     --follow \
     --region us-east-1
   ```

### Cost Alarms Triggering

1. **Check CloudWatch Billing Metrics**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Billing \
     --metric-name EstimatedCharges \
     --dimensions Name=Currency,Value=USD \
     --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 86400 \
     --statistics Maximum \
     --region us-east-1
   ```

2. **Review Resource Usage**:
   - Check DynamoDB read/write capacity
   - Review Lambda invocations and duration
   - Check S3 storage and requests
   - Review Batch job execution time

## Security Checklist

Before deploying to production:

- [ ] Secrets stored in AWS Secrets Manager (not environment variables)
- [ ] API Gateway authentication configured
- [ ] VPC endpoints configured (if using VPC)
- [ ] CloudWatch alarms configured with SNS notifications
- [ ] IAM roles follow least privilege principle
- [ ] S3 buckets have encryption enabled
- [ ] DynamoDB tables have encryption at rest
- [ ] CloudWatch log retention configured
- [ ] Cost alarms configured
- [ ] Backup and disaster recovery plan documented

## Additional Resources

- [Infrastructure README](../infrastructure/README.md)
- [CloudFormation Templates README](../infrastructure/cloudformation/README.md)
- [Architecture Documentation](architecture.md)
- [Best Practices](best-practices.md)

