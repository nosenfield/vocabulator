"""DynamoDB client wrapper with retry logic and error handling.

This module provides a high-level interface for DynamoDB operations with
automatic retry on throttling errors, connection pooling, and consistent
error handling.
"""

import random
import re
import time
import warnings
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("data.dynamodb")


class DynamoDBError(Exception):
    """Base exception for DynamoDB operations."""

    pass


class DynamoDBClient:
    """DynamoDB client wrapper with retry logic and error handling.
    
    This client provides a high-level interface for DynamoDB operations
    with automatic retry on throttling errors, exponential backoff, and
    consistent error handling.
    
    Attributes:
        table_name: Name of the DynamoDB table
        table: boto3 Table resource instance
    """

    def __init__(self, table_name: str):
        """Initialize DynamoDB client.
        
        Args:
            table_name: Name of the DynamoDB table to interact with
            
        Raises:
            DynamoDBError: If table cannot be accessed
        """
        self.table_name = table_name
        config = get_config()
        
        # Configure boto3 with retry logic
        boto_config = Config(
            region_name=config.aws_region,
            retries={
                "max_attempts": 3,
                "mode": "adaptive",  # Adaptive retry mode
            },
            max_pool_connections=50,
        )
        
        # Create DynamoDB resource
        endpoint_url = config.get_aws_endpoint_url()
        if endpoint_url:
            # LocalStack requires explicit credentials
            self.dynamodb = boto3.resource(
                "dynamodb",
                endpoint_url=endpoint_url,
                config=boto_config,
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
            )
        else:
            # Production: Use IAM roles (no explicit credentials)
            self.dynamodb = boto3.resource("dynamodb", config=boto_config)
        
        # Get table reference
        try:
            self.table = self.dynamodb.Table(table_name)
            # Verify table exists by loading metadata
            self.table.load()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                raise DynamoDBError(
                    f"Table '{table_name}' not found. "
                    "Please create the table first."
                ) from e
            raise DynamoDBError(f"Failed to access table '{table_name}': {e}") from e

    def _retry_with_backoff(self, operation, max_retries: int = 3, *args, **kwargs) -> Any:
        """Execute operation with exponential backoff retry.
        
        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of the operation
            
        Raises:
            DynamoDBError: If operation fails after all retries
        """
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                
                # Retry on throttling errors
                if error_code in ["ProvisionedThroughputExceededException", "ThrottlingException"]:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.random()  # Exponential backoff with jitter
                        logger.warning(
                            f"DynamoDB throttling detected, retrying in {wait_time:.2f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise DynamoDBError(
                            f"DynamoDB operation failed after {max_retries} retries: {e}"
                        ) from e
                else:
                    # Don't retry on other errors
                    raise DynamoDBError(f"DynamoDB operation failed: {e}") from e
        
        raise DynamoDBError(f"Operation failed after {max_retries} retries")

    def get_item(
        self,
        partition_key: str,
        partition_value: Any,
        sort_key: Optional[str] = None,
        sort_value: Optional[Any] = None,
        consistent_read: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get a single item from the table.
        
        Args:
            partition_key: Name of the partition key attribute
            partition_value: Value of the partition key
            sort_key: Optional name of the sort key attribute
            sort_value: Optional value of the sort key
            consistent_read: Whether to use strongly consistent read
            
        Returns:
            Item dictionary if found, None otherwise
        """
        key = {partition_key: partition_value}
        if sort_key and sort_value is not None:
            key[sort_key] = sort_value
        
        response = self._retry_with_backoff(
            self.table.get_item,
            Key=key,
            ConsistentRead=consistent_read,
        )
        return response.get("Item")

    def put_item(self, item: Dict[str, Any]) -> None:
        """Put an item into the table.
        
        Args:
            item: Dictionary containing item attributes
        """
        self._retry_with_backoff(self.table.put_item, Item=item)

    def update_item(
        self,
        partition_key: str,
        partition_value: Any,
        update_expression: str,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        sort_key: Optional[str] = None,
        sort_value: Optional[Any] = None,
        return_values: str = "NONE",
    ) -> Optional[Dict[str, Any]]:
        """Update an item in the table.
        
        Args:
            partition_key: Name of the partition key attribute
            partition_value: Value of the partition key
            update_expression: Update expression (e.g., "SET #attr = :val")
            expression_attribute_names: Attribute name mappings
            expression_attribute_values: Attribute value mappings
            sort_key: Optional name of the sort key attribute
            sort_value: Optional value of the sort key
            return_values: What to return ("NONE", "ALL_OLD", "ALL_NEW", "UPDATED_OLD", "UPDATED_NEW")
            
        Returns:
            Updated item if return_values is set, None otherwise
        """
        key = {partition_key: partition_value}
        if sort_key and sort_value is not None:
            key[sort_key] = sort_value
        
        kwargs = {
            "Key": key,
            "UpdateExpression": update_expression,
            "ReturnValues": return_values,
        }
        
        if expression_attribute_names:
            kwargs["ExpressionAttributeNames"] = expression_attribute_names
        if expression_attribute_values:
            kwargs["ExpressionAttributeValues"] = expression_attribute_values
        
        response = self._retry_with_backoff(self.table.update_item, **kwargs)
        return response.get("Attributes")

    def delete_item(
        self,
        partition_key: str,
        partition_value: Any,
        sort_key: Optional[str] = None,
        sort_value: Optional[Any] = None,
    ) -> None:
        """Delete an item from the table.
        
        Args:
            partition_key: Name of the partition key attribute
            partition_value: Value of the partition key
            sort_key: Optional name of the sort key attribute
            sort_value: Optional value of the sort key
        """
        key = {partition_key: partition_value}
        if sort_key and sort_value is not None:
            key[sort_key] = sort_value
        
        self._retry_with_backoff(self.table.delete_item, Key=key)

    def batch_get_items(self, keys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch get multiple items from the table.
        
        DynamoDB batch_get_item can handle up to 100 items, but this method
        handles batching automatically for larger requests.
        
        Args:
            keys: List of key dictionaries (each dict has partition_key and optional sort_key)
            
        Returns:
            List of items found (may be fewer than requested if some don't exist)
        """
        if not keys:
            return []
        
        all_items = []
        batch_size = 100  # DynamoDB limit
        
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i : i + batch_size]
            
            response = self._retry_with_backoff(
                self.dynamodb.batch_get_item,
                RequestItems={
                    self.table_name: {
                        "Keys": batch_keys,
                    }
                },
            )
            
            items = response.get("Responses", {}).get(self.table_name, [])
            all_items.extend(items)
            
            # Handle unprocessed keys (shouldn't happen with retry logic, but handle anyway)
            unprocessed = response.get("UnprocessedKeys", {}).get(self.table_name)
            if unprocessed:
                unprocessed_count = len(unprocessed.get("Keys", []))
                raise DynamoDBError(
                    f"Batch get operation incomplete: {unprocessed_count} unprocessed keys "
                    f"remain for table '{self.table_name}'. This may indicate throttling or "
                    "capacity issues. Consider retrying the operation."
                )
        
        return all_items

    def batch_write_items(self, items: List[Dict[str, Any]]) -> None:
        """Batch write multiple items to the table.
        
        DynamoDB batch_write_item can handle up to 25 items per request, but this
        method handles batching automatically for larger requests.
        
        Args:
            items: List of item dictionaries to write
        """
        if not items:
            return
        
        batch_size = 25  # DynamoDB limit
        
        for i in range(0, len(items), batch_size):
            batch_items = items[i : i + batch_size]
            
            # Convert to write requests
            write_requests = [
                {"PutRequest": {"Item": item}} for item in batch_items
            ]
            
            response = self._retry_with_backoff(
                self.dynamodb.batch_write_item,
                RequestItems={
                    self.table_name: write_requests,
                },
            )
            
            # Handle unprocessed items (shouldn't happen with retry logic, but handle anyway)
            unprocessed = response.get("UnprocessedItems", {}).get(self.table_name)
            if unprocessed:
                unprocessed_count = len(unprocessed)
                raise DynamoDBError(
                    f"Batch write operation incomplete: {unprocessed_count} unprocessed items "
                    f"remain for table '{self.table_name}'. This may indicate throttling or "
                    "capacity issues. Consider retrying the operation."
                )

    def query(
        self,
        partition_key: Optional[str] = None,
        partition_value: Optional[Any] = None,
        key_condition_expression: Optional[Any] = None,
        sort_key: Optional[str] = None,
        sort_key_condition: Optional[str] = None,
        filter_expression: Optional[Any] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query items by partition key.
        
        This method supports two usage patterns:
        
        1. Simple API (backward compatible):
           query(partition_key="id", partition_value="value")
        
        2. Advanced API (recommended):
           from boto3.dynamodb.conditions import Key
           query(key_condition_expression=Key("id").eq("value"))
        
        Args:
            partition_key: Name of the partition key attribute (for simple API)
            partition_value: Value of the partition key (for simple API)
            key_condition_expression: boto3 Key condition expression (recommended).
                If provided, partition_key and partition_value are ignored.
            sort_key: Optional name of the sort key attribute (for simple API with sort_key_condition)
            sort_key_condition: DEPRECATED - Use key_condition_expression instead.
                Optional condition string for sort key (e.g., "begins_with(:prefix)").
                This parameter is kept for backward compatibility but may be removed in future versions.
            filter_expression: Optional filter expression (can be string or boto3 condition object)
            expression_attribute_values: Values for expressions
            expression_attribute_names: Attribute name mappings
            index_name: Optional GSI name to query
            limit: Optional limit on number of results
            
        Returns:
            List of matching items
            
        Raises:
            DynamoDBError: If query fails or invalid parameters provided
        """
        from boto3.dynamodb.conditions import Key
        
        # Build key condition expression
        if key_condition_expression is not None:
            # Advanced API: Use provided key condition directly
            key_condition = key_condition_expression
        elif partition_key is not None and partition_value is not None:
            # Simple API: Build key condition from partition key/value
            key_condition = Key(partition_key).eq(partition_value)
            
            # Build sort key condition if provided (backward compatibility)
            if sort_key_condition is not None:
                warnings.warn(
                    "The 'sort_key_condition' parameter is deprecated and will be removed in a "
                    "future version. Use 'key_condition_expression' with boto3 Key conditions instead. "
                    "Example: Key('pk').eq('value') & Key('sk').begins_with('prefix')",
                    DeprecationWarning,
                    stacklevel=2,
                )
            
            if sort_key and sort_key_condition and expression_attribute_values:
                # Parse simple conditions like "begins_with(:prefix)" or "between(:start, :end)"
                if sort_key_condition.startswith("begins_with"):
                    match = re.search(r":(\w+)", sort_key_condition)
                    if match:
                        prefix_key = match.group(1)
                        if prefix_key in expression_attribute_values:
                            prefix = expression_attribute_values[prefix_key]
                            key_condition = key_condition & Key(sort_key).begins_with(prefix)
                elif sort_key_condition.startswith("between"):
                    matches = re.findall(r":(\w+)", sort_key_condition)
                    if len(matches) == 2 and all(m in expression_attribute_values for m in matches):
                        start = expression_attribute_values[matches[0]]
                        end = expression_attribute_values[matches[1]]
                        key_condition = key_condition & Key(sort_key).between(start, end)
                elif sort_key_condition.startswith(">="):
                    match = re.search(r":(\w+)", sort_key_condition)
                    if match and match.group(1) in expression_attribute_values:
                        value = expression_attribute_values[match.group(1)]
                        key_condition = key_condition & Key(sort_key).gte(value)
                elif sort_key_condition.startswith("<="):
                    match = re.search(r":(\w+)", sort_key_condition)
                    if match and match.group(1) in expression_attribute_values:
                        value = expression_attribute_values[match.group(1)]
                        key_condition = key_condition & Key(sort_key).lte(value)
        else:
            raise DynamoDBError(
                "Either key_condition_expression or (partition_key and partition_value) must be provided"
            )
        
        kwargs = {
            "KeyConditionExpression": key_condition,
        }
        
        if filter_expression:
            kwargs["FilterExpression"] = filter_expression
        if expression_attribute_values:
            kwargs["ExpressionAttributeValues"] = expression_attribute_values
        if expression_attribute_names:
            kwargs["ExpressionAttributeNames"] = expression_attribute_names
        if index_name:
            kwargs["IndexName"] = index_name
        if limit:
            kwargs["Limit"] = limit
        
        response = self._retry_with_backoff(self.table.query, **kwargs)
        return response.get("Items", [])

    def scan(
        self,
        filter_expression: Optional[Any] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Scan the entire table.
        
        Note: Scan operations are expensive and slow. Use query() when possible.
        
        Args:
            filter_expression: Optional filter expression (can be string or boto3 condition object)
            expression_attribute_values: Values for expressions
            expression_attribute_names: Attribute name mappings
            limit: Optional limit on number of results
            
        Returns:
            List of items matching the scan criteria
        """
        kwargs = {}
        
        if filter_expression:
            kwargs["FilterExpression"] = filter_expression
        if expression_attribute_values:
            kwargs["ExpressionAttributeValues"] = expression_attribute_values
        if expression_attribute_names:
            kwargs["ExpressionAttributeNames"] = expression_attribute_names
        if limit:
            kwargs["Limit"] = limit
        
        response = self._retry_with_backoff(self.table.scan, **kwargs)
        items = response.get("Items", [])
        
        # Handle pagination
        while "LastEvaluatedKey" in response:
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = self._retry_with_backoff(self.table.scan, **kwargs)
            items.extend(response.get("Items", []))
        
        return items

