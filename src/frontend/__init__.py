"""Frontend module for Vocabulator.

This module provides HTML report generation functionality.
"""

from src.frontend.templates import render_profile_report, render_recommendations_report
from src.frontend.report_generator import ReportGenerator, ReportGenerationError

__all__ = [
    "render_profile_report",
    "render_recommendations_report",
    "ReportGenerator",
    "ReportGenerationError",
]

