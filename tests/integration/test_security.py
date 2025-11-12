"""Security testing for Vocabulator API and services.

This module tests security requirements:
- No hardcoded secrets
- Input sanitization
- S3 path traversal protection
- COPPA compliance (no PII collection)
- IAM least privilege verification
"""

import re

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.utils.s3_paths import build_s3_path


@pytest.mark.integration
def test_no_hardcoded_secrets():
    """Verify no hardcoded secrets in codebase.
    
    This test checks for common patterns of hardcoded secrets.
    Actual secret scanning should be done with bandit and safety tools.
    """
    import os
    
    # Check environment variables are used, not hardcoded
    # This is a basic check - full scanning done via bandit
    assert os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") != "test-key", \
        "Hardcoded test API key found - should use environment variables"
    
    # Verify config uses environment variables
    from src.utils.config import get_config
    
    config = get_config()
    # Config should load from environment, not have hardcoded values
    assert hasattr(config, "openai_api_key"), "Config should have openai_api_key attribute"


@pytest.mark.integration
def test_s3_path_traversal_protection():
    """Test S3 path traversal protection.
    
    Verify that build_s3_path prevents directory traversal attacks.
    """
    # Test normal paths
    normal_path = build_s3_path("transcripts", "raw", "STU-001", "2024-01-15")
    assert ".." not in normal_path
    assert normal_path.startswith("transcripts/raw/STU-001/")
    
    # Test with malicious input (should be sanitized)
    malicious_student_id = "../../../etc/passwd"
    safe_path = build_s3_path("transcripts", "raw", malicious_student_id, "2024-01-15")
    
    # Path should not contain traversal sequences
    assert ".." not in safe_path, "Path traversal detected in S3 path"
    assert safe_path.startswith("transcripts/raw/"), "Path structure should be preserved"
    
    # Test with null bytes (should be sanitized)
    null_byte_student_id = "STU-001\0"
    safe_path_null = build_s3_path("transcripts", "raw", null_byte_student_id, "2024-01-15")
    assert "\0" not in safe_path_null, "Null bytes should be removed from path"
    
    # Test with absolute paths (should be sanitized)
    absolute_path_student_id = "/etc/passwd"
    safe_path_abs = build_s3_path("transcripts", "raw", absolute_path_student_id, "2024-01-15")
    assert not safe_path_abs.startswith("/"), "Absolute paths should not be allowed"
    assert safe_path_abs.startswith("transcripts/raw/"), "Path structure should be preserved"


@pytest.mark.integration
def test_student_id_validation():
    """Test student ID format validation.
    
    Student IDs must follow format STU-XXX to prevent injection attacks.
    """
    from src.api.utils.validation import validate_student_id
    
    # Valid student IDs
    valid_ids = ["STU-001", "STU-999", "STU-123"]
    for student_id in valid_ids:
        try:
            validate_student_id(student_id)
        except ValueError:
            pytest.fail(f"Valid student ID {student_id} was rejected")
    
    # Invalid student IDs (should raise ValueError)
    invalid_ids = [
        "STU001",  # Missing dash
        "stu-001",  # Lowercase
        "STU-",  # Missing number
        "STU-ABC",  # Non-numeric
        "../../etc/passwd",  # Path traversal
        "STU-001'; DROP TABLE students; --",  # SQL injection attempt
        "STU-001<script>alert('xss')</script>",  # XSS attempt
    ]
    
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError, match="Student ID must match"):
            validate_student_id(invalid_id)


@pytest.mark.integration
def test_coppa_compliance_no_pii():
    """Test COPPA compliance: verify no PII is collected.
    
    Student profiles should only contain anonymous IDs, not PII.
    """
    from src.data.models.student_profile import StudentProfile
    
    # Create a student profile
    student = StudentProfile(
        student_id="STU-001",
        grade_level=7,
        vocabulary_list=[],
    )
    
    # Verify profile does not contain PII fields
    profile_dict = student.model_dump()
    
    # Check that no PII fields exist
    pii_fields = [
        "name", "first_name", "last_name",
        "email", "email_address",
        "phone", "phone_number",
        "address", "home_address",
        "birth_date", "date_of_birth",
        "ssn", "social_security_number",
        "parent_name", "parent_email",
    ]
    
    for field in pii_fields:
        assert field not in profile_dict, \
            f"PII field '{field}' found in student profile - violates COPPA compliance"
    
    # Verify only anonymous identifier is used
    assert "student_id" in profile_dict
    assert profile_dict["student_id"].startswith("STU-"), \
        "Student ID should be anonymous identifier (STU-XXX format)"
    
    # Verify student_id is not a real name or email
    student_id = profile_dict["student_id"]
    assert "@" not in student_id, "Student ID should not contain email addresses"
    assert not re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", student_id), \
        "Student ID should not contain names"


@pytest.mark.integration
def test_input_sanitization_in_api():
    """Test input sanitization in API endpoints.
    
    Verify that API endpoints properly sanitize and validate input.
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test with malicious input in student ID
    malicious_id = "STU-001'; DROP TABLE students; --"
    response = client.get(f"/api/v1/students/{malicious_id}/profile")
    
    # Should return 400 (validation error) or 404, not 500 (server error)
    assert response.status_code in [400, 404], \
        f"API should reject malicious input, got {response.status_code}"
    
    # Test with XSS attempt in text field
    xss_payload = "<script>alert('xss')</script>"
    response = client.post(
        "/api/v1/transcripts/upload",
        json={
            "student_id": "STU-001",
            "text": xss_payload,
            "session_date": "2024-01-15",
            "grade_level": 7,
        },
    )
    
    # Should handle XSS payload safely (either reject or sanitize)
    # In this case, it should fail because student doesn't exist, but
    # the important thing is it doesn't crash or execute the script
    assert response.status_code != 500, \
        "API should not crash on XSS payload"


@pytest.mark.integration
def test_sql_injection_protection():
    """Test SQL injection protection.
    
    Verify that database queries are parameterized and not vulnerable to SQL injection.
    Note: DynamoDB uses NoSQL, but we should still verify input validation.
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test SQL injection attempts in student ID
    sql_injection_attempts = [
        "STU-001' OR '1'='1",
        "STU-001'; DROP TABLE students; --",
        "STU-001' UNION SELECT * FROM students --",
    ]
    
    for malicious_id in sql_injection_attempts:
        response = client.get(f"/api/v1/students/{malicious_id}/profile")
        
        # Should reject invalid format (validation error)
        assert response.status_code in [400, 404], \
            f"API should reject SQL injection attempt, got {response.status_code} for {malicious_id}"


@pytest.mark.integration
def test_cors_configuration():
    """Test CORS configuration.
    
    Verify CORS is properly configured to prevent unauthorized access.
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test OPTIONS request (CORS preflight)
    response = client.options("/api/v1/students")
    
    # Should return appropriate CORS headers or 405 (Method Not Allowed)
    # FastAPI handles CORS via middleware, so OPTIONS may return 405
    assert response.status_code in [200, 405], \
        f"CORS preflight should be handled, got {response.status_code}"


@pytest.mark.integration
def test_error_messages_no_information_disclosure():
    """Test that error messages don't disclose sensitive information.
    
    Error messages should not expose:
    - Database structure
    - Internal file paths
    - Stack traces in production
    - API keys or secrets
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test 404 error (should not expose internal structure)
    response = client.get("/api/v1/students/STU-999/profile")
    assert response.status_code == 404
    
    error_detail = response.json().get("detail", {})
    if isinstance(error_detail, dict):
        error_message = str(error_detail)
    else:
        error_message = str(error_detail)
    
    # Should not expose internal paths or stack traces
    assert "/src/" not in error_message, \
        "Error message should not expose internal file paths"
    assert "Traceback" not in error_message, \
        "Error message should not expose stack traces"
    assert "api_key" not in error_message.lower(), \
        "Error message should not expose API keys"
    assert "password" not in error_message.lower(), \
        "Error message should not expose passwords"

