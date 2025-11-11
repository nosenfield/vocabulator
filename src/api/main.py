"""FastAPI application for Vocabulator API.

This module initializes the FastAPI application with dependency injection,
middleware, and route registration.
"""

from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.data.dynamodb_client import DynamoDBClient
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.data.s3_client import S3Client
from src.processing.batch_client import BatchClient
from src.processing.text_processing_pipeline import TextProcessingPipeline
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Vocabulator API")
    yield
    # Shutdown
    logger.info("Shutting down Vocabulator API")


# Initialize FastAPI application
app = FastAPI(
    title="Vocabulator API",
    description="Personalized Vocabulary Recommendation Engine for Middle School Students",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
config = get_config()
cors_origins = config.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else [],  # Empty list = no CORS in production unless configured
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# Dependency Injection Functions
# Note: DynamoDBClient requires a table_name parameter, so direct usage is limited.
# Repositories (StudentRepository, RecommendationRepository) create their own clients.
# This dependency is kept for potential future use but may not be used directly in routes.
def get_dynamodb_client() -> Generator[DynamoDBClient, None, None]:
    """Provide DynamoDB client as dependency.
    
    Note: This dependency is not typically used directly as DynamoDBClient
    requires a table_name parameter. Repositories handle their own client creation.
    This is kept for potential future use.
    
    Yields:
        DynamoDBClient instance (requires table_name, so use repositories instead)
        
    Raises:
        ValueError: If called without proper setup (DynamoDBClient requires table_name)
    """
    # DynamoDBClient requires table_name, so this dependency is not directly usable
    # Repositories create their own clients internally
    raise NotImplementedError(
        "DynamoDBClient requires table_name. Use repositories (StudentRepository, "
        "RecommendationRepository) instead, which handle client creation internally."
    )


def get_s3_client() -> Generator[S3Client, None, None]:
    """Provide S3 client as dependency.
    
    Yields:
        S3Client instance
        
    Note:
        Client is automatically cleaned up after request completes.
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
    repository = StudentRepository()
    try:
        yield repository
    finally:
        logger.debug("Student repository dependency cleanup")


def get_recommendation_repository() -> Generator[RecommendationRepository, None, None]:
    """Provide recommendation repository as dependency.
    
    Yields:
        RecommendationRepository instance
    """
    repository = RecommendationRepository()
    try:
        yield repository
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Dictionary with status and timestamp
    """
    from datetime import datetime, timezone
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "vocabulator-api",
        "version": "1.0.0",
    }


# Import routes (will be created in subsequent tasks)
# from src.api.routes import upload, profiles, recommendations, batch

# Register route routers (will be uncommented as routes are created)
# app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
# app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
# app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
# app.include_router(batch.router, prefix="/api/v1", tags=["batch"])

