"""Batch processing endpoints.

This module provides endpoints for submitting and tracking batch processing jobs.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.api.dependencies import get_batch_client
from src.api.models.requests import BatchProcessRequest
from src.api.models.responses import BatchProcessResponse, BatchStatusResponse
from src.api.utils.errors import (
    create_internal_error_response,
    create_not_found_error_response,
    create_validation_error_response,
)
from src.processing.batch_client import BatchClient, BatchJobStatus
from src.utils.logger import get_logger

logger = get_logger("api.routes.batch")

router = APIRouter()


@router.post(
    "/batch/process",
    response_model=BatchProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit batch processing job",
    description="Submit a batch processing job to process multiple student transcripts in parallel.",
)
async def submit_batch_job(
    request: BatchProcessRequest,
    batch_client: Annotated[BatchClient, Depends(get_batch_client)],
) -> BatchProcessResponse:
    """Submit a batch processing job.
    
    Args:
        request: Batch processing request with student IDs and S3 paths
        batch_client: Batch client dependency
        
    Returns:
        BatchProcessResponse with job ID
        
    Raises:
        HTTPException: If job submission fails
    """
    request_id = str(uuid4())
    
    try:
        logger.info(
            "Submitting batch processing job",
            extra={
                "student_count": len(request.student_ids),
                "grade_level": request.grade_level,
                "request_id": request_id,
            },
        )
        
        # Convert s3_paths list to dict mapping student_id to path
        # The request has parallel lists, but BatchClient expects a dict
        s3_paths_dict = {
            student_id: s3_path
            for student_id, s3_path in zip(request.student_ids, request.s3_paths)
        }
        
        # Prepare job configuration
        job_config = {
            "student_ids": request.student_ids,
            "s3_paths": s3_paths_dict,
            "grade_level": request.grade_level,
        }
        
        # Submit job (sync method)
        job_id = batch_client.submit_job(
            job_name="vocabulator-batch-process",
            job_config=job_config,
            request_id=request_id,
        )
        
        logger.info(
            f"Batch job submitted successfully: {job_id}",
            extra={
                "job_id": job_id,
                "student_count": len(request.student_ids),
                "request_id": request_id,
            },
        )
        
        return BatchProcessResponse(
            success=True,
            job_id=job_id,
            message=f"Batch job submitted successfully for {len(request.student_ids)} students",
        )
        
    except ValueError as e:
        # Invalid request parameters (e.g., invalid resource requirements)
        logger.warning(
            f"Invalid batch job request: {e}",
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_validation_error_response(
                message=f"Invalid batch job request: {str(e)}",
                request_id=request_id,
                field="batch_configuration",
            ),
        ) from e
    except Exception as e:
        logger.error(
            f"Error submitting batch job: {e}",
            extra={"request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to submit batch job",
                request_id=request_id,
            ),
        ) from e


@router.get(
    "/batch/{job_id}/status",
    response_model=BatchStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get batch job status",
    description="Retrieve the current status of a batch processing job.",
)
async def get_batch_status(
    job_id: Annotated[str, Path(..., description="AWS Batch job ID")],
    batch_client: Annotated[BatchClient, Depends(get_batch_client)],
) -> BatchStatusResponse:
    """Get the status of a batch processing job.
    
    Args:
        job_id: AWS Batch job ID
        batch_client: Batch client dependency
        
    Returns:
        BatchStatusResponse with job status and details
        
    Raises:
        HTTPException: If job not found or status retrieval fails
    """
    request_id = str(uuid4())
    
    try:
        logger.debug(
            "Retrieving batch job status",
            extra={"job_id": job_id, "request_id": request_id},
        )
        
        # Get job status (sync method)
        job_info = batch_client.get_job_status(job_id)
        
        if not job_info:
            logger.warning(
                f"Batch job not found: {job_id}",
                extra={"request_id": request_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_not_found_error_response(
                    resource_type="batch_job",
                    resource_id=job_id,
                    request_id=request_id,
                ),
            )
        
        # Calculate progress based on status
        progress = None
        if job_info.status == BatchJobStatus.SUCCEEDED:
            progress = 100
        elif job_info.status == BatchJobStatus.FAILED:
            progress = 0
        elif job_info.status == BatchJobStatus.RUNNING:
            # Estimate progress based on time elapsed (rough estimate)
            if job_info.started_at:
                from datetime import datetime, timezone
                # Assume 15 minutes average job duration
                elapsed = (datetime.now(timezone.utc) - job_info.started_at).total_seconds()
                estimated_duration = 15 * 60  # 15 minutes
                progress = min(int((elapsed / estimated_duration) * 100), 95)
            else:
                progress = 10  # Just started
        
        logger.debug(
            f"Retrieved batch job status: {job_id} -> {job_info.status.value}",
            extra={"request_id": request_id},
        )
        
        return BatchStatusResponse(
            job_id=job_info.job_id,
            status=job_info.status.value,
            created_at=job_info.created_at,
            started_at=job_info.started_at,
            stopped_at=job_info.stopped_at,
            progress=progress,
            error_message=job_info.status_reason,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving batch job status: {e}",
            extra={"job_id": job_id, "request_id": request_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_internal_error_response(
                message="Failed to retrieve batch job status",
                request_id=request_id,
            ),
        ) from e

