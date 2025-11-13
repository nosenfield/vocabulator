"""Data layer module for Vocabulator.

This module provides data access abstractions including DynamoDB and S3 clients.
"""

from src.data.dynamodb_client import DynamoDBClient, DynamoDBError

__all__ = ["DynamoDBClient", "DynamoDBError"]

