"""FastAPI dependency injection functions.

This module provides dependency injection functions for FastAPI routes,
avoiding circular imports by separating dependencies from main app setup.
"""

from typing import Generator

from src.data.dynamodb_client import DynamoDBClient
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.data.s3_client import S3Client
from src.processing.batch_client import BatchClient
from src.processing.text_processing_pipeline import TextProcessingPipeline
from src.utils.logger import get_logger

logger = get_logger("api.dependencies")


def get_s3_client() -> Generator[S3Client, None, None]:
    """Provide S3 client as dependency.
    
    Yields:
        S3Client instance
    """
    client = S3Client()
    try:
        yield client
    finally:
        logger.debug("S3 client dependency cleanup")


def get_student_repository() -> Generator[StudentRepository, None, None]:
    """Provide student repository as dependency.
    
    Yields:
        StudentRepository instance
    """
    repo = StudentRepository()
    try:
        yield repo
    finally:
        logger.debug("Student repository dependency cleanup")


def get_recommendation_repository() -> Generator[RecommendationRepository, None, None]:
    """Provide recommendation repository as dependency.
    
    Yields:
        RecommendationRepository instance
    """
    repo = RecommendationRepository()
    try:
        yield repo
    finally:
        logger.debug("Recommendation repository dependency cleanup")


def get_text_processing_pipeline() -> Generator[TextProcessingPipeline, None, None]:
    """Provide text processing pipeline as dependency.
    
    Yields:
        TextProcessingPipeline instance
    """
    pipeline = TextProcessingPipeline()
    try:
        yield pipeline
    finally:
        logger.debug("Text processing pipeline dependency cleanup")


def get_batch_client() -> Generator[BatchClient, None, None]:
    """Provide batch client as dependency.
    
    Yields:
        BatchClient instance
    """
    client = BatchClient()
    try:
        yield client
    finally:
        logger.debug("Batch client dependency cleanup")


def get_dynamodb_client() -> Generator[DynamoDBClient, None, None]:
    """Provide DynamoDB client as dependency.
    
    Note: DynamoDBClient requires table_name. Use repositories instead,
    which handle client creation internally.
    
    Raises:
        NotImplementedError: If called without proper setup
    """
    raise NotImplementedError(
        "DynamoDBClient requires table_name. Use repositories (StudentRepository, "
        "RecommendationRepository) instead, which handle client creation internally."
    )

