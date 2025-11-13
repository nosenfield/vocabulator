"""AWS Batch client wrapper for job submission and status tracking.

This module provides a high-level interface for AWS Batch operations including
job submission, status tracking, and job management.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("processing.batch_client")


class BatchJobStatus(str, Enum):
    """AWS Batch job status values."""

    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNABLE = "RUNNABLE"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class BatchJobError(Exception):
    """Base exception for AWS Batch operations."""

    pass


@dataclass
class BatchJobInfo:
    """Information about a batch job."""

    job_id: str
    job_name: str
    status: BatchJobStatus
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    status_reason: Optional[str] = None


class BatchClient:
    """AWS Batch client wrapper for job management.

    Provides high-level interface for submitting jobs, tracking status,
    and managing batch processing workflows.
    """

    def __init__(
        self,
        job_queue: Optional[str] = None,
        job_definition: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """Initialize Batch client.

        Args:
            job_queue: Name of the Batch job queue (uses config if None)
            job_definition: Name of the Batch job definition (uses config if None)
            region: AWS region (uses config if None)
        """
        config = get_config()

        # Use provided values or config values (fail fast if neither provided)
        self.job_queue = job_queue or getattr(config, "batch_job_queue", None)
        self.job_definition = job_definition or getattr(config, "batch_job_definition", None)

        if not self.job_queue:
            raise ValueError(
                "job_queue must be provided or configured in config.batch_job_queue"
            )
        if not self.job_definition:
            raise ValueError(
                "job_definition must be provided or configured in config.batch_job_definition"
            )

        # Configure boto3 with retry logic
        aws_region = region or config.aws_region
        boto_config = Config(
            retries={
                "max_attempts": 3,
                "mode": "adaptive",
            },
        )

        # Create Batch client
        # Note: AWS Batch doesn't support LocalStack, so we always use production client
        self.client = boto3.client("batch", config=boto_config, region_name=aws_region)

        logger.debug(
            f"Initialized BatchClient",
            extra={
                "job_queue": self.job_queue,
                "job_definition": self.job_definition,
                "region": region or config.aws_region,
            },
        )

    def submit_job(
        self,
        job_name: str,
        job_config: Dict,
        request_id: Optional[str] = None,
        timeout: int = 1800,  # 30 minutes default
        memory: int = 4096,  # 4GB default
        vcpus: int = 2,  # 2 vCPUs default
    ) -> str:
        """Submit a batch job for processing.

        Args:
            job_name: Name for the job (will be prefixed with timestamp)
            job_config: Job configuration dictionary containing:
                - student_ids: List of student IDs to process
                - s3_paths: Dict mapping student_id to S3 path
                - grade_level: Optional grade level
            request_id: Optional request ID for correlation
            timeout: Job timeout in seconds (default: 1800 = 30 minutes)
            memory: Memory requirement in MB (default: 4096 = 4GB, must be 512-30720)
            vcpus: vCPU requirement (default: 2, must be 0.25-4)

        Returns:
            Job ID string

        Raises:
            BatchJobError: If job submission fails
            ValueError: If resource requirements are invalid
        """
        # Validate resource requirements (AWS Fargate limits)
        if memory < 512 or memory > 30720:
            raise ValueError(
                f"Invalid memory: {memory} MB (must be 512-30720 MB for Fargate)"
            )
        if vcpus < 0.25 or vcpus > 4:
            raise ValueError(
                f"Invalid vCPUs: {vcpus} (must be 0.25-4 for Fargate)"
            )

        # Generate unique job name with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        unique_job_name = f"{job_name}-{timestamp}"

        logger.info(
            f"Submitting batch job",
            extra={
                "job_name": unique_job_name,
                "job_queue": self.job_queue,
                "job_definition": self.job_definition,
                "student_count": len(job_config.get("student_ids", [])),
                "request_id": request_id,
            },
        )

        # Prepare job parameters (passed as JSON string)
        parameters = {
            "job_config": json.dumps(job_config),
        }
        if request_id:
            parameters["request_id"] = request_id

        # Prepare environment variables for container
        environment = [
            {"name": "STUDENT_IDS", "value": json.dumps(job_config.get("student_ids", []))},
            {"name": "S3_PATHS", "value": json.dumps(job_config.get("s3_paths", {}))},
        ]

        if "grade_level" in job_config:
            environment.append(
                {"name": "GRADE_LEVEL", "value": str(job_config["grade_level"])}
            )

        if request_id:
            environment.append({"name": "REQUEST_ID", "value": request_id})

        # Prepare container overrides
        container_overrides = {
            "environment": environment,
            "resourceRequirements": [
                {"type": "MEMORY", "value": str(memory)},
                {"type": "VCPU", "value": str(vcpus)},
            ],
        }

        # Submit job
        try:
            response = self.client.submit_job(
                jobName=unique_job_name,
                jobQueue=self.job_queue,
                jobDefinition=self.job_definition,
                parameters=parameters,
                containerOverrides=container_overrides,
                timeout={"attemptDurationSeconds": timeout},
            )

            job_id = response["jobId"]

            logger.info(
                f"Batch job submitted successfully",
                extra={
                    "job_id": job_id,
                    "job_name": unique_job_name,
                    "request_id": request_id,
                },
            )

            return job_id

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                f"Failed to submit batch job",
                extra={
                    "job_name": unique_job_name,
                    "error_code": error_code,
                    "error_message": error_message,
                    "request_id": request_id,
                },
            )

            raise BatchJobError(
                f"Failed to submit batch job: {error_message}"
            ) from e

    def get_job_status(self, job_id: str) -> Optional[BatchJobInfo]:
        """Get status of a batch job.

        Args:
            job_id: Job ID to check

        Returns:
            BatchJobInfo if job exists, None otherwise

        Raises:
            BatchJobError: If status retrieval fails
        """
        logger.debug(f"Getting job status", extra={"job_id": job_id})

        try:
            response = self.client.describe_jobs(jobs=[job_id])

            if not response.get("jobs"):
                logger.debug(f"Job not found", extra={"job_id": job_id})
                return None

            job = response["jobs"][0]

            # Parse timestamps
            created_at = None
            if "createdAt" in job:
                created_at = datetime.fromtimestamp(job["createdAt"] / 1000)

            started_at = None
            if "startedAt" in job:
                started_at = datetime.fromtimestamp(job["startedAt"] / 1000)

            stopped_at = None
            if "stoppedAt" in job:
                stopped_at = datetime.fromtimestamp(job["stoppedAt"] / 1000)

            # Parse status
            status_str = job.get("status", "UNKNOWN")
            try:
                status = BatchJobStatus(status_str)
            except ValueError:
                logger.warning(
                    f"Unknown job status",
                    extra={"job_id": job_id, "status": status_str},
                )
                # Default to PENDING for unknown statuses
                status = BatchJobStatus.PENDING

            job_info = BatchJobInfo(
                job_id=job["jobId"],
                job_name=job.get("jobName", ""),
                status=status,
                created_at=created_at,
                started_at=started_at,
                stopped_at=stopped_at,
                exit_code=job.get("container", {}).get("exitCode"),
                status_reason=job.get("statusReason"),
            )

            logger.debug(
                f"Retrieved job status",
                extra={
                    "job_id": job_id,
                    "status": status.value,
                },
            )

            return job_info

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                f"Failed to get job status",
                extra={
                    "job_id": job_id,
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )

            raise BatchJobError(
                f"Failed to get job status: {error_message}"
            ) from e

    def list_jobs_by_status(
        self,
        status: BatchJobStatus,
        max_results: Optional[int] = None,
    ) -> List[Dict]:
        """List jobs by status.

        Args:
            status: Job status to filter by
            max_results: Maximum number of results (None for all)

        Returns:
            List of job summary dictionaries

        Raises:
            BatchJobError: If listing fails
        """
        logger.debug(
            f"Listing jobs by status",
            extra={"status": status.value, "max_results": max_results},
        )

        jobs = []
        next_token = None

        try:
            while True:
                params = {
                    "jobQueue": self.job_queue,
                    "jobStatus": status.value,
                }

                if next_token:
                    params["nextToken"] = next_token

                if max_results:
                    remaining = max_results - len(jobs)
                    if remaining <= 0:
                        break
                    params["maxResults"] = min(remaining, 100)  # AWS limit is 100

                response = self.client.list_jobs(**params)

                jobs.extend(response.get("jobSummaryList", []))

                next_token = response.get("nextToken")
                if not next_token:
                    break

                if max_results and len(jobs) >= max_results:
                    break

            logger.debug(
                f"Listed jobs by status",
                extra={
                    "status": status.value,
                    "count": len(jobs),
                },
            )

            return jobs[:max_results] if max_results else jobs

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                f"Failed to list jobs",
                extra={
                    "status": status.value,
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )

            raise BatchJobError(
                f"Failed to list jobs: {error_message}"
            ) from e

    def cancel_job(self, job_id: str, reason: str = "User requested cancellation") -> None:
        """Cancel a running batch job.

        Args:
            job_id: Job ID to cancel
            reason: Reason for cancellation

        Raises:
            BatchJobError: If cancellation fails
        """
        logger.info(f"Cancelling batch job", extra={"job_id": job_id, "reason": reason})

        try:
            self.client.cancel_job(jobId=job_id, reason=reason)

            logger.info(f"Batch job cancelled", extra={"job_id": job_id})

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                f"Failed to cancel job",
                extra={
                    "job_id": job_id,
                    "error_code": error_code,
                    "error_message": error_message,
                },
            )

            raise BatchJobError(
                f"Failed to cancel job: {error_message}"
            ) from e

