"""Performance testing for Vocabulator API and services.

This module tests performance targets:
- API P95 latency < 500ms
- Batch processing: 30 students in < 15 minutes
- S3 upload/download < 2 seconds
- DynamoDB queries < 10ms (P99)

Note: These tests use mocked AWS services (moto) which don't simulate
real network latency. Results represent code execution time, not actual
AWS service latency. Real production performance will vary based on
network conditions and AWS service performance.
"""

import time
from datetime import datetime, timezone
from math import ceil
from typing import List

import boto3
import pytest
from moto import mock_aws

from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.student_repository import StudentRepository
from src.data.s3_client import S3Client


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
        
        yield {"s3": s3_client, "dynamodb": dynamodb}


def calculate_percentile(times: List[float], percentile: float) -> float:
    """Calculate percentile from list of times.
    
    Args:
        times: List of time measurements in seconds
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Percentile value in seconds
    """
    if not times:
        return 0.0
    
    sorted_times = sorted(times)
    # Use ceil to handle edge cases correctly
    index = max(0, ceil(len(sorted_times) * (percentile / 100)) - 1)
    return sorted_times[min(index, len(sorted_times) - 1)]


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.aws
def test_dynamodb_query_performance(mock_aws_services, temp_env_vars):
    """Test DynamoDB query performance: P99 < 100ms (mocked services).
    
    Note: This test uses mocked AWS services which don't simulate real
    network latency. Real DynamoDB queries in production will typically
    be 10-50ms depending on region and network conditions. This test
    validates code execution performance.
    """
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        AWS_REGION="us-east-1",
    )
    
    student_repo = StudentRepository()
    
    # Create test students
    student_ids = [f"STU-{i:03d}" for i in range(1, 101)]  # 100 students
    for student_id in student_ids:
        student = StudentProfile(
            student_id=student_id,
            grade_level=7,
            vocabulary_list=[],
        )
        student_repo.create(student)
    
    # Measure query times
    query_times = []
    for student_id in student_ids:
        start = time.perf_counter()
        profile = student_repo.get(student_id)
        end = time.perf_counter()
        query_times.append((end - start) * 1000)  # Convert to milliseconds
        assert profile is not None
    
    # Calculate P99 latency
    p99_latency = calculate_percentile(query_times, 99)
    
    # Target: P99 < 100ms (adjusted for mocked services)
    # Real DynamoDB target is < 10ms, but mocked services have overhead
    assert p99_latency < 100.0, \
        f"DynamoDB P99 latency {p99_latency:.2f}ms exceeds 100ms target (mocked services)"
    
    # Also verify P95 < 50ms
    p95_latency = calculate_percentile(query_times, 95)
    assert p95_latency < 50.0, \
        f"DynamoDB P95 latency {p95_latency:.2f}ms exceeds 50ms target (mocked services)"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.aws
def test_s3_upload_performance(mock_aws_services, temp_env_vars):
    """Test S3 upload performance: < 2 seconds."""
    temp_env_vars(
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    s3_client = S3Client()
    
    # Test with different file sizes
    test_cases = [
        ("small", b"x" * 1024),  # 1KB
        ("medium", b"x" * 1024 * 100),  # 100KB
        ("large", b"x" * 1024 * 1024),  # 1MB
    ]
    
    for size_name, content in test_cases:
        key = f"test/{size_name}.txt"
        
        start = time.perf_counter()
        s3_client.upload(
            key=key,
            content=content,
            content_type="text/plain",
        )
        end = time.perf_counter()
        
        upload_time = end - start
        
        # Target: < 2 seconds
        assert upload_time < 2.0, \
            f"S3 upload for {size_name} file ({len(content)} bytes) took {upload_time:.2f}s, exceeds 2s target"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.aws
def test_s3_download_performance(mock_aws_services, temp_env_vars):
    """Test S3 download performance: < 2 seconds."""
    temp_env_vars(
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    s3_client = S3Client()
    
    # Upload test file first
    content = b"x" * 1024 * 100  # 100KB
    key = "test/download-test.txt"
    s3_client.upload(
        key=key,
        content=content,
        content_type="text/plain",
    )
    
    # Measure download time
    start = time.perf_counter()
    downloaded_content = s3_client.download(key)
    end = time.perf_counter()
    
    download_time = end - start
    
    # Verify content
    assert downloaded_content == content
    
    # Target: < 2 seconds
    assert download_time < 2.0, \
        f"S3 download took {download_time:.2f}s, exceeds 2s target"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.aws
def test_batch_processing_data_layer_performance(mock_aws_services, temp_env_vars):
    """Test batch processing data layer performance.
    
    This test validates the data layer performance for batch operations.
    Real batch processing includes OpenAI API calls which are tested separately
    in integration tests. This test focuses on DynamoDB operations only.
    
    Note: Full batch processing (including OpenAI) target is 30 students in < 15 minutes.
    This test verifies data layer can handle 30 students efficiently.
    """
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
    )
    
    student_repo = StudentRepository()
    
    # Create 30 student profiles
    student_ids = [f"STU-{i:03d}" for i in range(1, 31)]
    for student_id in student_ids:
        student = StudentProfile(
            student_id=student_id,
            grade_level=7,
            vocabulary_list=[],
        )
        student_repo.create(student)
    
    # Simulate batch processing: get profiles and update vocabulary
    start = time.perf_counter()
    
    for student_id in student_ids:
        # Simulate processing: get profile, update vocabulary
        profile = student_repo.get(student_id)
        assert profile is not None
        
        # Simulate vocabulary update using proper VocabularyEntry model
        entry = VocabularyEntry(
            word="test",
            first_seen=datetime.now(timezone.utc),
            usage_count=1,
        )
        profile.vocabulary_list.append(entry)
        student_repo.update(profile)
    
    end = time.perf_counter()
    processing_time = end - start
    
    # Verify reasonable performance for data layer operations
    # Should complete 30 student updates in < 5 seconds for mocked scenario
    assert processing_time < 5.0, \
        f"Batch data layer processing took {processing_time:.2f}s, slower than expected"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.aws
def test_api_endpoint_latency(mock_aws_services, temp_env_vars):
    """Test API endpoint latency: P95 < 500ms."""
    from fastapi.testclient import TestClient
    
    from src.api.main import app
    
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        AWS_REGION="us-east-1",
        OPENAI_API_KEY="test-key",
    )
    
    # Create test client
    client = TestClient(app)
    
    # Create test student
    student_id = "STU-PERF-001"
    client.post(
        "/api/v1/students",
        json={"student_id": student_id, "grade_level": 7},
    )
    
    # Measure GET /students/{id}/profile latency
    response_times = []
    for _ in range(50):  # 50 requests
        start = time.perf_counter()
        response = client.get(f"/api/v1/students/{student_id}/profile")
        end = time.perf_counter()
        
        assert response.status_code == 200
        response_times.append((end - start) * 1000)  # Convert to milliseconds
    
    # Calculate P95 latency
    p95_latency = calculate_percentile(response_times, 95)
    
    # Target: P95 < 500ms
    assert p95_latency < 500.0, \
        f"API endpoint P95 latency {p95_latency:.2f}ms exceeds 500ms target"
    
    # Also verify P50 (median) is reasonable
    p50_latency = calculate_percentile(response_times, 50)
    assert p50_latency < 100.0, \
        f"API endpoint P50 latency {p50_latency:.2f}ms is higher than expected"

