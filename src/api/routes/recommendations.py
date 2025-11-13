"""Recommendation endpoints.

This module provides endpoints for retrieving and updating vocabulary recommendations.
"""

import re
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.api.dependencies import (
    get_recommendation_repository,
    get_student_repository,
)
from src.api.models.requests import UpdateRecommendationStatusRequest
from src.api.models.responses import (
    RecommendationWordResponse,
    RecommendationsResponse,
    RecommendationsListResponse,
    RecommendationStatusResponse,
)
from src.api.utils.errors import (
    create_error_response,
    create_internal_error_response,
    create_not_found_error_response,
    create_validation_error_response,
)
from src.api.utils.validation import validate_student_id as validate_student_id_format
from src.data.models.recommendation import (
    RecommendationStatus,
    RecommendedWord,
    VocabularyRecommendation,
)
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.utils.logger import get_logger

logger = get_logger("api.routes.recommendations")

router = APIRouter()


def validate_student_id(student_id: str) -> str:
    """Validate student ID format.
    
    Args:
        student_id: Student ID to validate
        
    Returns:
        Validated student ID
        
    Raises:
        HTTPException: If student ID format is invalid
    """
    try:
        validate_student_id_format(student_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_validation_error_response(
                message=str(e),
                request_id=None,
                field="student_id",
                student_id=student_id,
            ),
        ) from e
    return student_id


def parse_recommendation_id(recommendation_id: str) -> tuple[str, str]:
    """Parse recommendation ID into student_id and recommendation_date.
    
    Format: {student_id}:{recommendation_date}
    Example: "STU-001:2025-11-10"
    
    Args:
        recommendation_id: Composite recommendation identifier
        
    Returns:
        Tuple of (student_id, recommendation_date)
        
    Raises:
        HTTPException: If ID format is invalid
    """
    parts = recommendation_id.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_validation_error_response(
                message="Recommendation ID must be in format: STU-XXX:YYYY-MM-DD",
                request_id=None,
                field="recommendation_id",
                recommendation_id=recommendation_id,
            ),
        )
    
    student_id, recommendation_date = parts
    
    # Validate student ID format
    validate_student_id(student_id)
    
    # Validate date format (basic check)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", recommendation_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_validation_error_response(
                message="Recommendation date must be in format: YYYY-MM-DD",
                request_id=None,
                field="recommendation_date",
                recommendation_id=recommendation_id,
            ),
        )
    
    return student_id, recommendation_date


def vocabulary_recommendation_to_response(
    recommendation: VocabularyRecommendation,
) -> RecommendationsResponse:
    """Convert VocabularyRecommendation model to API response.
    
    Args:
        recommendation: VocabularyRecommendation instance
        
    Returns:
        RecommendationsResponse instance
    """
    return RecommendationsResponse(
        student_id=recommendation.student_id,
        recommendation_date=recommendation.recommendation_date,
        words=[
            RecommendationWordResponse(
                word=word.word,
                definition=word.definition,
                grade_level=word.grade_level,
                difficulty_score=word.difficulty_score,
                rationale=word.rationale,
                example_sentences=word.example_sentences,
            )
            for word in recommendation.words
        ],
        status=recommendation.status.value,
    )


@router.get(
    "/students/{student_id}/recommendations",
    response_model=RecommendationsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student recommendations",
    description="Retrieve all vocabulary recommendations for a student, ordered by date (newest first).",
)
async def get_student_recommendations(
    student_id: Annotated[str, Path(..., description="Student identifier (format: STU-XXX)")],
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
    recommendation_repo: Annotated[
        RecommendationRepository, Depends(get_recommendation_repository)
    ],
) -> RecommendationsListResponse:
    """Get all vocabulary recommendations for a student.
    
    Args:
        student_id: Student identifier (validated format: STU-XXX)
        student_repo: Student repository dependency
        recommendation_repo: Recommendation repository dependency
        
    Returns:
        RecommendationsListResponse with list of recommendations
        
    Raises:
        HTTPException: If student not found or query fails
    """
    request_id = str(uuid4())
    
    try:
        # Validate student ID format
        validate_student_id(student_id)
        
        logger.info(
            "Retrieving student recommendations",
            extra={"student_id": student_id, "request_id": request_id},
        )
        
        # Verify student exists
        profile = student_repo.get(student_id)
        if not profile:
            logger.warning(
                f"Student profile not found: {student_id}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_not_found_error_response(
                    resource_type="student",
                    resource_id=student_id,
                    request_id=request_id,
                ),
            )
        
        # Get recommendations from repository (sync method)
        recommendations = recommendation_repo.get_by_student(student_id)
        
        # Convert to response format
        recommendation_responses = [
            vocabulary_recommendation_to_response(rec) for rec in recommendations
        ]
        
        logger.debug(
            f"Retrieved {len(recommendation_responses)} recommendations for {student_id}",
            extra={"request_id": request_id},
        )
        
        return RecommendationsListResponse(
            recommendations=recommendation_responses,
            total=len(recommendation_responses),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving student recommendations: {e}",
            extra={"student_id": student_id, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to retrieve student recommendations",
                request_id=request_id,
            ),
        ) from e


@router.patch(
    "/recommendations/{recommendation_id}/status",
    response_model=RecommendationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Update recommendation status",
    description="Update the status of a vocabulary recommendation (pending, assigned, learned).",
)
async def update_recommendation_status(
    recommendation_id: Annotated[
        str, Path(..., description="Recommendation identifier (format: STU-XXX:YYYY-MM-DD)")
    ],
    request: UpdateRecommendationStatusRequest,
    recommendation_repo: Annotated[
        RecommendationRepository, Depends(get_recommendation_repository)
    ],
) -> RecommendationStatusResponse:
    """Update the status of a vocabulary recommendation.
    
    Args:
        recommendation_id: Composite recommendation identifier (format: STU-XXX:YYYY-MM-DD)
        request: Update request with new status
        recommendation_repo: Recommendation repository dependency
        
    Returns:
        RecommendationStatusResponse with updated status
        
    Raises:
        HTTPException: If recommendation not found or update fails
    """
    request_id = str(uuid4())
    
    try:
        # Parse recommendation ID
        student_id, recommendation_date = parse_recommendation_id(recommendation_id)
        
        logger.info(
            "Updating recommendation status",
            extra={
                "student_id": student_id,
                "recommendation_date": recommendation_date,
                "new_status": request.status,
                "request_id": request_id,
            },
        )
        
        # Convert status string to enum
        try:
            new_status = RecommendationStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_validation_error_response(
                    message=f"Invalid status: {request.status}. Must be one of: pending, assigned, learned",
                    request_id=request_id,
                    field="status",
                    status=request.status,
                ),
            )
        
        # Update status (sync method)
        updated_recommendation = recommendation_repo.update_status(
            student_id=student_id,
            recommendation_date=recommendation_date,
            status=new_status,
        )
        
        if not updated_recommendation:
            logger.warning(
                f"Recommendation not found: {recommendation_id}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_not_found_error_response(
                    resource_type="recommendation",
                    resource_id=recommendation_id,
                    request_id=request_id,
                ),
            )
        
        logger.info(
            f"Updated recommendation status: {recommendation_id} -> {request.status}",
            extra={"request_id": request_id},
        )
        
        return RecommendationStatusResponse(
            success=True,
            recommendation_id=recommendation_id,
            status=updated_recommendation.status.value,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating recommendation status: {e}",
            extra={"recommendation_id": recommendation_id, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to update recommendation status",
                request_id=request_id,
            ),
        ) from e

