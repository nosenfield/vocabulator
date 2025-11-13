"""Unit tests for cost tracker.

Tests cover:
- Cost calculation for different models
- Cost record creation
- Statistics aggregation
- Reset functionality
"""

from datetime import datetime, timezone

import pytest

from src.ai.cost_tracker import CostRecord, CostTracker, OperationType


@pytest.mark.unit
class TestCostRecord:
    """Test CostRecord dataclass."""

    def test_create_record(self):
        """Test creating a cost record."""
        record = CostRecord(
            timestamp=datetime.now(timezone.utc),
            model="gpt-4o-mini",
            operation_type=OperationType.EXTRACTION,
            prompt_tokens=1000,
            completion_tokens=500,
            estimated_cost=0.00045,
            request_id="req-123",
        )

        assert record.model == "gpt-4o-mini"
        assert record.operation_type == OperationType.EXTRACTION
        assert record.prompt_tokens == 1000
        assert record.completion_tokens == 500
        assert record.estimated_cost == 0.00045
        assert record.request_id == "req-123"

    def test_to_dict(self):
        """Test converting record to dictionary."""
        record = CostRecord(
            timestamp=datetime.now(timezone.utc),
            model="gpt-4o-mini",
            operation_type=OperationType.EXTRACTION,
            prompt_tokens=1000,
            completion_tokens=500,
            estimated_cost=0.00045,
        )

        record_dict = record.to_dict()
        assert "timestamp" in record_dict
        assert record_dict["model"] == "gpt-4o-mini"
        assert record_dict["operation_type"] == "extraction"
        assert record_dict["prompt_tokens"] == 1000
        assert record_dict["completion_tokens"] == 500
        assert record_dict["total_tokens"] == 1500
        assert record_dict["estimated_cost"] == 0.00045


@pytest.mark.unit
class TestCostTracker:
    """Test CostTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = CostTracker()
        assert tracker.total_requests == 0
        assert tracker.total_cost == 0.0
        assert len(tracker.records) == 0

    def test_log_gpt4o_mini(self):
        """Test logging GPT-4o-mini request."""
        tracker = CostTracker()
        record = tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            operation_type=OperationType.EXTRACTION,
        )

        assert tracker.total_requests == 1
        assert tracker.total_cost > 0
        assert len(tracker.records) == 1
        assert record.model == "gpt-4o-mini"
        assert record.prompt_tokens == 1000
        assert record.completion_tokens == 500

        # Verify cost calculation (approximate)
        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        # Expected: (1000 * 0.15 + 500 * 0.60) / 1_000_000
        expected_cost = (1000 * 0.15 + 500 * 0.60) / 1_000_000
        assert abs(record.estimated_cost - expected_cost) < 0.000001

    def test_log_gpt4o(self):
        """Test logging GPT-4o request."""
        tracker = CostTracker()
        record = tracker.log(
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            operation_type=OperationType.ANALYSIS,
        )

        assert tracker.total_requests == 1
        assert record.model == "gpt-4o"
        assert record.operation_type == OperationType.ANALYSIS

        # GPT-4o should cost more than GPT-4o-mini
        gpt4o_cost = record.estimated_cost

        tracker2 = CostTracker()
        record2 = tracker2.log(
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        assert gpt4o_cost > record2.estimated_cost

    def test_log_with_request_id(self):
        """Test logging with request ID."""
        tracker = CostTracker()
        record = tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            request_id="req-123",
        )

        assert record.request_id == "req-123"

    def test_log_unknown_model(self):
        """Test logging with unknown model (should use default pricing)."""
        tracker = CostTracker()
        record = tracker.log(
            model="unknown-model",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Should still create record (uses gpt-4o-mini pricing as fallback)
        assert tracker.total_requests == 1
        assert record.model == "unknown-model"

    def test_multiple_logs(self):
        """Test logging multiple requests."""
        tracker = CostTracker()

        for i in range(5):
            tracker.log(
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
            )

        assert tracker.total_requests == 5
        assert len(tracker.records) == 5
        assert tracker.total_cost > 0

    def test_get_stats_empty(self):
        """Test getting stats when no records."""
        tracker = CostTracker()
        stats = tracker.get_stats()

        assert stats["total_requests"] == 0
        assert stats["total_cost"] == 0.0
        assert stats["average_cost_per_request"] == 0.0
        assert stats["total_tokens"] == 0

    def test_get_stats_with_records(self):
        """Test getting stats with multiple records."""
        tracker = CostTracker()

        # Log multiple requests
        tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
            operation_type=OperationType.EXTRACTION,
        )
        tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=2000,
            completion_tokens=1000,
            operation_type=OperationType.EXTRACTION,
        )
        tracker.log(
            model="gpt-4o",
            prompt_tokens=500,
            completion_tokens=250,
            operation_type=OperationType.ANALYSIS,
        )

        stats = tracker.get_stats()

        assert stats["total_requests"] == 3
        assert stats["total_cost"] > 0
        assert stats["average_cost_per_request"] > 0
        assert stats["total_tokens"] == 5250  # 1500 + 3000 + 750

        # Check by_model stats
        assert "gpt-4o-mini" in stats["by_model"]
        assert "gpt-4o" in stats["by_model"]
        assert stats["by_model"]["gpt-4o-mini"]["requests"] == 2
        assert stats["by_model"]["gpt-4o"]["requests"] == 1

        # Check by_operation stats
        assert "extraction" in stats["by_operation"]
        assert "analysis" in stats["by_operation"]
        assert stats["by_operation"]["extraction"]["requests"] == 2
        assert stats["by_operation"]["analysis"]["requests"] == 1

    def test_reset(self):
        """Test resetting tracker."""
        tracker = CostTracker()

        tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        assert tracker.total_requests == 1
        assert tracker.total_cost > 0

        tracker.reset()

        assert tracker.total_requests == 0
        assert tracker.total_cost == 0.0
        assert len(tracker.records) == 0

    def test_all_operation_types(self):
        """Test logging all operation types."""
        tracker = CostTracker()

        tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            operation_type=OperationType.EXTRACTION,
        )
        tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            operation_type=OperationType.ANALYSIS,
        )
        tracker.log(
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            operation_type=OperationType.RECOMMENDATION,
        )

        stats = tracker.get_stats()
        assert stats["by_operation"]["extraction"]["requests"] == 1
        assert stats["by_operation"]["analysis"]["requests"] == 1
        assert stats["by_operation"]["recommendation"]["requests"] == 1

