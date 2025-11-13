"""S3 test fixtures and setup utilities.

This module provides fixtures and utilities for setting up S3 buckets
for testing, using LocalStack for local development.
"""

import boto3
from botocore.exceptions import ClientError
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.utils.config import get_config

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client as Boto3S3Client
else:
    Boto3S3Client = Any


def create_s3_client() -> Boto3S3Client:
    """Create an S3 client configured for testing.
    
    Uses LocalStack endpoint if available, otherwise uses default AWS config.
    
    Returns:
        boto3 S3 client instance
    """
    config = get_config()
    endpoint_url = config.get_aws_endpoint_url()
    
    if endpoint_url:
        # LocalStack requires explicit credentials
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )
    else:
        # Production: Use IAM roles (no explicit credentials)
        return boto3.client("s3", region_name=config.aws_region)


def create_test_bucket(bucket_name: str) -> None:
    """Create a test S3 bucket.
    
    Args:
        bucket_name: Name of the bucket to create
        
    Raises:
        ClientError: If bucket creation fails
    """
    client = create_s3_client()
    
    try:
        client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
            raise


def delete_test_bucket(bucket_name: str) -> None:
    """Delete a test S3 bucket and all its contents.
    
    Args:
        bucket_name: Name of the bucket to delete
    """
    client = create_s3_client()
    try:
        # List and delete all objects
        paginator = client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)
        
        for page in pages:
            if "Contents" in page:
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                if objects:
                    client.delete_objects(
                        Bucket=bucket_name,
                        Delete={"Objects": objects},
                    )
        
        # Delete bucket
        client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchBucket":
            raise

