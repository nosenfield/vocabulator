# Monitoring & Alerting Setup

This directory contains documentation and scripts for setting up monitoring and alerting for the Vocabulator MVP.

## Overview

The monitoring setup includes:
- **CloudWatch Logs**: Centralized logging for Lambda and Batch jobs
- **CloudWatch Alarms**: Automated alerts for critical issues
- **SNS Topics**: Notification channels for alarms
- **CloudWatch Dashboard**: Visual monitoring dashboard

## CloudWatch Alarms

The following alarms are configured:

### Critical Alarms

1. **Lambda Error Rate** (`vocabulator-{env}-lambda-error-rate`)
   - Triggers when error rate exceeds 5%
   - Period: 5 minutes
   - Evaluation: 2 periods

2. **Lambda Throttles** (`vocabulator-{env}-lambda-throttles`)
   - Triggers on any Lambda throttles
   - Period: 5 minutes
   - Indicates need for concurrency limit increase

3. **Lambda Duration** (`vocabulator-{env}-lambda-duration`)
   - Triggers when average duration exceeds 25 seconds (80% of 30s timeout)
   - Period: 5 minutes
   - Evaluation: 2 periods
   - Warning before timeout

4. **Batch Job Failures** (`vocabulator-{env}-batch-failure-rate`)
   - Triggers when failure rate exceeds 10%
   - Period: 5 minutes
   - Evaluation: 2 periods

5. **DynamoDB Throttles** (`vocabulator-{env}-dynamodb-throttles`)
   - Triggers on any DynamoDB throttling events
   - Period: 5 minutes
   - Indicates need for capacity increase

6. **Daily Cost** (`vocabulator-{env}-daily-cost`)
   - Triggers when daily AWS cost exceeds $20
   - Period: 24 hours
   - Helps prevent cost overruns

## SNS Topic Setup

### Option 1: Create via CloudFormation (Recommended)

When deploying the master stack, provide an email address:

```bash
aws cloudformation create-stack \
  --stack-name vocabulator-<environment> \
  --template-body file://master-stack.yaml \
  --parameters \
    ParameterKey=EmailAddress,ParameterValue=alerts@example.com \
    ...
```

The stack will:
1. Create an SNS topic
2. Subscribe the email address
3. Send a confirmation email (you must confirm the subscription)

### Option 2: Manual Setup

```bash
# Create SNS topic
aws sns create-topic --name vocabulator-<env>-alarms

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:vocabulator-dev-alarms \
  --protocol email \
  --notification-endpoint alerts@example.com

# Subscribe Slack (via webhook)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:vocabulator-dev-alarms \
  --protocol https \
  --notification-endpoint https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## CloudWatch Dashboard

A pre-configured dashboard is created with:
- Lambda metrics (invocations, errors, throttles, duration)
- Batch job metrics (submitted, succeeded, failed)
- DynamoDB metrics (read/write capacity, throttles)
- S3 storage metrics (object count, bucket size)
- AWS cost estimate

**Access**: AWS Console → CloudWatch → Dashboards → `vocabulator-{env}-monitoring`

## Custom Metrics

### Adding Custom Metrics

To track custom metrics (e.g., OpenAI API errors):

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='Vocabulator/Custom',
    MetricData=[
        {
            'MetricName': 'OpenAIErrors',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'production'},
                {'Name': 'Service', 'Value': 'vocabulary-extraction'}
            ]
        }
    ]
)
```

### Creating Custom Alarms

Add to `cloudwatch-logs.yaml`:

```yaml
OpenAIErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub 'vocabulator-${Environment}-openai-errors'
    MetricName: OpenAIErrors
    Namespace: Vocabulator/Custom
    Statistic: Sum
    Period: 3600  # 1 hour
    EvaluationPeriods: 1
    Threshold: 50
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SnsTopicArn
```

## Alert Response Procedures

### Lambda Error Rate > 5%

1. Check CloudWatch Logs for error patterns
2. Review recent deployments
3. Check for dependency issues
4. Scale up if needed (concurrent executions)

### Batch Job Failures > 10%

1. Check Batch job logs in CloudWatch
2. Review job definitions and resource limits
3. Check for S3 access issues
4. Verify DynamoDB table access

### DynamoDB Throttles

1. Review table capacity settings
2. Check for hot partitions
3. Consider increasing reserved capacity (if using provisioned)
4. Review query patterns for optimization

### Daily Cost > $20

1. Review CloudWatch cost breakdown
2. Check for runaway Lambda invocations
3. Review Batch job frequency
4. Check S3 storage size
5. Review DynamoDB read/write units

## Monitoring Best Practices

1. **Set up alerts early**: Configure alarms before production deployment
2. **Monitor trends**: Use CloudWatch dashboards to spot trends
3. **Set appropriate thresholds**: Adjust thresholds based on actual usage patterns
4. **Review regularly**: Check alarms weekly and adjust as needed
5. **Document procedures**: Keep runbooks for common alert scenarios

## Cost Optimization

- CloudWatch Logs: 30-day retention (configurable)
- CloudWatch Metrics: Standard metrics are free, custom metrics cost $0.30/metric/month
- SNS: First 1M requests/month free, then $0.50 per 100K
- Dashboard: Free (no additional cost)

**Estimated monthly cost**: < $5 for standard monitoring

## Troubleshooting

### Alarms Not Triggering

1. Verify SNS topic exists and subscriptions are confirmed
2. Check alarm state in CloudWatch console
3. Verify metric data is being published
4. Check alarm evaluation periods and thresholds

### Too Many False Positives

1. Increase evaluation periods
2. Adjust thresholds based on baseline metrics
3. Use anomaly detection instead of static thresholds
4. Review alarm conditions

### Missing Metrics

1. Verify IAM permissions for CloudWatch PutMetricData
2. Check that metrics are being published from application code
3. Verify namespace and metric names match
4. Check CloudWatch metric filters for log-based metrics

