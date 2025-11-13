"""Tests for cost optimization review script."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.review_cost_optimization import (
    calculate_estimated_monthly_cost,
    generate_cost_budget_alarms,
    review_caching_opportunities,
    review_prompt_optimization,
    review_aws_resource_sizing,
)


def test_calculate_estimated_monthly_cost_default():
    """Test cost calculation with default parameters."""
    result = calculate_estimated_monthly_cost()
    
    assert result["students"] == 500
    assert "openai_costs" in result
    assert "aws_costs" in result
    assert "total_monthly_cost" in result
    assert "cost_per_student" in result
    assert result["total_monthly_cost"] > 0
    assert result["cost_per_student"] > 0


def test_calculate_estimated_monthly_cost_custom_students():
    """Test cost calculation with custom student count."""
    result = calculate_estimated_monthly_cost(students=1000)
    
    assert result["students"] == 1000
    assert result["total_monthly_cost"] > 0
    assert result["cost_per_student"] > 0


def test_calculate_estimated_monthly_cost_structure():
    """Test that cost breakdown has expected structure."""
    result = calculate_estimated_monthly_cost()
    
    assert "extraction" in result["openai_costs"]
    assert "analysis" in result["openai_costs"]
    assert "recommendation" in result["openai_costs"]
    assert "total" in result["openai_costs"]
    assert "total" in result["aws_costs"]


def test_review_prompt_optimization():
    """Test prompt optimization review."""
    recommendations = review_prompt_optimization()
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0


def test_review_caching_opportunities():
    """Test caching opportunities review."""
    recommendations = review_caching_opportunities()
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any("Caching" in rec for rec in recommendations)


def test_review_aws_resource_sizing():
    """Test AWS resource sizing review."""
    recommendations = review_aws_resource_sizing()
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any("Lambda" in rec for rec in recommendations)


def test_generate_cost_budget_alarms():
    """Test budget and alarm generation."""
    alarms = generate_cost_budget_alarms()
    
    assert "budgets" in alarms
    assert "alarms" in alarms
    assert len(alarms["budgets"]) > 0
    assert len(alarms["alarms"]) > 0
    
    # Check budget structure
    for budget in alarms["budgets"]:
        assert "name" in budget
        assert "amount" in budget
        assert "threshold" in budget
        assert "period" in budget
    
    # Check alarm structure
    for alarm in alarms["alarms"]:
        assert "name" in alarm
        assert "metric" in alarm
        assert "threshold" in alarm
        assert "comparison" in alarm

