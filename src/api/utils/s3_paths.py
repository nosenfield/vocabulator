"""S3 path construction utilities.

This module provides helper functions for safely constructing S3 object keys.
"""

import re
from datetime import date, datetime
from typing import Optional


def sanitize_path_component(component: str) -> str:
    """Sanitize a path component for use in S3 keys.
    
    Removes or replaces characters that could cause issues in S3 paths:
    - Removes leading/trailing whitespace
    - Replaces spaces with hyphens
    - Removes special characters except hyphens, underscores, and dots
    - Limits length to 255 characters
    
    Args:
        component: Path component to sanitize
        
    Returns:
        Sanitized path component
        
    Example:
        >>> sanitize_path_component("STU-001")
        'STU-001'
        >>> sanitize_path_component("2025-11-10")
        '2025-11-10'
        >>> sanitize_path_component("file name.txt")
        'file-name.txt'
    """
    if not component:
        return ""
    
    # Remove leading/trailing whitespace
    component = component.strip()
    
    # Security: Prevent path traversal attacks BEFORE sanitization
    if ".." in component or component.startswith("."):
        raise ValueError(
            f"Path component cannot contain '..' or start with '.': {component}"
        )
    
    # Replace spaces with hyphens
    component = component.replace(" ", "-")
    
    # Remove special characters except hyphens, underscores, dots, and alphanumeric
    component = re.sub(r"[^a-zA-Z0-9._-]", "", component)
    
    # Limit length (S3 key component limit is effectively 1024, but 255 is safer)
    MAX_PATH_COMPONENT_LENGTH = 255
    if len(component) > MAX_PATH_COMPONENT_LENGTH:
        component = component[:MAX_PATH_COMPONENT_LENGTH]
    
    return component


def build_s3_path(*components: str, extension: Optional[str] = None) -> str:
    """Build a safe S3 object key from path components.
    
    Args:
        *components: Path components to join (will be sanitized)
        extension: Optional file extension (without leading dot)
        
    Returns:
        S3 object key path
        
    Example:
        >>> build_s3_path("transcripts", "raw", "STU-001", "2025-11-10", extension="txt")
        'transcripts/raw/STU-001/2025-11-10.txt'
        >>> build_s3_path("writing-samples", "raw", "STU-001", "ASSIGN-001", extension="txt")
        'writing-samples/raw/STU-001/ASSIGN-001.txt'
    """
    # Sanitize all components
    sanitized = [sanitize_path_component(str(comp)) for comp in components if comp]
    
    # Join with forward slashes
    path = "/".join(sanitized)
    
    # Add extension if provided
    if extension:
        # Remove leading dot if present
        extension = extension.lstrip(".")
        if extension:
            path = f"{path}.{extension}"
    
    return path


def format_date_for_path(date_value: date) -> str:
    """Format a date for use in S3 paths.
    
    Uses ISO format (YYYY-MM-DD) which is safe for S3 paths.
    
    Args:
        date_value: Date to format
        
    Returns:
        Formatted date string (YYYY-MM-DD)
        
    Example:
        >>> from datetime import date
        >>> format_date_for_path(date(2025, 11, 10))
        '2025-11-10'
    """
    return date_value.isoformat()


def format_datetime_for_path(dt: datetime, include_time: bool = False) -> str:
    """Format a datetime for use in S3 paths.
    
    Args:
        dt: Datetime to format
        include_time: Whether to include time component
        
    Returns:
        Formatted datetime string
        
    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 11, 10, 14, 30, 0, tzinfo=timezone.utc)
        >>> format_datetime_for_path(dt, include_time=False)
        '2025-11-10'
        >>> format_datetime_for_path(dt, include_time=True)
        '2025-11-10-14-30-00'
    """
    if include_time:
        # Format as YYYY-MM-DD-HH-MM-SS (replacing colons with hyphens)
        return dt.strftime("%Y-%m-%d-%H-%M-%S")
    else:
        return dt.date().isoformat()

