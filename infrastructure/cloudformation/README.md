# CloudFormation Templates for Vocabulator MVP

This directory contains CloudFormation templates for deploying the Vocabulator infrastructure to AWS.

## Template Structure

The infrastructure is organized as nested stacks:

### Master Stack
- **master-stack.yaml** - Orchestrates all nested stacks in the correct dependency order

### Nested Stacks

1. **dynamodb-tables.yaml** - DynamoDB tables
   - StudentProfiles
   - VocabularyRecommendations
   - CommonCoreVocabulary

2. **s3-buckets.yaml** - S3 buckets
   - Data bucket (transcripts, writing samples)
   - Reports bucket (HTML reports)

3. **cloudwatch-logs.yaml** - CloudWatch Logs groups and alarms
   - API Lambda log group
   - Batch log group
   - Error rate alarms
   - Cost alarms

4. **iam-roles.yaml** - IAM roles and policies
   - Lambda execution role
   - Batch execution role
   - Batch task role

5. **batch-resources.yaml** - AWS Batch resources
   - Compute environment (Fargate Spot)
   - Job queue
   - Job definition

6. **api-gateway-lambda.yaml** - API Gateway and Lambda function
   - Lambda function for FastAPI application
   - API Gateway REST API
   - Lambda integration

## ⚠️ SECURITY WARNINGS - READ BEFORE DEPLOYMENT

**CRITICAL**: This infrastructure template does NOT include:
1. **Secrets Management**: `OPENAI_API_KEY` must be configured via AWS Secrets Manager (see TODO section)
2. **API Authentication**: API Gateway is currently open to public (no authentication configured)
3. **VPC Configuration**: Lambda and Batch tasks are not in a VPC (traffic goes through public internet)

**DO NOT DEPLOY TO PRODUCTION** without addressing these security concerns.

See "TODO" section below for implementation steps.

---

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. S3 bucket for Lambda deployment package
3. **S3 bucket for CloudFormation templates** (nested stacks require S3 URLs)
4. VPC with at least 2 subnets in different availability zones (for Batch/Fargate)
5. Security group for Fargate tasks (allows outbound HTTPS)
6. (Optional) ECR repository for Batch container image
7. (Optional) SNS topic for alarm notifications

### Upload Templates to S3

**IMPORTANT**: CloudFormation nested stacks require templates to be in S3, not local files.

```bash
# Create S3 bucket for templates (if it doesn't exist)
aws s3 mb s3://vocabulator-cloudformation-templates-<account-id> --region us-east-1

# Upload all templates
aws s3 sync . s3://vocabulator-cloudformation-templates-<account-id>/ \
  --exclude "*" \
  --include "*.yaml" \
  --region us-east-1

# Update master-stack.yaml TemplateURLs to use S3 URLs:
# TemplateURL: https://s3.amazonaws.com/vocabulator-cloudformation-templates-<account-id>/dynamodb-tables.yaml
```

### Parameters

The master stack requires the following parameters:

- **Environment**: `development`, `staging`, or `production`
- **LambdaCodeS3Bucket**: S3 bucket containing Lambda deployment package
- **LambdaCodeS3Key**: S3 key of Lambda deployment package
- **EcrImageUri** (optional): URI of ECR container image for batch jobs
- **SnsTopicArn** (optional): ARN of SNS topic for alarm notifications

### Deploy Command

```bash
aws cloudformation create-stack \
  --stack-name vocabulator-<environment> \
  --template-body file://master-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=LambdaCodeS3Bucket,ParameterValue=my-lambda-bucket \
    ParameterKey=LambdaCodeS3Key,ParameterValue=vocabulator-api.zip \
    ParameterKey=TemplatesBucket,ParameterValue=my-templates-bucket \
    ParameterKey=SubnetIds,ParameterValue=subnet-12345,subnet-67890 \
    ParameterKey=SecurityGroupId,ParameterValue=sg-12345 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Update Stack

```bash
aws cloudformation update-stack \
  --stack-name vocabulator-<environment> \
  --template-body file://master-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=LambdaCodeS3Bucket,ParameterValue=my-lambda-bucket \
    ParameterKey=LambdaCodeS3Key,ParameterValue=vocabulator-api.zip \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

## Stack Dependencies

The stacks are deployed in this order:

1. DynamoDB Stack (no dependencies)
2. S3 Stack (no dependencies)
3. CloudWatch Stack (no dependencies)
4. IAM Stack (depends on DynamoDB, S3, CloudWatch)
5. Batch Stack (depends on IAM, CloudWatch) - optional
6. API Stack (depends on DynamoDB, S3, IAM, CloudWatch, Batch)

## Outputs

The master stack outputs:

- **ApiGatewayUrl**: URL of the deployed API
- **DataBucketName**: Name of the data S3 bucket
- **ReportsBucketName**: Name of the reports S3 bucket
- **StudentProfilesTableName**: Name of the StudentProfiles table
- **VocabularyRecommendationsTableName**: Name of the VocabularyRecommendations table
- **CommonCoreVocabularyTableName**: Name of the CommonCoreVocabulary table
- **BatchJobQueueName**: Name of the Batch job queue (if Batch stack deployed)

## Environment Variables

The Lambda function requires these environment variables (set automatically by CloudFormation):

- `ENVIRONMENT`: Deployment environment
- `AWS_REGION`: AWS region
- `S3_BUCKET_NAME`: Data bucket name
- `REPORTS_BUCKET_NAME`: Reports bucket name
- `DYNAMODB_TABLE_PREFIX`: Table name prefix
- `STUDENT_PROFILES_TABLE_NAME`: StudentProfiles table name
- `VOCABULARY_RECOMMENDATIONS_TABLE_NAME`: VocabularyRecommendations table name
- `COMMON_CORE_VOCABULARY_TABLE_NAME`: CommonCoreVocabulary table name
- `BATCH_JOB_QUEUE`: Batch job queue name (if configured)
- `BATCH_JOB_DEFINITION`: Batch job definition name (if configured)
- `LOG_LEVEL`: Logging level (INFO)

**Note**: Secrets like `OPENAI_API_KEY` and `AWS_ACCESS_KEY_ID` should be stored in AWS Secrets Manager or Parameter Store and retrieved at runtime, not set as environment variables.

**TODO**: Add Secrets Manager integration:
1. Create AWS::SecretsManager::Secret resource in CloudFormation
2. Add IAM policy to Lambda role to read secrets
3. Update application code to retrieve secrets at runtime using boto3
4. Remove secrets from environment variables

**TODO**: Add API Gateway authentication:
1. Configure API keys or IAM authorization
2. Add usage plans with throttling (e.g., 1000 requests/second)
3. Document authentication requirements in API docs

## Cost Considerations

- DynamoDB: PAY_PER_REQUEST billing (auto-scaling)
- Lambda: Pay per invocation (1M free requests/month)
- API Gateway: Pay per API call (1M free requests/month)
- S3: Pay for storage and requests
- Batch: Pay for Fargate compute time (Spot pricing available)
- CloudWatch: Pay for log storage and alarms

Estimated monthly cost for 500 students: ~$51/month (see architecture.md for details).

## Security

- All S3 buckets have public access blocked
- IAM roles follow least privilege principle
- Lambda function uses VPC endpoints (if configured)
- API Gateway can be configured with API keys or IAM authentication
- All resources are tagged with Environment and Project

## Troubleshooting

### Stack Creation Fails

1. Check CloudFormation events for specific error messages
2. Verify IAM permissions for stack creation
3. Ensure S3 bucket exists and is accessible
4. Check that all required parameters are provided

### Lambda Function Errors

1. Check CloudWatch Logs for the Lambda function
2. Verify environment variables are set correctly
3. Ensure Lambda execution role has required permissions
4. Check Lambda deployment package includes all dependencies

### Batch Jobs Fail

1. Check Batch job logs in CloudWatch
2. Verify ECR image URI is correct
3. Ensure Batch execution role has required permissions
4. Check compute environment is in ENABLED state

