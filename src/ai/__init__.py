"""AI/ML layer for Vocabulator.

This package contains OpenAI integration, prompt templates, and
vocabulary processing logic.
"""

# Lazy imports to avoid import errors if dependencies aren't installed
try:
    from src.ai.cost_tracker import CostTracker, OperationType
    from src.ai.openai_client import OpenAIClient

    __all__ = ["OpenAIClient", "CostTracker", "OperationType"]
except ImportError:
    # Allow imports to fail gracefully during test collection if deps not installed
    __all__ = []

