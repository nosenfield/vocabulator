"""Lambda handler for Vocabulator API.

This module provides the AWS Lambda handler that wraps the FastAPI application
using Mangum ASGI adapter for serverless deployment.
"""

import os
from mangum import Mangum

from src.api.main import app
from src.utils.logger import get_logger

logger = get_logger("lambda_handler")

# Initialize Mangum adapter for Lambda
# lifespan="off" because Lambda containers are reused across invocations
# and we don't want to run startup/shutdown logic on every invocation
handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    """AWS Lambda handler wrapper with error handling and logging."""
    try:
        logger.info(
            "Lambda invocation started",
            extra={
                "request_id": event.get("requestContext", {}).get("requestId"),
                "path": event.get("path"),
                "http_method": event.get("httpMethod"),
            },
        )
        response = handler(event, context)
        logger.info("Lambda invocation completed successfully")
        return response
    except Exception as e:
        logger.error(
            "Lambda invocation failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise

