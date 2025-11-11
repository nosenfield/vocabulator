"""Prompt templates for AI operations."""

from src.ai.prompts.extraction import (
    build_batch_extraction_prompt,
    build_extraction_prompt,
    EXTRACTION_SYSTEM_PROMPT,
)
from src.ai.prompts.gap_analysis import (
    build_gap_analysis_prompt,
    GAP_ANALYSIS_SYSTEM_PROMPT,
)

__all__ = [
    "build_extraction_prompt",
    "build_batch_extraction_prompt",
    "EXTRACTION_SYSTEM_PROMPT",
    "build_gap_analysis_prompt",
    "GAP_ANALYSIS_SYSTEM_PROMPT",
]

