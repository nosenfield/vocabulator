"""Response models for API endpoints.

This module defines Pydantic models for API responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TranscriptUploadResponse(BaseModel):
    """Response model for transcript upload.
    
    Attributes:
        success: Whether upload was successful
        student_id: Student identifier
        words_extracted: Number of vocabulary words extracted
        profile_url: URL to view student profile
    """
    
    success: bool = Field(..., description="Whether upload was successful")
    student_id: str = Field(..., description="Student identifier")
    words_extracted: int = Field(..., ge=0, description="Number of vocabulary words extracted")
    profile_url: Optional[str] = Field(
        default=None,
        description="URL to view student profile",
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "student_id": "STU-001",
                "words_extracted": 15,
                "profile_url": "https://example.com/profile/STU-001",
            }
        }
    )


class WritingUploadResponse(BaseModel):
    """Response model for writing sample upload.
    
    Attributes:
        success: Whether upload was successful
        student_id: Student identifier
        words_extracted: Number of vocabulary words extracted
        assignment_id: Assignment identifier (if provided)
    """
    
    success: bool = Field(..., description="Whether upload was successful")
    student_id: str = Field(..., description="Student identifier")
    words_extracted: int = Field(..., ge=0, description="Number of vocabulary words extracted")
    assignment_id: Optional[str] = Field(
        default=None,
        description="Assignment identifier",
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "student_id": "STU-001",
                "words_extracted": 12,
                "assignment_id": "ASSIGN-001",
            }
        }
    )


class StudentProfileResponse(BaseModel):
    """Response model for student profile.
    
    Attributes:
        student_id: Student identifier
        grade_level: Student grade level (6-8)
        vocabulary_size: Number of unique vocabulary words
        proficiency_score: Calculated proficiency score (0-100)
        created_at: Profile creation timestamp
        last_updated: Last update timestamp
    """
    
    student_id: str = Field(..., description="Student identifier")
    grade_level: int = Field(..., ge=6, le=8, description="Student grade level")
    vocabulary_size: int = Field(..., ge=0, description="Number of unique vocabulary words")
    proficiency_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Proficiency score (0-100)",
    )
    created_at: datetime = Field(..., description="Profile creation timestamp")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU-001",
                "grade_level": 7,
                "vocabulary_size": 150,
                "proficiency_score": 75.5,
                "created_at": "2025-11-10T10:00:00Z",
                "last_updated": "2025-11-10T15:30:00Z",
            }
        }
    )


class StudentListItem(BaseModel):
    """Student list item for bulk queries.
    
    Attributes:
        student_id: Student identifier
        grade_level: Student grade level (6-8)
        vocabulary_size: Number of unique vocabulary words
        proficiency_score: Calculated proficiency score (0-100)
    """
    
    student_id: str = Field(..., description="Student identifier")
    grade_level: int = Field(..., ge=6, le=8, description="Student grade level")
    vocabulary_size: int = Field(..., ge=0, description="Number of unique vocabulary words")
    proficiency_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Proficiency score (0-100)",
    )


class StudentsListResponse(BaseModel):
    """Response model for student list query.
    
    Attributes:
        students: List of student profiles
        total: Total number of students
    """
    
    students: List[StudentListItem] = Field(..., description="List of student profiles")
    total: int = Field(..., ge=0, description="Total number of students")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "students": [
                    {
                        "student_id": "STU-001",
                        "grade_level": 7,
                        "vocabulary_size": 150,
                        "proficiency_score": 75.5,
                    }
                ],
                "total": 1,
            }
        }
    )


class RecommendationWordResponse(BaseModel):
    """Response model for a single recommended word.
    
    Attributes:
        word: The vocabulary word
        definition: Definition of the word
        grade_level: Grade level for this word (6-8)
        difficulty_score: Difficulty score (0.0-1.0)
        rationale: Explanation of why this word was recommended
        example_sentences: Example sentences using the word
    """
    
    word: str = Field(..., description="The vocabulary word")
    definition: str = Field(..., description="Definition of the word")
    grade_level: int = Field(..., ge=6, le=8, description="Grade level (6-8)")
    difficulty_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Difficulty score (0.0=easy, 1.0=hard)",
    )
    rationale: str = Field(..., description="Explanation of why this word was recommended")
    example_sentences: List[str] = Field(
        ...,
        description="Example sentences using the word",
    )


class RecommendationsResponse(BaseModel):
    """Response model for vocabulary recommendations.
    
    Attributes:
        student_id: Student identifier
        recommendation_date: Date when recommendation was generated (ISO 8601 date string)
        words: List of recommended words
        status: Current status of the recommendation
    """
    
    student_id: str = Field(..., description="Student identifier")
    recommendation_date: str = Field(
        ...,
        description="Date when recommendation was generated (ISO 8601 date string)",
    )
    words: List[RecommendationWordResponse] = Field(
        ...,
        description="List of recommended words",
    )
    status: str = Field(..., description="Current status (pending, assigned, learned)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU-001",
                "recommendation_date": "2025-11-10",
                "words": [
                    {
                        "word": "photosynthesis",
                        "definition": "The process by which plants convert light into energy",
                        "grade_level": 7,
                        "difficulty_score": 0.6,
                        "rationale": "Important for science curriculum",
                        "example_sentences": ["Plants use photosynthesis to make food."],
                    }
                ],
                "status": "pending",
            }
        }
    )


class RecommendationsListResponse(BaseModel):
    """Response model for recommendation list query.
    
    Attributes:
        recommendations: List of recommendations
        total: Total number of recommendations
    """
    
    recommendations: List[RecommendationsResponse] = Field(
        ..., description="List of recommendations"
    )
    total: int = Field(..., ge=0, description="Total number of recommendations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendations": [
                    {
                        "student_id": "STU-001",
                        "recommendation_date": "2025-11-10",
                        "words": [
                            {
                                "word": "analyze",
                                "definition": "To examine in detail",
                                "grade_level": 7,
                                "difficulty_score": 0.5,
                                "rationale": "High-frequency academic word",
                                "example_sentences": ["Let's analyze the data."],
                            }
                        ],
                        "status": "pending",
                    }
                ],
                "total": 1,
            }
        }
    )


class RecommendationStatusResponse(BaseModel):
    """Response model for recommendation status update.
    
    Attributes:
        success: Whether update was successful
        recommendation_id: Recommendation identifier
        status: Updated status
    """
    
    success: bool = Field(..., description="Whether update was successful")
    recommendation_id: str = Field(..., description="Recommendation identifier")
    status: str = Field(..., description="Updated status")


class BatchProcessResponse(BaseModel):
    """Response model for batch processing job submission.
    
    Attributes:
        success: Whether job submission was successful
        job_id: AWS Batch job ID
        message: Status message
    """
    
    success: bool = Field(..., description="Whether job submission was successful")
    job_id: str = Field(..., description="AWS Batch job ID")
    message: str = Field(..., description="Status message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "job_id": "job-123",
                "message": "Batch job submitted successfully",
            }
        }
    )


class BatchStatusResponse(BaseModel):
    """Response model for batch job status query.
    
    Attributes:
        job_id: AWS Batch job ID
        status: Current job status
        created_at: Job creation timestamp
        started_at: Job start timestamp (if started)
        stopped_at: Job completion timestamp (if completed)
        progress: Job progress percentage (0-100)
        error_message: Error message (if failed)
    """
    
    job_id: str = Field(..., description="AWS Batch job ID")
    status: str = Field(..., description="Current job status")
    created_at: Optional[datetime] = Field(
        default=None,
        description="Job creation timestamp",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Job start timestamp",
    )
    stopped_at: Optional[datetime] = Field(
        default=None,
        description="Job completion timestamp",
    )
    progress: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Job progress percentage (0-100)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message (if job failed)",
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job-123",
                "status": "RUNNING",
                "created_at": "2025-11-10T10:00:00Z",
                "started_at": "2025-11-10T10:01:00Z",
                "progress": 50,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response model.
    
    Attributes:
        error: Error type/code
        message: Human-readable error message
        details: Additional error details (optional)
    """
    
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(
        default=None,
        description="Additional error details",
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "validation_error",
                "message": "Invalid student ID format",
                "details": {"field": "student_id"},
            }
        }
    )

