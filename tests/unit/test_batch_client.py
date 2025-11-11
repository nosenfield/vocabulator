"""Unit tests for AWS Batch client.

Tests cover:
- Batch job submission
- Job status tracking
- Error handling
- Job configuration
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.processing.batch_client import BatchClient, BatchJobError, BatchJobStatus


@pytest.fixture
def mock_boto3_batch():
    """Create mock boto3 batch client."""
    with patch("src.processing.batch_client.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def batch_client(mock_boto3_batch):
    """Create BatchClient instance with mocked boto3."""
    return BatchClient(
        job_queue="test-queue",
        job_definition="test-job-def",
    )


@pytest.fixture
def sample_job_config():
    """Sample job configuration."""
    return {
        "student_ids": ["STU-001", "STU-002", "STU-003"],
        "s3_paths": {
            "STU-001": "s3://bucket/transcripts/STU-001.txt",
            "STU-002": "s3://bucket/transcripts/STU-002.txt",
            "STU-003": "s3://bucket/transcripts/STU-003.txt",
        },
        "grade_level": 7,
    }


def test_submit_job_success(batch_client, mock_boto3_batch, sample_job_config):
    """Test successful job submission."""
    # Setup mock response
    mock_boto3_batch.submit_job.return_value = {
        "jobId": "test-job-123",
        "jobName": "vocabulator-batch-test-job-123",
    }

    # Submit job
    job_id = batch_client.submit_job(
        job_name="test-job",
        job_config=sample_job_config,
        request_id="test-request-001",
    )

    # Verify result
    assert job_id == "test-job-123"

    # Verify submit_job was called correctly
    mock_boto3_batch.submit_job.assert_called_once()
    call_kwargs = mock_boto3_batch.submit_job.call_args[1]
    assert call_kwargs["jobQueue"] == "test-queue"
    assert call_kwargs["jobDefinition"] == "test-job-def"
    assert call_kwargs["jobName"].startswith("test-job")
    assert "parameters" in call_kwargs
    assert "containerOverrides" in call_kwargs


def test_submit_job_with_environment_variables(
    batch_client, mock_boto3_batch, sample_job_config
):
    """Test job submission includes environment variables."""
    mock_boto3_batch.submit_job.return_value = {"jobId": "test-job-123"}

    batch_client.submit_job(
        job_name="test-job",
        job_config=sample_job_config,
    )

    # Verify environment variables are set
    call_kwargs = mock_boto3_batch.submit_job.call_args[1]
    container_overrides = call_kwargs["containerOverrides"]
    assert "environment" in container_overrides

    env_vars = {
        env["name"]: env["value"]
        for env in container_overrides["environment"]
    }
    assert "STUDENT_IDS" in env_vars
    assert "S3_PATHS" in env_vars
    assert "GRADE_LEVEL" in env_vars


def test_submit_job_error_handling(batch_client, mock_boto3_batch, sample_job_config):
    """Test error handling during job submission."""
    # Setup mock to raise error
    mock_boto3_batch.submit_job.side_effect = ClientError(
        {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid queue"}},
        "SubmitJob",
    )

    # Submit job should raise BatchJobError
    with pytest.raises(BatchJobError) as exc_info:
        batch_client.submit_job(
            job_name="test-job",
            job_config=sample_job_config,
        )

    assert "Invalid queue" in str(exc_info.value)


def test_get_job_status_success(batch_client, mock_boto3_batch):
    """Test successful job status retrieval."""
    # Setup mock response
    mock_boto3_batch.describe_jobs.return_value = {
        "jobs": [
            {
                "jobId": "test-job-123",
                "jobName": "test-job",
                "status": "RUNNING",
                "createdAt": 1234567890,
                "startedAt": 1234567900,
            }
        ]
    }

    # Get status
    status = batch_client.get_job_status("test-job-123")

    # Verify result
    assert status.job_id == "test-job-123"
    assert status.status == BatchJobStatus.RUNNING
    assert status.created_at is not None

    # Verify describe_jobs was called
    mock_boto3_batch.describe_jobs.assert_called_once_with(
        jobs=["test-job-123"]
    )


def test_get_job_status_not_found(batch_client, mock_boto3_batch):
    """Test job status retrieval when job not found."""
    # Setup mock response (empty jobs list)
    mock_boto3_batch.describe_jobs.return_value = {"jobs": []}

    # Get status should return None
    status = batch_client.get_job_status("non-existent-job")

    assert status is None


def test_get_job_status_error(batch_client, mock_boto3_batch):
    """Test error handling during status retrieval."""
    # Setup mock to raise error
    mock_boto3_batch.describe_jobs.side_effect = ClientError(
        {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid job ID"}},
        "DescribeJobs",
    )

    # Get status should raise BatchJobError
    with pytest.raises(BatchJobError) as exc_info:
        batch_client.get_job_status("invalid-job-id")

    assert "Invalid job ID" in str(exc_info.value)


def test_list_jobs_by_status(batch_client, mock_boto3_batch):
    """Test listing jobs by status."""
    # Setup mock response (AWS Batch filters by status, so only RUNNING jobs returned)
    mock_boto3_batch.list_jobs.return_value = {
        "jobSummaryList": [
            {"jobId": "job-1", "jobName": "test-1", "status": "RUNNING"},
        ],
        "nextToken": None,
    }

    # List jobs
    jobs = batch_client.list_jobs_by_status(BatchJobStatus.RUNNING)

    # Verify result
    assert len(jobs) == 1
    assert jobs[0]["jobId"] == "job-1"

    # Verify list_jobs was called
    mock_boto3_batch.list_jobs.assert_called_once()
    call_kwargs = mock_boto3_batch.list_jobs.call_args[1]
    assert call_kwargs["jobQueue"] == "test-queue"
    assert call_kwargs["jobStatus"] == "RUNNING"


def test_list_jobs_with_pagination(batch_client, mock_boto3_batch):
    """Test listing jobs with pagination."""
    # Setup mock responses for pagination
    mock_boto3_batch.list_jobs.side_effect = [
        {
            "jobSummaryList": [{"jobId": "job-1", "status": "RUNNING"}],
            "nextToken": "token-123",
        },
        {
            "jobSummaryList": [{"jobId": "job-2", "status": "RUNNING"}],
            "nextToken": None,
        },
    ]

    # List jobs
    jobs = batch_client.list_jobs_by_status(BatchJobStatus.RUNNING)

    # Verify result (should include both pages)
    assert len(jobs) == 2
    assert mock_boto3_batch.list_jobs.call_count == 2


def test_cancel_job_success(batch_client, mock_boto3_batch):
    """Test successful job cancellation."""
    # Setup mock response
    mock_boto3_batch.cancel_job.return_value = {}

    # Cancel job
    batch_client.cancel_job("test-job-123", reason="User requested")

    # Verify cancel_job was called
    mock_boto3_batch.cancel_job.assert_called_once_with(
        jobId="test-job-123",
        reason="User requested",
    )


def test_cancel_job_error(batch_client, mock_boto3_batch):
    """Test error handling during job cancellation."""
    # Setup mock to raise error
    mock_boto3_batch.cancel_job.side_effect = ClientError(
        {"Error": {"Code": "InvalidJobId", "Message": "Job not found"}},
        "CancelJob",
    )

    # Cancel job should raise BatchJobError
    with pytest.raises(BatchJobError) as exc_info:
        batch_client.cancel_job("invalid-job-id", reason="Test")

    assert "Job not found" in str(exc_info.value)


def test_batch_job_status_enum():
    """Test BatchJobStatus enum values."""
    assert BatchJobStatus.SUBMITTED.value == "SUBMITTED"
    assert BatchJobStatus.PENDING.value == "PENDING"
    assert BatchJobStatus.RUNNABLE.value == "RUNNABLE"
    assert BatchJobStatus.RUNNING.value == "RUNNING"
    assert BatchJobStatus.SUCCEEDED.value == "SUCCEEDED"
    assert BatchJobStatus.FAILED.value == "FAILED"


def test_batch_client_initialization():
    """Test BatchClient initialization with default values."""
    with patch("src.processing.batch_client.boto3") as mock_boto3, patch(
        "src.processing.batch_client.get_config"
    ) as mock_get_config:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        # Mock config
        mock_config = MagicMock()
        mock_config.aws_region = "us-east-1"
        mock_get_config.return_value = mock_config

        client = BatchClient()

        # Verify boto3 client was created
        mock_boto3.client.assert_called_once()
        call_args = mock_boto3.client.call_args
        assert call_args[0][0] == "batch"
        assert "region_name" in call_args[1]
        assert client.client == mock_client


def test_batch_client_with_custom_config():
    """Test BatchClient initialization with custom config."""
    with patch("src.processing.batch_client.boto3") as mock_boto3, patch(
        "src.processing.batch_client.get_config"
    ) as mock_get_config:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        # Mock config
        mock_config = MagicMock()
        mock_config.aws_region = "us-east-1"
        mock_get_config.return_value = mock_config

        client = BatchClient(
            job_queue="custom-queue",
            job_definition="custom-def",
            region="us-west-2",
        )

        assert client.job_queue == "custom-queue"
        assert client.job_definition == "custom-def"
        # Verify boto3 client was created with custom region and config
        mock_boto3.client.assert_called_once()
        call_args = mock_boto3.client.call_args
        assert call_args[0][0] == "batch"
        assert call_args[1]["region_name"] == "us-west-2"
        assert "config" in call_args[1]


def test_batch_client_missing_config():
    """Test BatchClient raises ValueError when config attributes are missing."""
    with patch("src.processing.batch_client.boto3") as mock_boto3, patch(
        "src.processing.batch_client.get_config"
    ) as mock_get_config:
        # Mock config without batch_job_queue and batch_job_definition
        # Use a simple object that doesn't have these attributes
        class MockConfig:
            aws_region = "us-east-1"
            # Intentionally omit batch_job_queue and batch_job_definition

        mock_get_config.return_value = MockConfig()

        # Should raise ValueError when neither provided nor in config
        with pytest.raises(ValueError, match="job_queue must be provided"):
            BatchClient()

        # Should raise ValueError for missing job_definition
        with pytest.raises(ValueError, match="job_definition must be provided"):
            BatchClient(job_queue="test-queue")

