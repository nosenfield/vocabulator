# Cost Optimization Review

**Date:** 2025-11-12  
**Reviewer:** Development Team  
**Target:** $51/month for 500 students

## Executive Summary

This document reviews cost optimization opportunities for the Vocabulator MVP to ensure we meet the target cost of $51/month for 500 students.

## Current Cost Estimates

Based on architecture.md and cost tracking implementation:

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| OpenAI API (GPT-4o-mini) | ~$1.50 | Vocabulary extraction |
| OpenAI API (GPT-4o) | ~$5.00 | Gap analysis & recommendations |
| Lambda | ~$1.00 | 50k invocations @ 512MB |
| AWS Batch + Fargate | ~$40.00 | 100 hours @ 2vCPU/4GB |
| S3 Storage | ~$1.15 | 50GB |
| DynamoDB | ~$1.50 | 5M reads, 1M writes |
| CloudFront | ~$0.85 | 10GB transfer |
| **Total** | **~$51/month** | ✅ Within target |

## Cost Optimization Strategies

### 1. OpenAI API Optimization

#### Prompt Optimization
- ✅ **Current**: Prompt templates are modular and focused
- **Recommendation**: Review prompts for unnecessary verbosity
- **Impact**: 10-20% token reduction possible
- **Action**: Run `scripts/review_cost_optimization.py` to analyze prompt usage

#### Model Selection
- ✅ **Current**: GPT-4o-mini for extraction, GPT-4o for analysis
- **Rationale**: Cost-effective model selection already implemented
- **Impact**: 10x cost savings vs using GPT-4o for all operations

#### Caching Strategy
- **Opportunity**: Cache extraction results for identical texts
- **Implementation**: Use DynamoDB with TTL for cache entries
- **Impact**: 20-30% reduction in extraction costs for duplicate content
- **Priority**: Medium (post-MVP enhancement)

### 2. AWS Resource Optimization

#### Lambda Memory Sizing
- **Current**: 512MB-1GB memory
- **Recommendation**: Monitor actual usage, reduce to 256MB if possible
- **Impact**: ~$0.20 per 1M requests per 128MB reduction
- **Action**: Monitor CloudWatch metrics after deployment

#### Batch/Fargate Sizing
- **Current**: 2 vCPU, 4GB memory
- **Recommendation**: Test with 1 vCPU, 2GB for smaller batches
- **Impact**: ~50% cost reduction for smaller workloads
- **Action**: Performance test with reduced resources

#### DynamoDB Billing
- **Current**: On-demand billing
- **Recommendation**: Monitor usage patterns, consider provisioned capacity if predictable
- **Impact**: Variable (can reduce costs if usage is predictable)
- **Action**: Monitor for 1 month, then optimize

#### S3 Storage Classes
- **Current**: Standard storage
- **Recommendation**: Use Intelligent-Tiering for data older than 30 days
- **Impact**: ~40% savings on infrequently accessed data
- **Action**: Configure lifecycle policies

### 3. Caching Implementation

#### Response Caching
- **Vocabulary Extraction**: Cache results for identical text inputs
- **Gap Analysis**: Cache for students with unchanged profiles
- **Recommendations**: Cache for 24 hours (refresh daily)

#### In-Memory Caching
- **Common Core Vocabulary**: Load once, cache in Lambda memory
- **Student Profiles**: Cache frequently accessed profiles
- **Impact**: Reduces DynamoDB read costs

### 4. Cost Monitoring & Alerts

#### CloudWatch Budgets
Configure the following budgets:

1. **Monthly Budget**: $60 (20% buffer above target)
   - Alert at 80% ($48)
   - Alert at 100% ($60)

2. **Daily OpenAI Budget**: $2.00
   - Alert at $1.50/day
   - Prevents runaway costs

#### CloudWatch Alarms
Set up alarms for:
- OpenAI cost per student exceeds $0.12/month
- AWS monthly cost exceeds $25
- Lambda error rate > 1%
- Batch job failure rate > 5%

## Validation Plan

### Phase 1: Baseline Measurement (Week 1)
1. Deploy to demo environment
2. Run with test data (500 students)
3. Measure actual costs
4. Compare to estimates

### Phase 2: Optimization (Week 2)
1. Implement caching for vocabulary extraction
2. Optimize Lambda memory allocation
3. Review and optimize prompts
4. Configure S3 lifecycle policies

### Phase 3: Validation (Week 3)
1. Re-run cost analysis
2. Verify costs within target
3. Document optimizations
4. Update cost estimates

## Cost Tracking

The system includes built-in cost tracking via `CostTracker`:
- Tracks all OpenAI API calls
- Logs token usage and costs
- Provides aggregate statistics
- Can be exported for analysis

Run cost analysis:
```bash
python3 scripts/review_cost_optimization.py --students 500
```

## Recommendations Summary

### Immediate (Pre-Launch)
1. ✅ Cost tracking implemented
2. ✅ Model selection optimized (GPT-4o-mini for extraction)
3. ⚠️ Set up CloudWatch budgets and alarms
4. ⚠️ Configure S3 lifecycle policies

### Short-Term (Post-Launch)
1. Implement response caching
2. Optimize Lambda memory allocation
3. Review prompt efficiency
4. Monitor and adjust resource sizing

### Long-Term (Scaling)
1. Consider Redis for distributed caching
2. Implement request batching
3. Optimize batch job resource allocation
4. Review cost per student as scale increases

## Conclusion

The current architecture is designed to meet the $51/month target for 500 students. Key optimizations already in place:
- ✅ Efficient model selection (GPT-4o-mini for extraction)
- ✅ Cost tracking and monitoring
- ✅ Serverless architecture (pay-per-use)

Additional optimizations recommended:
- Set up cost budgets and alarms
- Implement caching for duplicate content
- Monitor and optimize resource sizing

**Status**: ✅ Architecture supports target cost with optimization opportunities identified.

