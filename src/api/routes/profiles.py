"""Student profile endpoints.

This module provides CRUD endpoints for student profiles.
"""

from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.api.dependencies import get_student_repository
from src.api.models.requests import CreateStudentRequest, UpdateStudentRequest
from src.api.models.responses import (
    StudentProfileResponse,
    StudentListItem,
    StudentsListResponse,
)
from src.api.utils.errors import (
    create_conflict_error_response,
    create_error_response,
    create_internal_error_response,
    create_not_found_error_response,
    create_validation_error_response,
)
from src.api.utils.validation import validate_student_id as validate_student_id_format
from src.data.models.student_profile import StudentProfile
from src.data.repositories.student_repository import StudentRepository
from src.utils.logger import get_logger

logger = get_logger("api.routes.profiles")

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


@router.get(
    "/students/{student_id}/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student profile",
    description="Retrieve a student's vocabulary profile including vocabulary size and proficiency score.",
)
async def get_student_profile(
    student_id: Annotated[str, Path(..., description="Student identifier (format: STU-XXX)")],
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> StudentProfileResponse:
    """Get a student's vocabulary profile.
    
    Args:
        student_id: Student identifier (validated format: STU-XXX)
        student_repo: Student repository dependency
        
    Returns:
        StudentProfileResponse with profile data
        
    Raises:
        HTTPException: If student not found or invalid ID format
    """
    request_id = str(uuid4())
    
    try:
        # Validate student ID format
        validate_student_id(student_id)
        
        logger.info(
            "Retrieving student profile",
            extra={"student_id": student_id, "request_id": request_id},
        )
        
        # Get profile from repository (sync method)
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
        
        logger.debug(
            f"Retrieved profile for {student_id}",
            extra={
                "vocabulary_size": len(profile.vocabulary_list),
                "proficiency_score": profile.proficiency_score,
                "request_id": request_id,
            },
        )
        
        return StudentProfileResponse(
            student_id=profile.student_id,
            grade_level=profile.grade_level,
            vocabulary_size=len(profile.vocabulary_list),
            proficiency_score=profile.proficiency_score,
            created_at=profile.created_at,
            last_updated=profile.last_updated,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving student profile: {e}",
            extra={"student_id": student_id, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to retrieve student profile",
                request_id=request_id,
            ),
        ) from e


@router.get(
    "/students",
    response_model=StudentsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List students",
    description="List all students, optionally filtered by grade level.",
)
async def list_students(
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
    grade_level: Annotated[
        Optional[int],
        Query(
            ge=6,
            le=8,
            description="Filter by grade level (6-8)",
        ),
    ] = None,
) -> StudentsListResponse:
    """List students with optional grade level filter.
    
    Args:
        grade_level: Optional grade level filter (6-8)
        student_repo: Student repository dependency
        
    Returns:
        StudentsListResponse with list of students and total count
        
    Raises:
        HTTPException: If query fails
    """
    request_id = str(uuid4())
    
    try:
        logger.info(
            "Listing students",
            extra={"grade_level": grade_level, "request_id": request_id},
        )
        
        # Get students from repository (sync method)
        if grade_level:
            profiles = student_repo.list_by_grade_level(grade_level)
        else:
            # If no grade filter, query all grade levels (6, 7, 8) and combine results
            # Note: This makes 3 separate GSI queries. For post-MVP, consider implementing
            # a more efficient list_all() method using a single scan operation.
            all_profiles = []
            for grade in [6, 7, 8]:
                grade_profiles = student_repo.list_by_grade_level(grade)
                logger.debug(
                    f"Found {len(grade_profiles)} students in grade {grade}",
                    extra={"grade_level": grade, "request_id": request_id},
                )
                all_profiles.extend(grade_profiles)
            profiles = all_profiles
        
        # Convert to response items
        students = []
        for profile in profiles:
            # Debug: Log metadata for first few students
            if len(students) < 3:
                logger.info(
                    f"Processing profile {profile.student_id}: metadata={profile.metadata}, has_metadata={hasattr(profile, 'metadata')}, class={profile.metadata.get('class') if profile.metadata else None}",
                    extra={"student_id": profile.student_id, "metadata": profile.metadata},
                )
            
            class_value = profile.metadata.get("class") if profile.metadata else None
            students.append(
            StudentListItem(
                student_id=profile.student_id,
                grade_level=profile.grade_level,
                vocabulary_size=len(profile.vocabulary_list),
                proficiency_score=profile.proficiency_score,
                    class_id=class_value,
                )
            )
        
        logger.debug(
            f"Retrieved {len(students)} students",
            extra={"grade_level": grade_level, "request_id": request_id},
        )
        
        return StudentsListResponse(students=students, total=len(students))
        
    except Exception as e:
        logger.error(
            f"Error listing students: {e}",
            extra={"grade_level": grade_level, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to list students",
                request_id=request_id,
            ),
        ) from e


@router.post(
    "/students",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student profile",
    description="Create a new student vocabulary profile.",
)
async def create_student(
    request: CreateStudentRequest,
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> StudentProfileResponse:
    """Create a new student profile.
    
    Args:
        request: Create student request with student_id and grade_level
        student_repo: Student repository dependency
        
    Returns:
        StudentProfileResponse with created profile data
        
    Raises:
        HTTPException: If creation fails or student already exists
    """
    request_id = str(uuid4())
    
    try:
        logger.info(
            "Creating student profile",
            extra={
                "student_id": request.student_id,
                "grade_level": request.grade_level,
                "request_id": request_id,
            },
        )
        
        # Validate student ID format first (before checking existence)
        validate_student_id(request.student_id)
        
        # Check if student already exists (sync method)
        existing = student_repo.get(request.student_id)
        if existing:
            logger.warning(
                f"Student profile already exists: {request.student_id}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=create_conflict_error_response(
                    resource_type="student",
                    resource_id=request.student_id,
                    reason="Profile already exists",
                    request_id=request_id,
                ),
            )
        
        # Create new profile
        profile = StudentProfile(
            student_id=request.student_id,
            grade_level=request.grade_level,
            vocabulary_list=[],
            proficiency_score=0.0,
        )
        
        created_profile = student_repo.create(profile)
        
        logger.info(
            f"Created student profile: {request.student_id}",
            extra={"request_id": request_id},
        )
        
        return StudentProfileResponse(
            student_id=created_profile.student_id,
            grade_level=created_profile.grade_level,
            vocabulary_size=len(created_profile.vocabulary_list),
            proficiency_score=created_profile.proficiency_score,
            created_at=created_profile.created_at,
            last_updated=created_profile.last_updated,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating student profile: {e}",
            extra={"student_id": request.student_id, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to create student profile",
                request_id=request_id,
            ),
        ) from e


@router.put(
    "/students/{student_id}",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student profile",
    description="Update an existing student profile (partial updates supported).",
)
async def update_student(
    student_id: Annotated[str, Path(..., description="Student identifier (format: STU-XXX)")],
    request: UpdateStudentRequest,
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> StudentProfileResponse:
    """Update an existing student profile.
    
    Supports partial updates - only provided fields are updated.
    
    Args:
        student_id: Student identifier (validated format: STU-XXX)
        request: Update request with fields to update
        student_repo: Student repository dependency
        
    Returns:
        StudentProfileResponse with updated profile data
        
    Raises:
        HTTPException: If student not found or update fails
    """
    request_id = str(uuid4())
    
    try:
        # Validate student ID format
        validate_student_id(student_id)
        
        logger.info(
            "Updating student profile",
            extra={
                "student_id": student_id,
                "updates": request.model_dump(exclude_unset=True),
                "request_id": request_id,
            },
        )
        
        # Get existing profile (sync method)
        profile = student_repo.get(student_id)
        if not profile:
            logger.warning(
                f"Student profile not found for update: {student_id}",
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
        
        # Apply updates
        if request.grade_level is not None:
            profile.grade_level = request.grade_level
        
        # Update profile (repository will recalculate proficiency score) (sync method)
        updated_profile = student_repo.update(profile)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="update_failed",
                    message="Failed to update student profile",
                    request_id=request_id,
                    student_id=student_id,
                ),
            )
        
        logger.info(
            f"Updated student profile: {student_id}",
            extra={"request_id": request_id},
        )
        
        return StudentProfileResponse(
            student_id=updated_profile.student_id,
            grade_level=updated_profile.grade_level,
            vocabulary_size=len(updated_profile.vocabulary_list),
            proficiency_score=updated_profile.proficiency_score,
            created_at=updated_profile.created_at,
            last_updated=updated_profile.last_updated,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating student profile: {e}",
            extra={"student_id": student_id, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to update student profile",
                request_id=request_id,
            ),
        ) from e

