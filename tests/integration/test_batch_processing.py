"""Batch processing integration tests.

This module tests batch processing workflows:
- Submit batch job → Process students → Verify results
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.processing.batch_client import BatchClient, BatchJobInfo, BatchJobStatus


@pytest.fixture
def mock_aws_services():
    """Create mock AWS services (S3 and DynamoDB) for testing."""
    with mock_aws():
        # Set up S3
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        
        # Set up DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create StudentProfiles table
        dynamodb.create_table(
            TableName="test-StudentProfiles",
            KeySchema=[{"AttributeName": "student_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "student_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        
        # Create VocabularyRecommendations table
        dynamodb.create_table(
            TableName="test-VocabularyRecommendations",
            KeySchema=[
                {"AttributeName": "student_id", "KeyType": "HASH"},
                {"AttributeName": "recommendation_date", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "student_id", "AttributeType": "S"},
                {"AttributeName": "recommendation_date", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        
        yield {"s3": s3_client, "dynamodb": dynamodb}


@pytest.fixture
def mock_batch_client():
    """Mock AWS Batch client for testing."""
    mock_client = MagicMock()
    
    # Mock job submission
    def mock_submit_job(**kwargs):
        job_id = f"test-job-{kwargs.get('jobName', 'unknown')}"
        return {"jobId": job_id}
    
    mock_client.submit_job = MagicMock(side_effect=mock_submit_job)
    
    # Mock job status retrieval
    def mock_describe_jobs(jobIds):
        job_id = jobIds[0]
        return {
            "jobs": [
                {
                    "jobId": job_id,
                    "jobName": "test-job",
                    "status": "SUCCEEDED",
                    "createdAt": datetime.now(timezone.utc).timestamp() * 1000,
                    "startedAt": datetime.now(timezone.utc).timestamp() * 1000,
                    "stoppedAt": datetime.now(timezone.utc).timestamp() * 1000,
                }
            ]
        }
    
    mock_client.describe_jobs = MagicMock(side_effect=mock_describe_jobs)
    
    return mock_client


@pytest.mark.integration
def test_batch_job_submission_and_status(
    mock_aws_services, mock_batch_client, temp_env_vars
):
    """Test batch job submission and status retrieval."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
        BATCH_JOB_QUEUE="test-queue",
        BATCH_JOB_DEFINITION="test-definition",
    )
    
    # Create student profiles
    student_repo = StudentRepository()
    student_ids = ["STU-001", "STU-002", "STU-003"]
    
    for student_id in student_ids:
        from src.data.models.student_profile import StudentProfile
        
        student = StudentProfile(
            student_id=student_id,
            grade_level=7,
            vocabulary_list=[],
        )
        student_repo.create(student)
    
    # Prepare batch job configuration
    s3_paths = {
        student_id: f"transcripts/raw/{student_id}/2024-01-01.txt"
        for student_id in student_ids
    }
    
    job_config = {
        "student_ids": student_ids,
        "s3_paths": s3_paths,
        "grade_level": 7,
    }
    
    # Submit batch job with mocked Batch client
    with patch("src.processing.batch_client.boto3.client", return_value=mock_batch_client):
        batch_client = BatchClient(
            job_queue="test-queue",
            job_definition="test-definition",
        )
        
        job_id = batch_client.submit_job(
            job_name="vocabulator-batch-process",
            job_config=job_config,
        )
        
        # Verify job was submitted
        assert job_id is not None
        assert job_id.startswith("test-job")
        
        # Get job status (same client instance)
        job_info = batch_client.get_job_status(job_id)
    
    # Verify job status
    assert job_info is not None
    assert job_info.job_id == job_id
    assert job_info.status == BatchJobStatus.SUCCEEDED


@pytest.mark.integration
def test_batch_job_with_multiple_students(
    mock_aws_services, mock_batch_client, temp_env_vars
):
    """Test batch job processing for multiple students."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
        BATCH_JOB_QUEUE="test-queue",
        BATCH_JOB_DEFINITION="test-definition",
    )
    
    # Create 30 student profiles (simulating batch processing requirement)
    student_repo = StudentRepository()
    student_ids = [f"STU-{i:03d}" for i in range(1, 31)]
    
    for student_id in student_ids:
        from src.data.models.student_profile import StudentProfile
        
        student = StudentProfile(
            student_id=student_id,
            grade_level=7,
            vocabulary_list=[],
        )
        student_repo.create(student)
    
    # Prepare batch job configuration
    s3_paths = {
        student_id: f"transcripts/raw/{student_id}/2024-01-01.txt"
        for student_id in student_ids
    }
    
    job_config = {
        "student_ids": student_ids,
        "s3_paths": s3_paths,
        "grade_level": 7,
    }
    
    # Submit batch job (inside patch context)
    with patch("src.processing.batch_client.boto3.client", return_value=mock_batch_client):
        batch_client = BatchClient(
            job_queue="test-queue",
            job_definition="test-definition",
        )
        
        job_id = batch_client.submit_job(
            job_name="vocabulator-batch-process-30",
            job_config=job_config,
        )
    
    # Verify job was submitted with all students
    assert job_id is not None
    
    # Verify all students exist in repository
    for student_id in student_ids:
        profile = student_repo.get(student_id)
        assert profile is not None
        assert profile.student_id == student_id


@pytest.mark.integration
def test_batch_job_status_tracking(
    mock_aws_services, mock_batch_client, temp_env_vars
):
    """Test batch job status tracking through different states."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
        BATCH_JOB_QUEUE="test-queue",
        BATCH_JOB_DEFINITION="test-definition",
    )
    
    # Create mock client that returns different statuses
    statuses = [
        BatchJobStatus.SUBMITTED,
        BatchJobStatus.PENDING,
        BatchJobStatus.RUNNABLE,
        BatchJobStatus.RUNNING,
        BatchJobStatus.SUCCEEDED,
    ]
    status_index = [0]
    
    def mock_describe_jobs_with_status(jobIds):
        current_status = statuses[status_index[0]]
        status_index[0] = min(status_index[0] + 1, len(statuses) - 1)
        
        return {
            "jobs": [
                {
                    "jobId": jobIds[0],
                    "jobName": "test-job",
                    "status": current_status.value,
                    "createdAt": datetime.now(timezone.utc).timestamp() * 1000,
                }
            ]
        }
    
    mock_batch_client.describe_jobs = MagicMock(side_effect=mock_describe_jobs_with_status)
    
    job_id = "test-job-123"
    
    # Create BatchClient inside patch context
    with patch("src.processing.batch_client.boto3.client", return_value=mock_batch_client):
        batch_client = BatchClient(
            job_queue="test-queue",
            job_definition="test-definition",
        )
        
        # Track status progression (all calls use same mocked client)
        tracked_statuses = []
        for _ in range(len(statuses)):
            job_info = batch_client.get_job_status(job_id)
            if job_info:
                tracked_statuses.append(job_info.status)
    
    # Verify status progression
    assert len(tracked_statuses) == len(statuses)
    assert tracked_statuses[-1] == BatchJobStatus.SUCCEEDED

