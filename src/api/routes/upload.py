"""Upload endpoints for transcripts and writing samples.

This module provides endpoints for uploading student transcripts and writing samples,
processing them through the vocabulary extraction pipeline, and storing results.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import (
    get_s3_client,
    get_student_repository,
    get_text_processing_pipeline,
)
from src.api.models.requests import TranscriptUploadRequest, WritingUploadRequest
from src.api.models.responses import (
    TranscriptUploadResponse,
    WritingUploadResponse,
)
from src.api.utils.errors import (
    create_error_response,
    create_internal_error_response,
    create_not_found_error_response,
)
from src.api.utils.s3_paths import (
    build_s3_path,
    format_date_for_path,
    format_datetime_for_path,
)
from src.data.repositories.student_repository import StudentRepository
from src.data.s3_client import S3Client, S3Error
from src.processing.text_processing_pipeline import TextProcessingPipeline
from src.utils.logger import get_logger

logger = get_logger("api.routes.upload")

router = APIRouter()


@router.post(
    "/transcripts/upload",
    response_model=TranscriptUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload student transcript",
    description="Upload a student transcript, extract vocabulary, and update student profile.",
)
async def upload_transcript(
    request: TranscriptUploadRequest,
    pipeline: Annotated[TextProcessingPipeline, Depends(get_text_processing_pipeline)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> TranscriptUploadResponse:
    """Upload and process a student transcript.
    
    This endpoint:
    1. Validates the request
    2. Verifies student profile exists (returns 404 if not found)
    3. Stores the raw transcript in S3
    4. Processes the transcript through the vocabulary extraction pipeline
    5. Updates the student profile with extracted vocabulary
    6. Generates vocabulary recommendations
    
    Args:
        request: Transcript upload request with student_id, text, session_date, grade_level
        pipeline: Text processing pipeline dependency
        s3_client: S3 client dependency
        student_repo: Student repository dependency
        
    Returns:
        TranscriptUploadResponse with success status and words extracted count
        
    Raises:
        HTTPException: If upload or processing fails
    """
    request_id = str(uuid4())
    
    try:
        logger.info(
            "Processing transcript upload",
            extra={
                "student_id": request.student_id,
                "session_date": str(request.session_date),
                "text_length": len(request.text),
                "request_id": request_id,
            },
        )
        
        # Step 1: Verify student profile exists before proceeding
        profile = student_repo.get(request.student_id)
        if not profile:
            logger.warning(
                f"Student profile not found for transcript upload: {request.student_id}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_not_found_error_response(
                    resource_type="student",
                    resource_id=request.student_id,
                    request_id=request_id,
                ),
            )
        
        # Step 2: Store raw transcript in S3
        s3_key = build_s3_path(
            "transcripts",
            "raw",
            request.student_id,
            format_date_for_path(request.session_date),
            extension="txt",
        )
        try:
            s3_client.upload(
                key=s3_key,
                content=request.text.encode("utf-8"),
                content_type="text/plain",
                metadata={
                    "student_id": request.student_id,
                    "session_date": request.session_date.isoformat(),
                    "grade_level": str(request.grade_level),
                },
            )
            logger.debug(f"Stored transcript in S3: {s3_key}", extra={"request_id": request_id})
        except S3Error as e:
            logger.error(
                f"Failed to store transcript in S3: {e}",
                extra={"request_id": request_id, "s3_key": s3_key},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="s3_upload_failed",
                    message="Failed to store transcript in S3",
                    request_id=request_id,
                    s3_key=s3_key,
                ),
            ) from e
        
        # Step 3: Process transcript through pipeline
        try:
            recommendation = await pipeline.process_text(
                text=request.text,
                student_id=request.student_id,
                grade_level=request.grade_level,
                request_id=request_id,
            )
            
            # Get updated profile to calculate words_extracted (sync method)
            profile = student_repo.get(request.student_id)
            words_extracted = len(profile.vocabulary_list) if profile else 0
            
            logger.info(
                "Transcript processed successfully",
                extra={
                    "student_id": request.student_id,
                    "words_extracted": words_extracted,
                    "request_id": request_id,
                },
            )
            
            # Step 4: Generate profile URL
            profile_url = f"/api/v1/students/{request.student_id}/profile"
            
            return TranscriptUploadResponse(
                success=True,
                student_id=request.student_id,
                words_extracted=words_extracted,
                profile_url=profile_url,
            )
            
        except ValueError as e:
            logger.error(
                f"Validation error processing transcript: {e}",
                extra={"request_id": request_id, "student_id": request.student_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    error_code="validation_error",
                    message=str(e),
                    request_id=request_id,
                    student_id=request.student_id,
                ),
            ) from e
        except Exception as e:
            logger.error(
                f"Error processing transcript: {e}",
                extra={"request_id": request_id, "student_id": request.student_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="processing_error",
                    message="Failed to process transcript",
                    request_id=request_id,
                    student_id=request.student_id,
                ),
            ) from e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in transcript upload: {e}",
            extra={"request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="An unexpected error occurred",
                request_id=request_id,
            ),
        ) from e


@router.post(
    "/writing/upload",
    response_model=WritingUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload writing sample",
    description="Upload a student writing sample, extract vocabulary, and update student profile.",
)
async def upload_writing(
    request: WritingUploadRequest,
    pipeline: Annotated[TextProcessingPipeline, Depends(get_text_processing_pipeline)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    student_repo: Annotated[StudentRepository, Depends(get_student_repository)],
) -> WritingUploadResponse:
    """Upload and process a student writing sample.
    
    This endpoint:
    1. Validates the request
    2. Verifies student profile exists (returns 404 if not found)
    3. Stores the raw writing sample in S3
    4. Processes the writing sample through the vocabulary extraction pipeline
    5. Updates the student profile with extracted vocabulary
    6. Generates vocabulary recommendations
    
    Args:
        request: Writing upload request with student_id, text, assignment_id (optional), grade_level
        pipeline: Text processing pipeline dependency
        s3_client: S3 client dependency
        student_repo: Student repository dependency
        
    Returns:
        WritingUploadResponse with success status and words extracted count
        
    Raises:
        HTTPException: If upload or processing fails
    """
    request_id = str(uuid4())
    
    try:
        logger.info(
            "Processing writing sample upload",
            extra={
                "student_id": request.student_id,
                "assignment_id": request.assignment_id,
                "text_length": len(request.text),
                "request_id": request_id,
            },
        )
        
        # Step 1: Verify student profile exists before proceeding
        profile = student_repo.get(request.student_id)
        if not profile:
            logger.warning(
                f"Student profile not found for writing upload: {request.student_id}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_not_found_error_response(
                    resource_type="student",
                    resource_id=request.student_id,
                    request_id=request_id,
                ),
            )
        
        # Step 2: Store raw writing sample in S3
        assignment_id = request.assignment_id or f"writing-{format_datetime_for_path(datetime.now(timezone.utc), include_time=True)}"
        s3_key = build_s3_path(
            "writing-samples",
            "raw",
            request.student_id,
            assignment_id,
            extension="txt",
        )
        
        try:
            s3_client.upload(
                key=s3_key,
                content=request.text.encode("utf-8"),
                content_type="text/plain",
                metadata={
                    "student_id": request.student_id,
                    "assignment_id": assignment_id,
                    "grade_level": str(request.grade_level),
                },
            )
            logger.debug(f"Stored writing sample in S3: {s3_key}", extra={"request_id": request_id})
        except S3Error as e:
            logger.error(
                f"Failed to store writing sample in S3: {e}",
                extra={"request_id": request_id, "s3_key": s3_key},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="s3_upload_failed",
                    message="Failed to store writing sample in S3",
                    request_id=request_id,
                    s3_key=s3_key,
                ),
            ) from e
        
        # Step 3: Process writing sample through pipeline
        try:
            recommendation = await pipeline.process_text(
                text=request.text,
                student_id=request.student_id,
                grade_level=request.grade_level,
                request_id=request_id,
            )
            
            # Get updated profile to calculate words_extracted
            profile = student_repo.get(request.student_id)
            words_extracted = len(profile.vocabulary_list) if profile else 0
            
            logger.info(
                "Writing sample processed successfully",
                extra={
                    "student_id": request.student_id,
                    "words_extracted": words_extracted,
                    "request_id": request_id,
                },
            )
            
            return WritingUploadResponse(
                success=True,
                student_id=request.student_id,
                words_extracted=words_extracted,
                assignment_id=request.assignment_id,
            )
            
        except ValueError as e:
            logger.error(
                f"Validation error processing writing sample: {e}",
                extra={"request_id": request_id, "student_id": request.student_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    error_code="validation_error",
                    message=str(e),
                    request_id=request_id,
                    student_id=request.student_id,
                ),
            ) from e
        except Exception as e:
            logger.error(
                f"Error processing writing sample: {e}",
                extra={"request_id": request_id, "student_id": request.student_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    error_code="processing_error",
                    message="Failed to process writing sample",
                    request_id=request_id,
                    student_id=request.student_id,
                ),
            ) from e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in writing upload: {e}",
            extra={"request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="An unexpected error occurred",
                request_id=request_id,
            ),
        ) from e
