"""Cost tracking for OpenAI API usage.

This module tracks token usage and costs for OpenAI API requests,
providing per-request and aggregate cost tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("ai.cost_tracker")

# OpenAI pricing (as of 2024, in USD per 1M tokens)
# These should be updated if pricing changes
PRICING = {
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,  # $0.15 per 1M input tokens
        "output": 0.60 / 1_000_000,  # $0.60 per 1M output tokens
    },
    "gpt-4o": {
        "input": 2.50 / 1_000_000,  # $2.50 per 1M input tokens
        "output": 10.00 / 1_000_000,  # $10.00 per 1M output tokens
    },
}


class OperationType(str, Enum):
    """Types of OpenAI operations."""

    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"


@dataclass
class CostRecord:
    """Record of a single API request cost."""

    timestamp: datetime
    model: str
    operation_type: OperationType
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float
    request_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "operation_type": self.operation_type.value,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "estimated_cost": self.estimated_cost,
            "request_id": self.request_id,
        }


class CostTracker:
    """Track OpenAI API costs per request and aggregate.

    This tracker logs token usage and calculates costs based on
    current OpenAI pricing. It maintains a history of requests
    and provides aggregate statistics.
    """

    def __init__(self):
        """Initialize cost tracker."""
        self.records: List[CostRecord] = []
        self._total_cost: float = 0.0
        self._total_requests: int = 0

    def log(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        operation_type: OperationType = OperationType.EXTRACTION,
        request_id: Optional[str] = None,
    ) -> CostRecord:
        """Log a cost record for an API request.

        Args:
            model: Model used (gpt-4o-mini or gpt-4o)
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            operation_type: Type of operation performed
            request_id: Optional request ID for correlation

        Returns:
            CostRecord instance with calculated cost

        Raises:
            ValueError: If model pricing not found
        """
        if model not in PRICING:
            logger.warning(
                f"Unknown model pricing for {model}, using gpt-4o-mini pricing"
            )
            model_pricing = PRICING["gpt-4o-mini"]
        else:
            model_pricing = PRICING[model]

        # Calculate cost
        # Pricing is already per token (divided by 1M in PRICING dict)
        input_cost = prompt_tokens * model_pricing["input"]
        output_cost = completion_tokens * model_pricing["output"]
        estimated_cost = input_cost + output_cost

        # Create record
        record = CostRecord(
            timestamp=datetime.now(timezone.utc),
            model=model,
            operation_type=operation_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost=estimated_cost,
            request_id=request_id,
        )

        # Store record
        self.records.append(record)
        self._total_cost += estimated_cost
        self._total_requests += 1

        # Log cost
        logger.info(
            f"OpenAI API cost tracked",
            extra={
                "model": model,
                "operation_type": operation_type.value,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost": round(estimated_cost, 6),
                "request_id": request_id,
            },
        )

        return record

    @property
    def total_cost(self) -> float:
        """Get total cost across all requests.

        Returns:
            Total estimated cost in USD
        """
        return self._total_cost

    @property
    def total_requests(self) -> int:
        """Get total number of requests tracked.

        Returns:
            Total request count
        """
        return self._total_requests

    def get_stats(self) -> Dict:
        """Get aggregate statistics.

        Returns:
            Dictionary with cost statistics
        """
        if not self.records:
            return {
                "total_requests": 0,
                "total_cost": 0.0,
                "average_cost_per_request": 0.0,
                "total_tokens": 0,
            }

        total_tokens = sum(
            r.prompt_tokens + r.completion_tokens for r in self.records
        )

        return {
            "total_requests": self._total_requests,
            "total_cost": round(self._total_cost, 6),
            "average_cost_per_request": round(
                self._total_cost / self._total_requests, 6
            ),
            "total_tokens": total_tokens,
            "by_model": self._get_stats_by_model(),
            "by_operation": self._get_stats_by_operation(),
        }

    def _get_stats_by_model(self) -> Dict[str, Dict]:
        """Get statistics grouped by model."""
        by_model: Dict[str, Dict] = {}
        for record in self.records:
            if record.model not in by_model:
                by_model[record.model] = {
                    "requests": 0,
                    "cost": 0.0,
                    "tokens": 0,
                }
            by_model[record.model]["requests"] += 1
            by_model[record.model]["cost"] += record.estimated_cost
            by_model[record.model]["tokens"] += (
                record.prompt_tokens + record.completion_tokens
            )

        # Round costs
        for model_stats in by_model.values():
            model_stats["cost"] = round(model_stats["cost"], 6)

        return by_model

    def _get_stats_by_operation(self) -> Dict[str, Dict]:
        """Get statistics grouped by operation type."""
        by_op: Dict[str, Dict] = {}
        for record in self.records:
            op_key = record.operation_type.value
            if op_key not in by_op:
                by_op[op_key] = {
                    "requests": 0,
                    "cost": 0.0,
                    "tokens": 0,
                }
            by_op[op_key]["requests"] += 1
            by_op[op_key]["cost"] += record.estimated_cost
            by_op[op_key]["tokens"] += (
                record.prompt_tokens + record.completion_tokens
            )

        # Round costs
        for op_stats in by_op.values():
            op_stats["cost"] = round(op_stats["cost"], 6)

        return by_op

    def reset(self):
        """Reset tracker (useful for testing)."""
        self.records.clear()
        self._total_cost = 0.0
        self._total_requests = 0

