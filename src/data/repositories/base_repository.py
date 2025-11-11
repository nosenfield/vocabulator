"""Base repository class for DynamoDB operations.

This module provides a base repository class that implements common CRUD
operations for DynamoDB tables, following the repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from src.data.dynamodb_client import DynamoDBClient, DynamoDBError
from src.utils.logger import get_logger

logger = get_logger("data.repositories")

# Type variable for the model type
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository class for DynamoDB operations.
    
    This class provides common CRUD operations that can be extended by
    specific repository implementations. It uses the DynamoDBClient for
    all database operations.
    
    Attributes:
        client: DynamoDBClient instance for this repository
        table_name: Name of the DynamoDB table
    """

    def __init__(self, table_name: str):
        """Initialize base repository.
        
        Args:
            table_name: Name of the DynamoDB table
        """
        self.client = DynamoDBClient(table_name=table_name)
        self.table_name = table_name
        logger.debug(f"Initialized repository for table: {table_name}")

    @abstractmethod
    def _item_to_model(self, item: Dict[str, Any]) -> T:
        """Convert DynamoDB item to model instance.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            Model instance
        """
        pass

    @abstractmethod
    def _model_to_item(self, model: T) -> Dict[str, Any]:
        """Convert model instance to DynamoDB item.
        
        Args:
            model: Model instance
            
        Returns:
            DynamoDB item dictionary
        """
        pass

    @abstractmethod
    def _get_partition_key(self) -> str:
        """Get the partition key attribute name.
        
        Returns:
            Partition key attribute name
        """
        pass

    @abstractmethod
    def _get_sort_key(self) -> Optional[str]:
        """Get the sort key attribute name (if table has one).
        
        Returns:
            Sort key attribute name, or None if table doesn't have sort key
        """
        pass

    def create(self, model: T) -> T:
        """Create a new item in the table.
        
        Args:
            model: Model instance to create
            
        Returns:
            Created model instance
        """
        item = self._model_to_item(model)
        self.client.put_item(item=item)
        logger.debug(f"Created item in {self.table_name}")
        return model

    def get(
        self,
        partition_value: Any,
        sort_value: Optional[Any] = None,
        consistent_read: bool = False,
    ) -> Optional[T]:
        """Get an item by its keys.
        
        Args:
            partition_value: Value of the partition key
            sort_value: Optional value of the sort key
            consistent_read: Whether to use strongly consistent read
            
        Returns:
            Model instance if found, None otherwise
        """
        sort_key = self._get_sort_key()
        
        item = self.client.get_item(
            partition_key=self._get_partition_key(),
            partition_value=partition_value,
            sort_key=sort_key,
            sort_value=sort_value,
            consistent_read=consistent_read,
        )
        
        if item is None:
            return None
        
        return self._item_to_model(item)

    def update(
        self,
        partition_value: Any,
        update_expression: str,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        sort_value: Optional[Any] = None,
        return_values: str = "ALL_NEW",
    ) -> Optional[T]:
        """Update an item in the table.
        
        Args:
            partition_value: Value of the partition key
            update_expression: Update expression (e.g., "SET #attr = :val")
            expression_attribute_names: Attribute name mappings
            expression_attribute_values: Attribute value mappings
            sort_value: Optional value of the sort key
            return_values: What to return ("NONE", "ALL_OLD", "ALL_NEW", etc.)
            
        Returns:
            Updated model instance if return_values is set, None otherwise
        """
        sort_key = self._get_sort_key()
        
        updated_item = self.client.update_item(
            partition_key=self._get_partition_key(),
            partition_value=partition_value,
            sort_key=sort_key,
            sort_value=sort_value,
            update_expression=update_expression,
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values,
            return_values=return_values,
        )
        
        if updated_item:
            return self._item_to_model(updated_item)
        return None

    def delete(self, partition_value: Any, sort_value: Optional[Any] = None) -> None:
        """Delete an item from the table.
        
        Args:
            partition_value: Value of the partition key
            sort_value: Optional value of the sort key
        """
        sort_key = self._get_sort_key()
        
        self.client.delete_item(
            partition_key=self._get_partition_key(),
            partition_value=partition_value,
            sort_key=sort_key,
            sort_value=sort_value,
        )
        
        logger.debug(f"Deleted item from {self.table_name}")

    def batch_get(self, keys: List[Dict[str, Any]]) -> List[T]:
        """Batch get multiple items.
        
        Args:
            keys: List of key dictionaries (each dict has partition_key and optional sort_key)
            
        Returns:
            List of model instances
        """
        items = self.client.batch_get_items(keys=keys)
        return [self._item_to_model(item) for item in items]

    def batch_create(self, models: List[T]) -> List[T]:
        """Batch create multiple items.
        
        Args:
            models: List of model instances to create
            
        Returns:
            List of created model instances
        """
        items = [self._model_to_item(model) for model in models]
        self.client.batch_write_items(items=items)
        logger.debug(f"Batch created {len(models)} items in {self.table_name}")
        return models

    def query(
        self,
        partition_value: Any,
        sort_key_condition: Optional[str] = None,
        filter_expression: Optional[Any] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[T]:
        """Query items by partition key.
        
        Args:
            partition_value: Value of the partition key
            sort_key_condition: Optional condition for sort key
            filter_expression: Optional filter expression (can be string or boto3 condition object)
            expression_attribute_values: Values for expressions
            expression_attribute_names: Attribute name mappings
            index_name: Optional GSI name to query
            limit: Optional limit on number of results
            
        Returns:
            List of matching model instances
        """
        items = self.client.query(
            partition_key=self._get_partition_key(),
            partition_value=partition_value,
            sort_key=self._get_sort_key(),
            sort_key_condition=sort_key_condition,
            filter_expression=filter_expression,
            expression_attribute_values=expression_attribute_values,
            expression_attribute_names=expression_attribute_names,
            index_name=index_name,
            limit=limit,
        )
        
        return [self._item_to_model(item) for item in items]

    def scan(
        self,
        filter_expression: Optional[Any] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[T]:
        """Scan the entire table.
        
        Note: Scan operations are expensive. Use query() when possible.
        
        Args:
            filter_expression: Optional filter expression (can be string or boto3 condition object)
            expression_attribute_values: Values for expressions
            expression_attribute_names: Attribute name mappings
            limit: Optional limit on number of results
            
        Returns:
            List of matching model instances
        """
        items = self.client.scan(
            filter_expression=filter_expression,
            expression_attribute_values=expression_attribute_values,
            expression_attribute_names=expression_attribute_names,
            limit=limit,
        )
        
        return [self._item_to_model(item) for item in items]

