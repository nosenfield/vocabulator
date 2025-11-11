"""Batch job handler script for AWS Batch/Fargate containers.

This script runs inside the batch container and processes student transcripts
using the TextProcessingPipeline and ParallelExecutor.
"""

import asyncio
import json
import os
import sys
from typing import Dict, List

from src.data.s3_client import S3Client, S3Error
from src.processing.parallel_executor import ParallelExecutor, ProcessingTask
from src.processing.text_processing_pipeline import TextProcessingPipeline
from src.utils.logger import get_logger

logger = get_logger("processing.batch_handler")


async def process_batch_job() -> int:
    """Process a batch job.

    Reads job configuration from environment variables, downloads transcripts
    from S3, processes them using the pipeline, and updates student profiles.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get job configuration from environment variables
        student_ids_json = os.environ.get("STUDENT_IDS", "[]")
        s3_paths_json = os.environ.get("S3_PATHS", "{}")
        grade_level_str = os.environ.get("GRADE_LEVEL")
        request_id = os.environ.get("REQUEST_ID")

        # Parse configuration
        student_ids: List[str] = json.loads(student_ids_json)
        s3_paths: Dict[str, str] = json.loads(s3_paths_json)
        grade_level = int(grade_level_str) if grade_level_str else None

        logger.info(
            f"Starting batch job processing",
            extra={
                "student_count": len(student_ids),
                "grade_level": grade_level,
                "request_id": request_id,
            },
        )

        if not student_ids:
            logger.warning("No student IDs provided in job configuration")
            return 1

        # Initialize clients
        s3_client = S3Client()
        pipeline = TextProcessingPipeline()
        executor = ParallelExecutor(pipeline=pipeline, max_concurrent=10)

        # Download transcripts and create processing tasks
        tasks = []
        for student_id in student_ids:
            s3_path = s3_paths.get(student_id)
            if not s3_path:
                logger.warning(
                    f"No S3 path provided for student",
                    extra={"student_id": student_id, "request_id": request_id},
                )
                continue

            try:
                # Validate S3 path format
                if not s3_path or not isinstance(s3_path, str):
                    logger.warning(
                        f"Invalid S3 path format",
                        extra={"student_id": student_id, "s3_path": s3_path, "request_id": request_id},
                    )
                    continue

                # Security: Prevent path traversal attacks
                if ".." in s3_path or s3_path.startswith("/"):
                    logger.warning(
                        f"Potentially malicious S3 path detected",
                        extra={"student_id": student_id, "s3_path": s3_path, "request_id": request_id},
                    )
                    continue

                # Parse S3 path (format: s3://bucket/key or bucket/key)
                if s3_path.startswith("s3://"):
                    # Remove s3:// prefix
                    path_parts = s3_path[5:].split("/", 1)
                    bucket = path_parts[0]
                    key = path_parts[1] if len(path_parts) > 1 else ""
                else:
                    # Assume format: bucket/key
                    path_parts = s3_path.split("/", 1)
                    bucket = path_parts[0]
                    key = path_parts[1] if len(path_parts) > 1 else ""

                # Validate parsed values
                if not bucket or not key:
                    logger.warning(
                        f"Invalid S3 path: missing bucket or key",
                        extra={"student_id": student_id, "s3_path": s3_path, "request_id": request_id},
                    )
                    continue

                # Create S3 client for this bucket and download transcript
                student_s3_client = S3Client(bucket_name=bucket)
                transcript_bytes = student_s3_client.download(key)
                transcript_text = transcript_bytes.decode("utf-8")
                logger.debug(
                    f"Downloaded transcript",
                    extra={
                        "student_id": student_id,
                        "s3_path": s3_path,
                        "text_length": len(transcript_text),
                        "request_id": request_id,
                    },
                )

                # Create processing task
                task = ProcessingTask(
                    student_id=student_id,
                    text=transcript_text,
                    grade_level=grade_level,
                )
                tasks.append(task)

            except (S3Error, json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
                # Catch specific exceptions, but also catch generic Exception
                # to prevent one student's failure from stopping the batch
                # Log error type to help with debugging unexpected exceptions
                logger.error(
                    f"Failed to download or process transcript",
                    extra={
                        "student_id": student_id,
                        "s3_path": s3_path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "request_id": request_id,
                    },
                )
                # Continue with other students
                continue

        if not tasks:
            logger.error("No valid processing tasks created")
            return 1

        # Process tasks in parallel
        logger.info(
            f"Processing {len(tasks)} students in parallel",
            extra={"task_count": len(tasks), "request_id": request_id},
        )

        results = await executor.execute_parallel(tasks, request_id=request_id)

        # Check results
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        logger.info(
            f"Batch job completed",
            extra={
                "total_tasks": len(tasks),
                "successful": success_count,
                "failed": failure_count,
                "request_id": request_id,
            },
        )

        # Return non-zero exit code if all tasks failed
        if failure_count == len(results):
            logger.error("All processing tasks failed")
            return 1

        # Return non-zero exit code if more than 50% failed
        if failure_count > len(results) / 2:
            logger.warning(
                f"More than 50% of tasks failed",
                extra={"failure_rate": failure_count / len(results)},
            )
            return 1

        return 0

    except Exception as e:
        logger.error(
            f"Batch job failed with exception",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return 1


def main():
    """Main entry point for batch job handler."""
    exit_code = asyncio.run(process_batch_job())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

