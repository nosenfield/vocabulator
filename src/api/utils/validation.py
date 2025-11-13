"""Validation utilities for API endpoints.

This module provides shared validation functions and constants used across
multiple API endpoints.
"""

import re

# Student ID format: STU-XXX where XXX is a 3-digit number
STUDENT_ID_PATTERN = r"^STU-\d{3}$"
STUDENT_ID_REGEX = re.compile(STUDENT_ID_PATTERN)


def validate_student_id(student_id: str) -> str:
    """Validate student ID format.
    
    Args:
        student_id: Student ID to validate
        
    Returns:
        Validated student ID
        
    Raises:
        ValueError: If student ID format is invalid
    """
    if not STUDENT_ID_REGEX.match(student_id):
        raise ValueError(
            f"Student ID must match format: STU-XXX (e.g., STU-001), got: {student_id}"
        )
    return student_id

