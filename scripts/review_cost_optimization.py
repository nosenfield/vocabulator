#!/usr/bin/env python3
"""Review and optimize costs for Vocabulator MVP.

This script analyzes cost usage and provides optimization recommendations.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.cost_tracker import CostTracker, OperationType, PRICING
from src.utils.logger import get_logger

logger = get_logger("scripts.review_cost_optimization")

# Target cost per student per month (from architecture.md)
TARGET_COST_PER_STUDENT = 51.0 / 500.0  # $0.102 per student per month
TARGET_MONTHLY_COST = 51.0  # $51/month for 500 students


def calculate_estimated_monthly_cost(
    students: int = 500,
    transcripts_per_student: int = 20,
    writing_samples_per_student: int = 5,
) -> Dict:
    """Calculate estimated monthly cost based on usage patterns.
    
    Args:
        students: Number of students
        transcripts_per_student: Transcripts per student per month
        writing_samples_per_student: Writing samples per student per month
        
    Returns:
        Dictionary with cost breakdown
    """
    # Average token usage per operation (aligned with architecture.md estimates)
    # Architecture target: ~10M tokens GPT-4o-mini, ~2M tokens GPT-4o for 500 students
    # Per-student estimates: 20k tokens GPT-4o-mini, 4k tokens GPT-4o
    
    # GPT-4o-mini: ~20k tokens per student (extraction only)
    # 25 texts per student * 800 tokens average = 20k tokens
    EXTRACTION_TOKENS = {
        "input": 600,  # Average transcript/writing sample (after preprocessing)
        "output": 200,  # Extracted vocabulary list (concise format)
    }
    
    # GPT-4o: ~4k tokens per student (analysis + recommendation)
    # Analysis: ~2k tokens, Recommendation: ~2k tokens
    ANALYSIS_TOKENS = {
        "input": 1500,  # Student profile summary + gap analysis prompt
        "output": 500,  # Gap analysis results (concise)
    }
    
    RECOMMENDATION_TOKENS = {
        "input": 1000,  # Gap words + recommendation prompt
        "output": 1000,  # Recommendations with definitions
    }
    
    # Calculate operations per month
    total_texts = students * (transcripts_per_student + writing_samples_per_student)
    extractions = total_texts  # One extraction per text
    analyses = students  # One analysis per student per month
    recommendations = students  # One recommendation set per student per month
    
    # Calculate costs using GPT-4o-mini for extraction, GPT-4o for analysis/recommendation
    extraction_cost = (
        extractions
        * (
            EXTRACTION_TOKENS["input"] * PRICING["gpt-4o-mini"]["input"]
            + EXTRACTION_TOKENS["output"] * PRICING["gpt-4o-mini"]["output"]
        )
    )
    
    analysis_cost = (
        analyses
        * (
            ANALYSIS_TOKENS["input"] * PRICING["gpt-4o"]["input"]
            + ANALYSIS_TOKENS["output"] * PRICING["gpt-4o"]["output"]
        )
    )
    
    recommendation_cost = (
        recommendations
        * (
            RECOMMENDATION_TOKENS["input"] * PRICING["gpt-4o"]["input"]
            + RECOMMENDATION_TOKENS["output"] * PRICING["gpt-4o"]["output"]
        )
    )
    
    total_openai_cost = float(extraction_cost + analysis_cost + recommendation_cost)
    
    # AWS costs (from architecture.md estimates)
    aws_costs = {
        "lambda": 1.0,  # $1.00 for 50k invocations
        "batch_fargate": 40.0,  # $40.00 for 100 hours
        "s3": 1.15,  # $1.15 for 50GB
        "dynamodb": 1.5,  # $1.50 for 5M reads, 1M writes
        "cloudfront": 0.85,  # $0.85 for 10GB transfer
    }
    
    # Scale AWS costs linearly with student count (simplified)
    scale_factor = students / 500.0
    scaled_aws_cost = sum(aws_costs.values()) * scale_factor
    
    total_cost = total_openai_cost + scaled_aws_cost
    
    return {
        "students": students,
        "openai_costs": {
            "extraction": float(extraction_cost),
            "analysis": float(analysis_cost),
            "recommendation": float(recommendation_cost),
            "total": total_openai_cost,
        },
        "aws_costs": {
            **aws_costs,
            "total": scaled_aws_cost,
        },
        "total_monthly_cost": total_cost,
        "cost_per_student": total_cost / students,
        "target_cost": TARGET_MONTHLY_COST if students == 500 else (TARGET_COST_PER_STUDENT * students),
        "within_target": total_cost <= (TARGET_MONTHLY_COST if students == 500 else (TARGET_COST_PER_STUDENT * students)),
    }


def review_prompt_optimization() -> List[str]:
    """Review prompt optimization opportunities.
    
    Returns:
        List of optimization recommendations
    """
    recommendations = []
    
    # Check prompt files
    prompt_dir = Path("src/ai/prompts")
    if prompt_dir.exists():
        prompt_files = list(prompt_dir.glob("*.py"))
        total_prompts = len(prompt_files)
        
        if total_prompts > 0:
            recommendations.append(
                f"✅ Found {total_prompts} prompt template files - review for optimization opportunities"
            )
            recommendations.append(
                "  - Consider using shorter, more focused prompts where possible"
            )
            recommendations.append(
                "  - Use few-shot examples sparingly (they increase token count)"
            )
            recommendations.append(
                "  - Cache common prompt patterns to reduce redundant token usage"
            )
        else:
            recommendations.append("⚠️  No prompt files found - prompts may be hardcoded")
    else:
        recommendations.append("⚠️  Prompt directory not found")
    
    return recommendations


def review_caching_opportunities() -> List[str]:
    """Review caching opportunities for cost reduction.
    
    Returns:
        List of caching recommendations
    """
    recommendations = []
    
    recommendations.append("Caching Opportunities:")
    recommendations.append("  1. OpenAI API Responses:")
    recommendations.append("     - Cache vocabulary extraction results for identical texts")
    recommendations.append("     - Cache gap analysis for students with unchanged profiles")
    recommendations.append("     - Use DynamoDB TTL for cache expiration (30 days)")
    
    recommendations.append("  2. Common Core Vocabulary:")
    recommendations.append("     - Load vocabulary corpus once and cache in memory")
    recommendations.append("     - Consider Redis for distributed caching (if scaling)")
    
    recommendations.append("  3. Student Profiles:")
    recommendations.append("     - Cache frequently accessed profiles in Lambda memory")
    recommendations.append("     - Use CloudFront for static report caching")
    
    return recommendations


def review_aws_resource_sizing() -> List[str]:
    """Review AWS resource sizing for cost optimization.
    
    Returns:
        List of sizing recommendations
    """
    recommendations = []
    
    recommendations.append("AWS Resource Sizing Review:")
    recommendations.append("  1. Lambda Functions:")
    recommendations.append("     - Current: 512MB-1GB memory")
    recommendations.append("     - Recommendation: Monitor actual usage, reduce if possible")
    recommendations.append("     - Cost impact: ~$0.20 per 1M requests per 128MB")
    
    recommendations.append("  2. AWS Batch/Fargate:")
    recommendations.append("     - Current: 2 vCPU, 4GB memory")
    recommendations.append("     - Recommendation: Test with 1 vCPU, 2GB for smaller batches")
    recommendations.append("     - Cost impact: ~50% reduction possible")
    
    recommendations.append("  3. DynamoDB:")
    recommendations.append("     - Current: On-demand billing")
    recommendations.append("     - Recommendation: Monitor usage, consider provisioned capacity if predictable")
    recommendations.append("     - Cost impact: Variable based on usage patterns")
    
    recommendations.append("  4. S3 Storage:")
    recommendations.append("     - Current: Standard storage")
    recommendations.append("     - Recommendation: Use Intelligent-Tiering for old data")
    recommendations.append("     - Cost impact: ~40% savings on infrequently accessed data")
    
    return recommendations


def generate_cost_budget_alarms() -> Dict:
    """Generate CloudWatch budget and alarm configuration.
    
    Returns:
        Dictionary with budget and alarm recommendations
    """
    return {
        "budgets": [
            {
                "name": "vocabulator-monthly-budget",
                "amount": 60.0,  # 20% buffer above target
                "threshold": 80.0,  # Alert at 80% of budget
                "period": "monthly",
            },
            {
                "name": "vocabulator-openai-daily-budget",
                "amount": 2.0,  # Daily OpenAI budget (~$60/month / 30 days)
                "threshold": 1.5,  # Alert at $1.50/day
                "period": "daily",
            },
        ],
        "alarms": [
            {
                "name": "openai-cost-exceeded",
                "metric": "OpenAICostPerStudent",
                "threshold": TARGET_COST_PER_STUDENT * 1.2,  # 20% over target
                "comparison": "GreaterThanThreshold",
            },
            {
                "name": "aws-monthly-cost-exceeded",
                "metric": "AWSMonthlyCost",
                "threshold": 25.0,  # AWS portion of budget
                "comparison": "GreaterThanThreshold",
            },
        ],
    }


def main():
    """Main entry point for cost optimization review."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Review and optimize Vocabulator costs")
    parser.add_argument(
        "--students",
        type=int,
        default=500,
        help="Number of students for cost calculation (default: 500)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for cost report (default: stdout)",
    )
    
    args = parser.parse_args()
    
    logger.info("Starting cost optimization review...")
    
    # Calculate estimated costs
    cost_breakdown = calculate_estimated_monthly_cost(students=args.students)
    
    # Generate recommendations
    prompt_recommendations = review_prompt_optimization()
    caching_recommendations = review_caching_opportunities()
    sizing_recommendations = review_aws_resource_sizing()
    budget_alarms = generate_cost_budget_alarms()
    
    # Generate report
    report = {
        "cost_analysis": cost_breakdown,
        "recommendations": {
            "prompt_optimization": prompt_recommendations,
            "caching": caching_recommendations,
            "aws_sizing": sizing_recommendations,
        },
        "budget_alarms": budget_alarms,
        "summary": {
            "estimated_monthly_cost": cost_breakdown["total_monthly_cost"],
            "target_cost": cost_breakdown["target_cost"],
            "within_target": cost_breakdown["within_target"],
            "cost_per_student": cost_breakdown["cost_per_student"],
        },
    }
    
    # Output report
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Cost report written to {args.output}")
    else:
        print("\n" + "=" * 80)
        print("COST OPTIMIZATION REVIEW")
        print("=" * 80)
        print(f"\nEstimated Monthly Cost for {args.students} students:")
        print(f"  OpenAI API: ${cost_breakdown['openai_costs']['total']:.2f}")
        print(f"    - Extraction (GPT-4o-mini): ${cost_breakdown['openai_costs']['extraction']:.2f}")
        print(f"    - Analysis (GPT-4o): ${cost_breakdown['openai_costs']['analysis']:.2f}")
        print(f"    - Recommendations (GPT-4o): ${cost_breakdown['openai_costs']['recommendation']:.2f}")
        print(f"  AWS Services: ${cost_breakdown['aws_costs']['total']:.2f}")
        print(f"  Total: ${cost_breakdown['total_monthly_cost']:.2f}")
        print(f"  Cost per student: ${cost_breakdown['cost_per_student']:.4f}")
        print(f"  Target: ${cost_breakdown['target_cost']:.2f}")
        print(f"  Status: {'✅ Within target' if cost_breakdown['within_target'] else '⚠️  Exceeds target'}")
        
        print("\n" + "=" * 80)
        print("OPTIMIZATION RECOMMENDATIONS")
        print("=" * 80)
        
        print("\nPrompt Optimization:")
        for rec in prompt_recommendations:
            print(f"  {rec}")
        
        print("\n" + "\n".join(caching_recommendations))
        
        print("\n" + "\n".join(sizing_recommendations))
        
        print("\n" + "=" * 80)
        print("BUDGET & ALARM RECOMMENDATIONS")
        print("=" * 80)
        print("\nCloudWatch Budgets:")
        for budget in budget_alarms["budgets"]:
            print(f"  - {budget['name']}: ${budget['amount']:.2f}/{budget['period']} (alert at ${budget['threshold']:.2f})")
        
        print("\nCloudWatch Alarms:")
        for alarm in budget_alarms["alarms"]:
            print(f"  - {alarm['name']}: {alarm['metric']} > ${alarm['threshold']:.2f}")
    
    logger.info("Cost optimization review completed")


if __name__ == "__main__":
    main()

