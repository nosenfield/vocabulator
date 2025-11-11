"""DynamoDB test fixtures and setup utilities.

This module provides fixtures and utilities for setting up DynamoDB tables
for testing, using LocalStack for local development.
"""

import boto3
from botocore.exceptions import ClientError
from typing import Any, Optional

from src.utils.config import get_config


def create_dynamodb_client() -> Any:
    """Create a DynamoDB client configured for testing.
    
    Uses LocalStack endpoint if available, otherwise uses default AWS config.
    
    Returns:
        boto3 DynamoDB client instance
    """
    config = get_config()
    endpoint_url = config.get_aws_endpoint_url()
    
    if endpoint_url:
        return boto3.client(
            "dynamodb",
            endpoint_url=endpoint_url,
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )
    else:
        return boto3.client("dynamodb", region_name=config.aws_region)


def create_dynamodb_resource() -> Any:
    """Create a DynamoDB resource configured for testing.
    
    Uses LocalStack endpoint if available, otherwise uses default AWS config.
    
    Returns:
        boto3 DynamoDB resource instance
    """
    config = get_config()
    endpoint_url = config.get_aws_endpoint_url()
    
    if endpoint_url:
        return boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            region_name=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )
    else:
        return boto3.resource("dynamodb", region_name=config.aws_region)


def create_test_table(
    table_name: str,
    partition_key: str,
    sort_key: Optional[str] = None,
    gsi: Optional[dict] = None,
) -> None:
    """Create a test DynamoDB table.
    
    Args:
        table_name: Name of the table to create
        partition_key: Name of the partition key attribute
        sort_key: Optional name of the sort key attribute
        gsi: Optional GSI definition with keys:
            - index_name: Name of the GSI
            - partition_key: GSI partition key
            - sort_key: Optional GSI sort key
    
    Raises:
        ClientError: If table creation fails
    """
    client = create_dynamodb_client()
    
    key_schema = [
        {"AttributeName": partition_key, "KeyType": "HASH"},
    ]
    
    attribute_definitions = [
        {"AttributeName": partition_key, "AttributeType": "S"},
    ]
    
    if sort_key:
        key_schema.append({"AttributeName": sort_key, "KeyType": "RANGE"})
        attribute_definitions.append({"AttributeName": sort_key, "AttributeType": "N"})
    
    # Add GSI if provided
    global_secondary_indexes = []
    if gsi:
        gsi_key_schema = [
            {"AttributeName": gsi["partition_key"], "KeyType": "HASH"},
        ]
        if gsi.get("sort_key"):
            gsi_key_schema.append({"AttributeName": gsi["sort_key"], "KeyType": "RANGE"})
            attribute_definitions.append(
                {"AttributeName": gsi["sort_key"], "AttributeType": "N"}
            )
        
        attribute_definitions.append(
            {"AttributeName": gsi["partition_key"], "AttributeType": "N"}
        )
        
        global_secondary_indexes.append({
            "IndexName": gsi["index_name"],
            "KeySchema": gsi_key_schema,
            "Projection": {"ProjectionType": "ALL"},
        })
    
    try:
        create_kwargs = {
            "TableName": table_name,
            "KeySchema": key_schema,
            "AttributeDefinitions": attribute_definitions,
            "BillingMode": "PAY_PER_REQUEST",
        }
        if global_secondary_indexes:
            create_kwargs["GlobalSecondaryIndexes"] = global_secondary_indexes
        
        client.create_table(**create_kwargs)
        
        # Wait for table to be active
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=table_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise


def delete_test_table(table_name: str) -> None:
    """Delete a test DynamoDB table.
    
    Args:
        table_name: Name of the table to delete
    """
    client = create_dynamodb_client()
    try:
        client.delete_table(TableName=table_name)
        waiter = client.get_waiter("table_not_exists")
        waiter.wait(TableName=table_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

