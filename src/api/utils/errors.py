"""Standardized error response utilities.

This module provides helper functions for creating consistent error responses
across all API endpoints.
"""

from typing import Any, Dict, Optional


def create_error_response(
    error_code: str,
    message: str,
    request_id: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a standardized error response.
    
    Args:
        error_code: Machine-readable error code (e.g., "student_not_found")
        message: Human-readable error message
        request_id: Optional request ID for correlation
        **kwargs: Additional context fields to include
        
    Returns:
        Dictionary with standardized error structure
        
    Example:
        >>> create_error_response(
        ...     "student_not_found",
        ...     "No profile found for student STU-001",
        ...     request_id="abc-123",
        ...     student_id="STU-001"
        ... )
        {
            "error": "student_not_found",
            "message": "No profile found for student STU-001",
            "request_id": "abc-123",
            "student_id": "STU-001"
        }
    """
    response: Dict[str, Any] = {
        "error": error_code,
        "message": message,
    }
    
    if request_id:
        response["request_id"] = request_id
    
    # Add any additional context fields
    response.update(kwargs)
    
    return response


def create_validation_error_response(
    message: str,
    request_id: Optional[str] = None,
    field: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create a standardized validation error response.
    
    Args:
        message: Human-readable validation error message
        request_id: Optional request ID for correlation
        field: Optional field name that failed validation
        **kwargs: Additional context fields
        
    Returns:
        Dictionary with standardized validation error structure
    """
    return create_error_response(
        error_code="validation_error",
        message=message,
        request_id=request_id,
        field=field,
        **kwargs,
    )


def create_not_found_error_response(
    resource_type: str,
    resource_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized not found error response.
    
    Args:
        resource_type: Type of resource (e.g., "student", "recommendation")
        resource_id: Identifier of the resource
        request_id: Optional request ID for correlation
        
    Returns:
        Dictionary with standardized not found error structure
    """
    return create_error_response(
        error_code=f"{resource_type}_not_found",
        message=f"No {resource_type} found with identifier {resource_id}",
        request_id=request_id,
        **{f"{resource_type}_id": resource_id},
    )


def create_conflict_error_response(
    resource_type: str,
    resource_id: str,
    reason: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized conflict error response.
    
    Args:
        resource_type: Type of resource (e.g., "student", "recommendation")
        resource_id: Identifier of the resource
        reason: Reason for the conflict
        request_id: Optional request ID for correlation
        
    Returns:
        Dictionary with standardized conflict error structure
    """
    return create_error_response(
        error_code=f"{resource_type}_already_exists",
        message=f"{resource_type.capitalize()} {resource_id} already exists: {reason}",
        request_id=request_id,
        **{f"{resource_type}_id": resource_id},
    )


def create_internal_error_response(
    message: str = "An unexpected error occurred",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized internal error response.
    
    Args:
        message: Human-readable error message
        request_id: Optional request ID for correlation
        
    Returns:
        Dictionary with standardized internal error structure
    """
    return create_error_response(
        error_code="internal_error",
        message=message,
        request_id=request_id,
    )

