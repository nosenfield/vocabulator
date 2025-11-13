"""Mock endpoints for dashboard demonstration.

This module provides mock endpoints that simulate Google Classroom integration
and other features for dashboard demonstration purposes.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_student_repository
from src.api.utils.errors import (
    create_error_response,
    create_internal_error_response,
)
from src.data.repositories.student_repository import StudentRepository
from src.utils.logger import get_logger

logger = get_logger("api.routes.mock")

router = APIRouter()

# Constants
MOCK_STUDENT_COUNT = 18  # Expected number of mock students (STU-001 to STU-018)


@router.post(
    "/mock/sync-google-classroom",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Simulate Google Classroom student sync",
    description="Simulate syncing students from Google Classroom. In reality, would call Google Classroom API. For demo, runs the seeding script to populate mock students.",
)
async def sync_google_classroom(
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> dict:
    """Simulate syncing students from Google Classroom.
    
    This endpoint simulates the Google Classroom sync process. In a real
    implementation, this would:
    1. Authenticate with Google Classroom API
    2. Fetch class rosters
    3. Create/update student profiles
    
    For the demo, this endpoint:
    1. Checks if mock students already exist
    2. If not, runs the seeding script to create mock students
    3. Returns count of students synced
    
    Returns:
        Dictionary with sync status and student count
        
    Raises:
        HTTPException: If sync fails
    """
    request_id = str(uuid4())
    
    try:
        # Always run seeding to ensure all mock students exist with correct metadata
        # This ensures class information is set even if students already exist
        
        # Import and call the seeding function directly (safer than subprocess)
        try:
            from scripts.seed_mock_dashboard_data import seed_students
            
            # Execute the seeding function
            seed_students()
            
            # Count students after seeding
            student_count = 0
            for i in range(1, MOCK_STUDENT_COUNT + 1):
                try:
                    student = student_repo.get(f"STU-{i:03d}")
                    if student:
                        student_count += 1
                except Exception:
                    pass
            
            logger.info(
                f"Successfully synced {student_count} mock students",
                extra={"request_id": request_id, "students_count": student_count},
            )
            
            return {
                "success": True,
                "message": f"Successfully synced {student_count} students from Google Classroom (mock).",
                "students_count": student_count,
                "new_students_added": student_count,
                "request_id": request_id,
            }
            
        except ImportError as e:
            logger.error(
                f"Failed to import seeding function: {e}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="sync_import_failed",
                    message="Failed to import seeding function",
                    request_id=request_id,
                ),
            ) from e
        except Exception as e:
            logger.error(
                f"Error running seeding function: {e}",
                extra={"request_id": request_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="sync_error",
                    message=f"Failed to sync students: {str(e)}",
                    request_id=request_id,
                ),
            ) from e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in Google Classroom sync: {e}",
            extra={"request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="An unexpected error occurred during sync",
                request_id=request_id,
            ),
        ) from e


@router.delete(
    "/mock/clear-students",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Clear all mock students",
    description="Delete all mock students (STU-001 to STU-018) from the database. Useful for redemonstrating the Google Classroom sync.",
)
async def clear_mock_students(
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> dict:
    """Clear all mock students from the database.
    
    This endpoint deletes all mock students (STU-001 to STU-018) to allow
    redemonstrating the Google Classroom sync functionality.
    
    Returns:
        Dictionary with deletion status and count
        
    Raises:
        HTTPException: If deletion fails
    """
    request_id = str(uuid4())
    
    try:
        deleted_count = 0
        errors = []
        
        # Delete all mock students (STU-001 to STU-018)
        for i in range(1, MOCK_STUDENT_COUNT + 1):
            student_id = f"STU-{i:03d}"
            try:
                # Get the student to find profile_version
                student = student_repo.get(student_id)
                if student:
                    # Delete using profile_version (default is 1)
                    student_repo.delete(student_id, student.profile_version)
                    deleted_count += 1
                    logger.debug(
                        f"Deleted student {student_id}",
                        extra={"request_id": request_id, "student_id": student_id},
                    )
            except Exception as e:
                error_msg = f"Failed to delete {student_id}: {str(e)}"
                errors.append(error_msg)
                logger.warning(
                    error_msg,
                    extra={"request_id": request_id, "student_id": student_id},
                )
        
        # Also delete any other students that might exist (STU-973, STU-719, STU-783, STU-999, etc.)
        # These are from previous test runs or accidentally created
        # Query by student_id to find all profile versions and delete them all
        extra_student_ids = ["STU-973", "STU-719", "STU-783", "STU-999"]
        for student_id in extra_student_ids:
            try:
                # Query all profile versions for this student_id
                # Query by partition key (student_id) to get all versions
                # Use the repository's query method which handles the partition key correctly
                profiles = student_repo.query(
                    partition_value=student_id,
                )
                
                if profiles:
                    # Delete all versions found
                    for profile in profiles:
                        profile_version = profile.profile_version if hasattr(profile, 'profile_version') else 1
                        try:
                            student_repo.delete(student_id, profile_version=profile_version)
                            deleted_count += 1
                            logger.debug(
                                f"Deleted extra student {student_id} v{profile_version}",
                                extra={"request_id": request_id, "student_id": student_id, "profile_version": profile_version},
                            )
                        except Exception as delete_error:
                            logger.warning(
                                f"Failed to delete {student_id} v{profile_version}: {delete_error}",
                                extra={"request_id": request_id, "student_id": student_id, "profile_version": profile_version},
                            )
                else:
                    # If query returns nothing, try direct delete with version 1 as fallback
                    try:
                        student_repo.delete(student_id, profile_version=1)
                        deleted_count += 1
                        logger.debug(
                            f"Deleted extra student {student_id} (fallback delete)",
                            extra={"request_id": request_id, "student_id": student_id},
                        )
                    except Exception:
                        logger.debug(
                            f"Extra student {student_id} does not exist, skipping",
                            extra={"request_id": request_id, "student_id": student_id},
                        )
            except Exception as e:
                # If query fails, try direct delete as last resort
                try:
                    student_repo.delete(student_id, profile_version=1)
                    deleted_count += 1
                    logger.debug(
                        f"Deleted extra student {student_id} (exception fallback)",
                        extra={"request_id": request_id, "student_id": student_id},
                    )
                except Exception as delete_error:
                    logger.debug(
                        f"Could not delete extra student {student_id}: {delete_error}",
                        extra={"request_id": request_id, "student_id": student_id},
                    )
                pass
        
        logger.info(
            f"Cleared {deleted_count} students",
            extra={"request_id": request_id, "deleted_count": deleted_count},
        )
        
        response = {
            "success": True,
            "message": f"Successfully cleared {deleted_count} students.",
            "deleted_count": deleted_count,
            "request_id": request_id,
        }
        
        if errors:
            response["errors"] = errors
            response["message"] += f" {len(errors)} errors occurred."
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error clearing students: {e}",
            extra={"request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="An unexpected error occurred while clearing students",
                request_id=request_id,
            ),
        ) from e

