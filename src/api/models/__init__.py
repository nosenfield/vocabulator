"""API request and response models."""

from src.api.models.requests import (
    TranscriptUploadRequest,
    WritingUploadRequest,
    CreateStudentRequest,
    UpdateStudentRequest,
    UpdateRecommendationStatusRequest,
    BatchProcessRequest,
)
from src.api.models.responses import (
    TranscriptUploadResponse,
    WritingUploadResponse,
    StudentProfileResponse,
    StudentListItem,
    StudentsListResponse,
    RecommendationWordResponse,
    RecommendationsResponse,
    RecommendationStatusResponse,
    BatchProcessResponse,
    BatchStatusResponse,
    ErrorResponse,
)

__all__ = [
    # Request models
    "TranscriptUploadRequest",
    "WritingUploadRequest",
    "CreateStudentRequest",
    "UpdateStudentRequest",
    "UpdateRecommendationStatusRequest",
    "BatchProcessRequest",
    # Response models
    "TranscriptUploadResponse",
    "WritingUploadResponse",
    "StudentProfileResponse",
    "StudentListItem",
    "StudentsListResponse",
    "RecommendationWordResponse",
    "RecommendationsResponse",
    "RecommendationStatusResponse",
    "BatchProcessResponse",
    "BatchStatusResponse",
    "ErrorResponse",
]

