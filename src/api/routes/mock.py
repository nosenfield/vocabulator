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
        # Check if students already exist by trying to get a known student ID
        # If STU-001 exists, assume students are already seeded
        try:
            existing_student = student_repo.get("STU-001")
            if existing_student:
                # Count students by checking known mock student IDs
                student_count = 0
                for i in range(1, MOCK_STUDENT_COUNT + 1):
                    try:
                        student = student_repo.get(f"STU-{i:03d}")
                        if student:
                            student_count += 1
                    except Exception:
                        pass
                
                logger.info(
                    f"Mock students already exist ({student_count} found)",
                    extra={"request_id": request_id},
                )
                return {
                    "success": True,
                    "message": f"Students already synced. Found {student_count} students.",
                    "students_count": student_count,
                    "new_students_added": 0,
                    "request_id": request_id,
                }
        except Exception:
            # STU-001 doesn't exist, proceed with seeding
            pass
        
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

