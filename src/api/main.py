"""FastAPI application for Vocabulator API.

This module initializes the FastAPI application with dependency injection,
middleware, and route registration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


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


# Import routes
from src.api.routes import profiles, upload

# Register route routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
# app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
# app.include_router(batch.router, prefix="/api/v1", tags=["batch"])

