"""Unit tests for parallel processing executor.

Tests cover:
- Parallel execution of multiple student processing tasks
- Error handling for individual task failures
- Result aggregation and status reporting
- Concurrency limits
- Progress tracking
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.data.models.recommendation import VocabularyRecommendation
from src.data.models.student_profile import StudentProfile
from src.processing.parallel_executor import ParallelExecutor, ProcessingResult, ProcessingTask
from src.processing.text_processing_pipeline import TextProcessingPipeline


@pytest.fixture
def sample_processing_tasks():
    """Create sample processing tasks."""
    return [
        ProcessingTask(
            student_id="STU-001",
            text="Today we learned about photosynthesis.",
            grade_level=7,
        ),
        ProcessingTask(
            student_id="STU-002",
            text="We analyzed data from experiments.",
            grade_level=7,
        ),
        ProcessingTask(
            student_id="STU-003",
            text="The process involves converting sunlight into energy.",
            grade_level=8,
        ),
    ]


@pytest.fixture
def mock_pipeline():
    """Create mock text processing pipeline."""
    pipeline = MagicMock(spec=TextProcessingPipeline)
    pipeline.process_text = AsyncMock(return_value=None)
    return pipeline


@pytest.fixture
def sample_recommendation():
    """Create sample recommendation."""
    from src.data.models.recommendation import RecommendedWord

    return VocabularyRecommendation(
        student_id="STU-001",
        recommendation_date=datetime.now(timezone.utc).date().isoformat(),
        words=[
            RecommendedWord(
                word="synthesize",
                definition="combine elements",
                grade_level=7,
                difficulty_score=0.7,
                rationale="High-frequency word",
                example_sentences=["Scientists synthesize information."],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_execute_parallel_success(
    sample_processing_tasks, mock_pipeline, sample_recommendation
):
    """Test successful parallel execution of multiple tasks."""
    # Setup mocks
    mock_pipeline.process_text.return_value = sample_recommendation

    # Create executor
    executor = ParallelExecutor(pipeline=mock_pipeline, max_concurrent=3)

    # Execute
    results = await executor.execute_parallel(sample_processing_tasks)

    # Verify results
    assert len(results) == 3
    assert all(result.success for result in results)
    assert all(result.student_id in ["STU-001", "STU-002", "STU-003"] for result in results)

    # Verify pipeline was called for each task
    assert mock_pipeline.process_text.call_count == 3

    # Verify each task was processed
    call_args_list = mock_pipeline.process_text.call_args_list
    processed_student_ids = {call[1]["student_id"] for call in call_args_list}
    assert processed_student_ids == {"STU-001", "STU-002", "STU-003"}


@pytest.mark.asyncio
async def test_execute_parallel_with_failures(
    sample_processing_tasks, mock_pipeline
):
    """Test parallel execution with some task failures."""
    from src.ai.openai_client import OpenAIError

    # Setup mocks - first task succeeds, second fails, third succeeds
    def side_effect(**kwargs):
        student_id = kwargs.get("student_id")
        if student_id == "STU-002":
            raise OpenAIError("Extraction failed")
        return VocabularyRecommendation(
            student_id=student_id,
            recommendation_date=datetime.now(timezone.utc).date().isoformat(),
            words=[],
        )

    mock_pipeline.process_text.side_effect = side_effect

    # Create executor
    executor = ParallelExecutor(pipeline=mock_pipeline, max_concurrent=3)

    # Execute
    results = await executor.execute_parallel(sample_processing_tasks)

    # Verify results
    assert len(results) == 3

    # Check success/failure status
    success_results = [r for r in results if r.success]
    failure_results = [r for r in results if not r.success]

    assert len(success_results) == 2
    assert len(failure_results) == 1
    assert failure_results[0].student_id == "STU-002"
    assert failure_results[0].error is not None
    assert "Extraction failed" in failure_results[0].error


@pytest.mark.asyncio
async def test_execute_parallel_concurrency_limit(
    sample_processing_tasks, mock_pipeline, sample_recommendation
):
    """Test that concurrency limit is respected."""
    import asyncio

    # Track concurrent executions
    concurrent_count = 0
    max_concurrent = 0

    async def track_concurrency(**kwargs):
        nonlocal concurrent_count, max_concurrent
        concurrent_count += 1
        max_concurrent = max(max_concurrent, concurrent_count)
        await asyncio.sleep(0.1)  # Simulate processing time
        concurrent_count -= 1
        return sample_recommendation

    mock_pipeline.process_text.side_effect = track_concurrency

    # Create executor with concurrency limit of 2
    executor = ParallelExecutor(pipeline=mock_pipeline, max_concurrent=2)

    # Execute with 3 tasks
    results = await executor.execute_parallel(sample_processing_tasks)

    # Verify concurrency was limited
    assert max_concurrent <= 2
    assert len(results) == 3


@pytest.mark.asyncio
async def test_execute_parallel_empty_tasks(mock_pipeline):
    """Test execution with empty task list."""
    executor = ParallelExecutor(pipeline=mock_pipeline)

    results = await executor.execute_parallel([])

    assert len(results) == 0
    mock_pipeline.process_text.assert_not_called()


@pytest.mark.asyncio
async def test_execute_parallel_single_task(
    mock_pipeline, sample_recommendation
):
    """Test execution with single task."""
    task = ProcessingTask(
        student_id="STU-001",
        text="Sample text",
        grade_level=7,
    )

    mock_pipeline.process_text.return_value = sample_recommendation

    executor = ParallelExecutor(pipeline=mock_pipeline)

    results = await executor.execute_parallel([task])

    assert len(results) == 1
    assert results[0].success
    assert results[0].student_id == "STU-001"
    assert results[0].recommendation is not None


@pytest.mark.asyncio
async def test_execute_parallel_progress_callback(
    sample_processing_tasks, mock_pipeline, sample_recommendation
):
    """Test progress callback is called during execution."""
    mock_pipeline.process_text.return_value = sample_recommendation

    progress_calls = []

    def progress_callback(completed: int, total: int):
        progress_calls.append((completed, total))

    executor = ParallelExecutor(
        pipeline=mock_pipeline, progress_callback=progress_callback
    )

    await executor.execute_parallel(sample_processing_tasks)

    # Verify progress callback was called
    assert len(progress_calls) > 0
    # Should have at least one call with final count
    final_call = progress_calls[-1]
    assert final_call == (3, 3)


@pytest.mark.asyncio
async def test_execute_parallel_request_id_propagation(
    sample_processing_tasks, mock_pipeline, sample_recommendation
):
    """Test that request ID is propagated to pipeline."""
    mock_pipeline.process_text.return_value = sample_recommendation

    executor = ParallelExecutor(pipeline=mock_pipeline)
    request_id = "batch-request-123"

    await executor.execute_parallel(sample_processing_tasks, request_id=request_id)

    # Verify request ID was passed to pipeline
    call_args_list = mock_pipeline.process_text.call_args_list
    for call in call_args_list:
        assert call[1]["request_id"] == request_id


@pytest.mark.asyncio
async def test_execute_parallel_result_structure(
    sample_processing_tasks, mock_pipeline, sample_recommendation
):
    """Test that results have correct structure."""
    mock_pipeline.process_text.return_value = sample_recommendation

    executor = ParallelExecutor(pipeline=mock_pipeline)

    results = await executor.execute_parallel(sample_processing_tasks)

    for result in results:
        assert isinstance(result, ProcessingResult)
        assert result.student_id is not None
        assert isinstance(result.success, bool)
        if result.success:
            assert result.recommendation is not None
            assert result.error is None
        else:
            assert result.recommendation is None
            assert result.error is not None


@pytest.mark.asyncio
async def test_execute_parallel_default_max_concurrent(mock_pipeline):
    """Test default max_concurrent value."""
    executor = ParallelExecutor(pipeline=mock_pipeline)

    # Default should be reasonable (e.g., 10 or cpu_count)
    assert executor.max_concurrent > 0
    assert executor.max_concurrent <= 20  # Reasonable upper bound

