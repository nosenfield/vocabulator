"""Parallel processing executor for batch operations.

This module provides parallel execution capabilities for processing multiple
students concurrently, with configurable concurrency limits and error handling.
"""

import asyncio
from dataclasses import dataclass
from typing import Callable, List, Optional

from src.data.models.recommendation import VocabularyRecommendation
from src.processing.text_processing_pipeline import TextProcessingPipeline
from src.utils.logger import get_logger

logger = get_logger("processing.parallel_executor")


@dataclass
class ProcessingTask:
    """Represents a single student processing task.

    Attributes:
        student_id: Anonymous student identifier
        text: Student text to process (transcript or writing sample)
        grade_level: Optional grade level (uses profile grade if not provided)
    """

    student_id: str
    text: str
    grade_level: Optional[int] = None


@dataclass
class ProcessingResult:
    """Result of processing a single student task.

    Attributes:
        student_id: Student identifier
        success: Whether processing succeeded
        recommendation: Generated recommendation (if successful)
        error: Error message (if failed)
    """

    student_id: str
    success: bool
    recommendation: Optional[VocabularyRecommendation] = None
    error: Optional[str] = None


class ParallelExecutor:
    """Execute multiple student processing tasks in parallel.

    Uses asyncio for concurrent execution of I/O-bound operations.
    Supports configurable concurrency limits and progress tracking.
    """

    def __init__(
        self,
        pipeline: Optional[TextProcessingPipeline] = None,
        max_concurrent: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """Initialize parallel executor.

        Args:
            pipeline: Text processing pipeline instance (creates new if None)
            max_concurrent: Maximum number of concurrent tasks (default: 10)
            progress_callback: Optional callback for progress updates (completed, total)
        """
        self.pipeline = pipeline or TextProcessingPipeline()
        self.max_concurrent = max_concurrent
        self.progress_callback = progress_callback

    async def execute_parallel(
        self,
        tasks: List[ProcessingTask],
        request_id: Optional[str] = None,
    ) -> List[ProcessingResult]:
        """Execute multiple processing tasks in parallel.

        Args:
            tasks: List of processing tasks to execute
            request_id: Optional request ID for correlation

        Returns:
            List of ProcessingResult objects, one per task
        """
        if not tasks:
            logger.debug("No tasks to process")
            return []

        logger.info(
            f"Starting parallel execution",
            extra={
                "task_count": len(tasks),
                "max_concurrent": self.max_concurrent,
                "request_id": request_id,
            },
        )

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Create tasks
        async_tasks = [
            self._process_with_semaphore(semaphore, task, request_id, i, len(tasks))
            for i, task in enumerate(tasks)
        ]

        # Execute all tasks concurrently (respecting semaphore limit)
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Convert exceptions to ProcessingResult failures
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle unexpected exceptions
                task = tasks[i]
                processed_results.append(
                    ProcessingResult(
                        student_id=task.student_id,
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        # Log summary
        success_count = sum(1 for r in processed_results if r.success)
        failure_count = len(processed_results) - success_count

        logger.info(
            f"Parallel execution completed",
            extra={
                "total_tasks": len(tasks),
                "successful": success_count,
                "failed": failure_count,
                "request_id": request_id,
            },
        )

        return processed_results

    async def _process_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        task: ProcessingTask,
        request_id: Optional[str],
        task_index: int,
        total_tasks: int,
    ) -> ProcessingResult:
        """Process a single task with semaphore-controlled concurrency.

        Args:
            semaphore: Semaphore to control concurrency
            task: Processing task to execute
            request_id: Optional request ID
            task_index: Index of task (for progress tracking)
            total_tasks: Total number of tasks

        Returns:
            ProcessingResult for the task
        """
        async with semaphore:
            logger.debug(
                f"Processing task",
                extra={
                    "student_id": task.student_id,
                    "task_index": task_index + 1,
                    "total_tasks": total_tasks,
                    "request_id": request_id,
                },
            )

            try:
                recommendation = await self.pipeline.process_text(
                    text=task.text,
                    student_id=task.student_id,
                    grade_level=task.grade_level,
                    request_id=request_id,
                )

                result = ProcessingResult(
                    student_id=task.student_id,
                    success=True,
                    recommendation=recommendation,
                )

                logger.debug(
                    f"Task completed successfully",
                    extra={
                        "student_id": task.student_id,
                        "recommendations": len(recommendation.words),
                        "request_id": request_id,
                    },
                )

                # Call progress callback
                if self.progress_callback:
                    self.progress_callback(task_index + 1, total_tasks)

                return result

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Task failed",
                    extra={
                        "student_id": task.student_id,
                        "error": error_msg,
                        "request_id": request_id,
                    },
                )

                result = ProcessingResult(
                    student_id=task.student_id,
                    success=False,
                    error=error_msg,
                )

                # Call progress callback even on failure
                if self.progress_callback:
                    self.progress_callback(task_index + 1, total_tasks)

                return result

    async def execute_sequential(
        self,
        tasks: List[ProcessingTask],
        request_id: Optional[str] = None,
    ) -> List[ProcessingResult]:
        """Execute tasks sequentially (for testing or debugging).

        Args:
            tasks: List of processing tasks to execute
            request_id: Optional request ID for correlation

        Returns:
            List of ProcessingResult objects, one per task
        """
        logger.info(
            f"Starting sequential execution",
            extra={"task_count": len(tasks), "request_id": request_id},
        )

        results = []

        for i, task in enumerate(tasks):
            logger.debug(
                f"Processing task {i+1}/{len(tasks)}",
                extra={"student_id": task.student_id, "request_id": request_id},
            )

            try:
                recommendation = await self.pipeline.process_text(
                    text=task.text,
                    student_id=task.student_id,
                    grade_level=task.grade_level,
                    request_id=request_id,
                )

                results.append(
                    ProcessingResult(
                        student_id=task.student_id,
                        success=True,
                        recommendation=recommendation,
                    )
                )

                # Call progress callback
                if self.progress_callback:
                    self.progress_callback(i + 1, len(tasks))

            except Exception as e:
                logger.error(
                    f"Task failed",
                    extra={
                        "student_id": task.student_id,
                        "error": str(e),
                        "request_id": request_id,
                    },
                )

                results.append(
                    ProcessingResult(
                        student_id=task.student_id,
                        success=False,
                        error=str(e),
                    )
                )

                # Call progress callback even on failure
                if self.progress_callback:
                    self.progress_callback(i + 1, len(tasks))

        return results

