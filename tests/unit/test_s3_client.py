"""Unit tests for S3 client wrapper.

Tests cover upload, download, list, delete operations, multipart uploads, and presigned URLs.
"""

import io
import pytest
from pathlib import Path
from typing import BinaryIO

from src.data.s3_client import S3Client, S3Error
from tests.fixtures.s3_setup import (
    create_test_bucket,
    delete_test_bucket,
)


@pytest.fixture
def test_bucket_name(mock_aws_credentials, temp_env_vars):
    """Create a test bucket and return its name."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        OPENAI_API_KEY="test-key",
    )
    
    bucket_name = "test-vocabulator-bucket"
    
    # Create bucket
    create_test_bucket(bucket_name)
    
    yield bucket_name
    
    # Cleanup
    try:
        delete_test_bucket(bucket_name)
    except Exception:
        pass


@pytest.fixture
def s3_client(test_bucket_name):
    """Create an S3 client instance for testing."""
    return S3Client(bucket_name=test_bucket_name)


@pytest.mark.unit
@pytest.mark.aws
class TestS3Client:
    """Test suite for S3Client."""
    
    def test_upload_text_file(self, s3_client, test_bucket_name):
        """Test uploading a text file."""
        content = "This is a test transcript file."
        key = "transcripts/raw/STU-001/2025-11-10-session1.txt"
        
        s3_client.upload(key=key, content=content.encode("utf-8"), content_type="text/plain")
        
        # Verify file exists
        downloaded = s3_client.download(key=key)
        assert downloaded.decode("utf-8") == content
    
    def test_upload_binary_file(self, s3_client):
        """Test uploading a binary file."""
        content = b"\x00\x01\x02\x03\x04"
        key = "reports/STU-001/profile.html"
        
        s3_client.upload(key=key, content=content, content_type="text/html")
        
        # Verify file exists
        downloaded = s3_client.download(key=key)
        assert downloaded == content
    
    def test_download_file(self, s3_client, test_bucket_name):
        """Test downloading a file."""
        # Upload first
        content = "Test content"
        key = "test-download.txt"
        
        s3_client.upload(key=key, content=content.encode("utf-8"))
        
        # Download
        downloaded = s3_client.download(key=key)
        assert downloaded.decode("utf-8") == content
    
    def test_download_nonexistent_file(self, s3_client):
        """Test downloading a nonexistent file raises error."""
        with pytest.raises(S3Error):
            s3_client.download(key="nonexistent-file.txt")
    
    def test_list_files(self, s3_client):
        """Test listing files in a prefix."""
        # Upload multiple files
        files = [
            "transcripts/raw/STU-001/2025-11-10-session1.txt",
            "transcripts/raw/STU-001/2025-11-10-session2.txt",
            "transcripts/raw/STU-002/2025-11-10-session1.txt",
        ]
        
        for key in files:
            s3_client.upload(key=key, content=b"test content")
        
        # List files for STU-001
        listed = s3_client.list(prefix="transcripts/raw/STU-001/")
        
        assert len(listed) == 2
        assert all("STU-001" in key for key in listed)
    
    def test_list_empty_prefix(self, s3_client):
        """Test listing files with no matches returns empty list."""
        listed = s3_client.list(prefix="nonexistent/prefix/")
        assert listed == []
    
    def test_delete_file(self, s3_client):
        """Test deleting a file."""
        # Upload first
        key = "test-delete.txt"
        s3_client.upload(key=key, content=b"test content")
        
        # Delete
        s3_client.delete(key=key)
        
        # Verify deleted
        with pytest.raises(S3Error):
            s3_client.download(key=key)
    
    def test_delete_nonexistent_file(self, s3_client):
        """Test deleting a nonexistent file raises error."""
        with pytest.raises(S3Error):
            s3_client.delete(key="nonexistent-file.txt")
    
    def test_multipart_upload_large_file(self, s3_client):
        """Test multipart upload for large files."""
        # Create a file larger than 5MB (multipart threshold)
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        key = "large-file.txt"
        
        s3_client.upload(key=key, content=large_content, multipart_threshold=5 * 1024 * 1024)
        
        # Verify file uploaded correctly
        downloaded = s3_client.download(key=key)
        assert len(downloaded) == len(large_content)
        assert downloaded == large_content
    
    def test_generate_presigned_url(self, s3_client):
        """Test generating a presigned URL."""
        # Upload a file first
        key = "test-presigned.txt"
        s3_client.upload(key=key, content=b"test content")
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(key=key, expiration=3600)
        
        assert url.startswith("http")
        assert key in url or "test-presigned" in url
    
    def test_generate_presigned_url_nonexistent(self, s3_client):
        """Test generating presigned URL for nonexistent file."""
        # Should still generate URL (S3 doesn't validate existence)
        url = s3_client.generate_presigned_url(key="nonexistent.txt", expiration=3600)
        assert url.startswith("http")
    
    def test_build_path(self, s3_client):
        """Test building S3 paths according to bucket structure."""
        # Test transcript raw path
        path = s3_client.build_path(
            category="transcripts",
            subcategory="raw",
            student_id="STU-001",
            filename="2025-11-10-session1.txt",
        )
        assert path == "transcripts/raw/STU-001/2025-11-10-session1.txt"
        
        # Test report path
        path = s3_client.build_path(
            category="reports",
            student_id="STU-002",
            filename="profile.html",
        )
        assert path == "reports/STU-002/profile.html"
    
    def test_upload_with_metadata(self, s3_client):
        """Test uploading file with custom metadata."""
        key = "test-metadata.txt"
        metadata = {
            "student-id": "STU-001",
            "grade-level": "7",
        }
        
        s3_client.upload(
            key=key,
            content=b"test",
            metadata=metadata,
        )
        
        # Verify metadata was set (by checking object exists)
        # Note: Full metadata retrieval would require additional S3 API call
        downloaded = s3_client.download(key=key)
        assert downloaded == b"test"

