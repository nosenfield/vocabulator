"""Request models for API endpoints.

This module defines Pydantic models for validating incoming API requests.
"""

import re
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class TranscriptUploadRequest(BaseModel):
    """Request model for transcript upload.
    
    Attributes:
        student_id: Anonymous student identifier (format: STU-XXX)
        text: Transcript text content (10-50000 characters)
        session_date: Date of the recorded session
        grade_level: Student grade level (6-8)
    """
    
    student_id: str = Field(
        ...,
        pattern=r"^STU-\d{3}$",
        description="Student identifier (format: STU-001)",
        examples=["STU-001"],
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Transcript text content",
    )
    session_date: date = Field(
        ...,
        description="Date of the recorded session",
    )
    grade_level: int = Field(
        ...,
        ge=6,
        le=8,
        description="Student grade level (6-8)",
    )
    
    @field_validator("text")
    @classmethod
    def text_must_contain_words(cls, v: str) -> str:
        """Validate text contains actual words."""
        if not any(c.isalpha() for c in v):
            raise ValueError("Text must contain alphabetic characters")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU-001",
                "text": "Today we learned about photosynthesis and how plants convert sunlight into energy.",
                "session_date": "2025-11-10",
                "grade_level": 7,
            }
        }
    )


class WritingUploadRequest(BaseModel):
    """Request model for writing sample upload.
    
    Attributes:
        student_id: Anonymous student identifier (format: STU-XXX)
        text: Writing sample text content (10-50000 characters)
        assignment_id: Optional assignment identifier
        grade_level: Student grade level (6-8)
    """
    
    student_id: str = Field(
        ...,
        pattern=r"^STU-\d{3}$",
        description="Student identifier (format: STU-001)",
        examples=["STU-001"],
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Writing sample text content",
    )
    assignment_id: Optional[str] = Field(
        default=None,
        description="Optional assignment identifier",
    )
    grade_level: int = Field(
        ...,
        ge=6,
        le=8,
        description="Student grade level (6-8)",
    )
    
    @field_validator("text")
    @classmethod
    def text_must_contain_words(cls, v: str) -> str:
        """Validate text contains actual words."""
        if not any(c.isalpha() for c in v):
            raise ValueError("Text must contain alphabetic characters")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU-001",
                "text": "In my essay, I will discuss the importance of vocabulary in academic success.",
                "assignment_id": "ASSIGN-001",
                "grade_level": 7,
            }
        }
    )


class CreateStudentRequest(BaseModel):
    """Request model for creating a new student profile.
    
    Attributes:
        student_id: Anonymous student identifier (format: STU-XXX)
        first_name: Student's first name
        last_initial: Student's last name initial (single uppercase letter)
        grade_level: Student grade level (6-8)
    """
    
    student_id: str = Field(
        ...,
        pattern=r"^STU-\d{3}$",
        description="Student identifier (format: STU-001)",
        examples=["STU-001"],
    )
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Student's first name",
    )
    last_initial: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1,
        description="Student's last name initial (single uppercase letter)",
    )
    grade_level: int = Field(
        ...,
        ge=6,
        le=8,
        description="Student grade level (6-8)",
    )
    
    @field_validator("last_initial")
    @classmethod
    def validate_last_initial(cls, v: Optional[str]) -> Optional[str]:
        """Validate last initial is a single uppercase letter."""
        if v is not None:
            if not v.isalpha() or not v.isupper():
                raise ValueError("last_initial must be a single uppercase letter (A-Z)")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU-001",
                "first_name": "Alex",
                "last_initial": "S",
                "grade_level": 7,
            }
        }
    )


class UpdateStudentRequest(BaseModel):
    """Request model for updating a student profile.
    
    All fields are optional for partial updates.
    
    Attributes:
        first_name: Student's first name
        last_initial: Student's last name initial (single uppercase letter)
        grade_level: Student grade level (6-8)
    """
    
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Student's first name",
    )
    last_initial: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1,
        description="Student's last name initial (single uppercase letter)",
    )
    grade_level: Optional[int] = Field(
        default=None,
        ge=6,
        le=8,
        description="Student grade level (6-8)",
    )
    
    @field_validator("last_initial")
    @classmethod
    def validate_last_initial(cls, v: Optional[str]) -> Optional[str]:
        """Validate last initial is a single uppercase letter."""
        if v is not None:
            if not v.isalpha() or not v.isupper():
                raise ValueError("last_initial must be a single uppercase letter (A-Z)")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Alex",
                "last_initial": "S",
                "grade_level": 8,
            }
        }
    )


class UpdateRecommendationStatusRequest(BaseModel):
    """Request model for updating recommendation status.
    
    Attributes:
        status: New status (pending, assigned, learned)
    """
    
    status: str = Field(
        ...,
        description="New recommendation status",
        examples=["assigned"],
    )
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of the allowed values."""
        allowed_statuses = ["pending", "assigned", "learned"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "assigned",
            }
        }
    )


class BatchProcessRequest(BaseModel):
    """Request model for batch processing job submission.
    
    Attributes:
        student_ids: List of student IDs to process
        s3_paths: List of S3 paths to transcript files (must match student_ids length)
        grade_level: Grade level for all students in batch
    """
    
    student_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of student IDs to process",
    )
    s3_paths: List[str] = Field(
        ...,
        min_length=1,
        description="List of S3 paths to transcript files",
    )
    grade_level: int = Field(
        ...,
        ge=6,
        le=8,
        description="Grade level for all students in batch",
    )
    
    @field_validator("s3_paths")
    @classmethod
    def validate_paths_match_students(cls, v: List[str], info: ValidationInfo) -> List[str]:
        """Validate that s3_paths length matches student_ids length."""
        if info.data and "student_ids" in info.data:
            if len(v) != len(info.data["student_ids"]):
                raise ValueError("s3_paths length must match student_ids length")
        return v
    
    @field_validator("student_ids")
    @classmethod
    def validate_student_ids_format(cls, v: List[str]) -> List[str]:
        """Validate all student IDs match the required format."""
        pattern = r"^STU-\d{3}$"
        for student_id in v:
            if not re.match(pattern, student_id):
                raise ValueError(f"Invalid student ID format: {student_id}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_ids": ["STU-001", "STU-002"],
                "s3_paths": [
                    "s3://bucket/transcripts/STU-001.txt",
                    "s3://bucket/transcripts/STU-002.txt",
                ],
                "grade_level": 7,
            }
        }
    )

