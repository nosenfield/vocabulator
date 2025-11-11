"""Unit tests for DynamoDB client wrapper.

Tests cover connection management, retry logic, error handling, and basic CRUD operations.
"""

import pytest
from botocore.exceptions import ClientError
from typing import Any, Dict

from src.data.dynamodb_client import DynamoDBClient, DynamoDBError
from tests.fixtures.dynamodb_setup import (
    create_test_table,
    delete_test_table,
    create_dynamodb_resource,
)


@pytest.fixture
def test_table_name(mock_aws_credentials, temp_env_vars):
    """Create a test table and return its name."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        OPENAI_API_KEY="test-key",
    )
    
    table_name = "test-dynamodb-client"
    
    # Create table
    create_test_table(
        table_name=table_name,
        partition_key="id",
        sort_key="version",
    )
    
    yield table_name
    
    # Cleanup
    try:
        delete_test_table(table_name)
    except Exception:
        pass


@pytest.fixture
def dynamodb_client(test_table_name):
    """Create a DynamoDB client instance for testing."""
    return DynamoDBClient(table_name=test_table_name)


@pytest.mark.unit
@pytest.mark.aws
class TestDynamoDBClient:
    """Test suite for DynamoDBClient."""
    
    def test_create_client(self, test_table_name):
        """Test creating a DynamoDB client."""
        client = DynamoDBClient(table_name=test_table_name)
        assert client.table_name == test_table_name
        assert client.table is not None
    
    def test_get_item_exists(self, dynamodb_client, test_table_name):
        """Test getting an item that exists."""
        # Put an item first
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        table.put_item(
            Item={
                "id": "test-1",
                "version": 1,
                "data": "test data",
            }
        )
        
        # Get the item
        item = dynamodb_client.get_item(
            partition_key="id",
            partition_value="test-1",
            sort_key="version",
            sort_value=1,
        )
        
        assert item is not None
        assert item["id"] == "test-1"
        assert item["version"] == 1
        assert item["data"] == "test data"
    
    def test_get_item_not_exists(self, dynamodb_client):
        """Test getting an item that doesn't exist."""
        item = dynamodb_client.get_item(
            partition_key="id",
            partition_value="nonexistent",
            sort_key="version",
            sort_value=1,
        )
        assert item is None
    
    def test_get_item_partition_key_only(self, dynamodb_client, test_table_name):
        """Test getting an item with only partition key."""
        # Create a table without sort key for this test
        table_name = "test-simple-table"
        create_test_table(
            table_name=table_name,
            partition_key="id",
        )
        
        try:
            client = DynamoDBClient(table_name=table_name)
            resource = create_dynamodb_resource()
            table = resource.Table(table_name)
            table.put_item(Item={"id": "test-1", "data": "test"})
            
            item = client.get_item(
                partition_key="id",
                partition_value="test-1",
            )
            
            assert item is not None
            assert item["id"] == "test-1"
        finally:
            delete_test_table(table_name)
    
    def test_put_item(self, dynamodb_client, test_table_name):
        """Test putting an item."""
        item = {
            "id": "test-2",
            "version": 1,
            "data": "new item",
        }
        
        dynamodb_client.put_item(item=item)
        
        # Verify it was saved
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        response = table.get_item(
            Key={"id": "test-2", "version": 1}
        )
        
        assert "Item" in response
        assert response["Item"]["data"] == "new item"
    
    def test_update_item(self, dynamodb_client, test_table_name):
        """Test updating an item."""
        # Put initial item
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        table.put_item(
            Item={
                "id": "test-3",
                "version": 1,
                "data": "original",
            }
        )
        
        # Update the item
        dynamodb_client.update_item(
            partition_key="id",
            partition_value="test-3",
            sort_key="version",
            sort_value=1,
            update_expression="SET #data = :new_data",
            expression_attribute_names={"#data": "data"},
            expression_attribute_values={":new_data": "updated"},
        )
        
        # Verify update
        response = table.get_item(Key={"id": "test-3", "version": 1})
        assert response["Item"]["data"] == "updated"
    
    def test_delete_item(self, dynamodb_client, test_table_name):
        """Test deleting an item."""
        # Put an item
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        table.put_item(
            Item={
                "id": "test-4",
                "version": 1,
                "data": "to delete",
            }
        )
        
        # Delete it
        dynamodb_client.delete_item(
            partition_key="id",
            partition_value="test-4",
            sort_key="version",
            sort_value=1,
        )
        
        # Verify deletion
        response = table.get_item(Key={"id": "test-4", "version": 1})
        assert "Item" not in response
    
    def test_batch_get_items(self, dynamodb_client, test_table_name):
        """Test batch getting multiple items."""
        # Put multiple items
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        
        items = [
            {"id": f"batch-{i}", "version": 1, "data": f"item-{i}"}
            for i in range(5)
        ]
        
        for item in items:
            table.put_item(Item=item)
        
        # Batch get
        keys = [
            {"id": f"batch-{i}", "version": 1}
            for i in range(5)
        ]
        
        results = dynamodb_client.batch_get_items(keys=keys)
        
        assert len(results) == 5
        # Verify all items are present (batch_get doesn't guarantee order)
        result_ids = {r["id"] for r in results}
        expected_ids = {f"batch-{i}" for i in range(5)}
        assert result_ids == expected_ids
        # Verify data matches
        for result in results:
            i = int(result["id"].split("-")[1])
            assert result["data"] == f"item-{i}"
    
    def test_batch_write_items(self, dynamodb_client, test_table_name):
        """Test batch writing multiple items."""
        items = [
            {"id": f"write-{i}", "version": 1, "data": f"write-item-{i}"}
            for i in range(5)
        ]
        
        dynamodb_client.batch_write_items(items=items)
        
        # Verify all items were written
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        
        for item in items:
            response = table.get_item(
                Key={"id": item["id"], "version": item["version"]}
            )
            assert "Item" in response
            assert response["Item"]["data"] == item["data"]
    
    def test_batch_write_large_batch(self, dynamodb_client, test_table_name):
        """Test batch writing more than 25 items (DynamoDB batch limit)."""
        # Create 30 items (more than DynamoDB's batch_write_item limit of 25)
        items = [
            {"id": f"large-{i}", "version": 1, "data": f"item-{i}"}
            for i in range(30)
        ]
        
        dynamodb_client.batch_write_items(items=items)
        
        # Verify all 30 items were written across multiple batches
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        
        for item in items:
            response = table.get_item(
                Key={"id": item["id"], "version": item["version"]}
            )
            assert "Item" in response
            assert response["Item"]["data"] == item["data"]
    
    def test_batch_write_empty_list(self, dynamodb_client):
        """Test batch writing empty list (should not fail)."""
        # Should not raise an exception
        dynamodb_client.batch_write_items(items=[])
    
    def test_query_by_partition_key(self, dynamodb_client, test_table_name):
        """Test querying items by partition key."""
        # Put multiple items with same partition key
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        
        for version in range(1, 4):
            table.put_item(
                Item={
                    "id": "query-test",
                    "version": version,
                    "data": f"version-{version}",
                }
            )
        
        # Query
        results = dynamodb_client.query(
            partition_key="id",
            partition_value="query-test",
        )
        
        assert len(results) == 3
        versions = sorted([r["version"] for r in results])
        assert versions == [1, 2, 3]
    
    def test_query_with_filter(self, dynamodb_client, test_table_name):
        """Test querying with filter expression."""
        from boto3.dynamodb.conditions import Attr
        
        # Put items
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        
        for version in range(1, 4):
            table.put_item(
                Item={
                    "id": "filter-test",
                    "version": version,
                    "data": f"version-{version}",
                    "status": "active" if version > 1 else "inactive",
                }
            )
        
        # Query with filter using boto3 Attr
        results = dynamodb_client.query(
            partition_key="id",
            partition_value="filter-test",
            filter_expression=Attr("status").eq("active"),
        )
        
        assert len(results) == 2
        assert all(r["status"] == "active" for r in results)
    
    def test_query_with_gsi(self, mock_aws_credentials, temp_env_vars):
        """Test querying using a Global Secondary Index (GSI)."""
        from boto3.dynamodb.conditions import Key
        
        temp_env_vars(
            DYNAMODB_TABLE_PREFIX="test",
            S3_BUCKET_NAME="test-bucket",
            OPENAI_API_KEY="test-key",
        )
        
        # Create a table with GSI (similar to StudentProfiles table design)
        table_name = "test-gsi-table"
        create_test_table(
            table_name=table_name,
            partition_key="student_id",
            sort_key="timestamp",
            gsi={
                "index_name": "grade_level-proficiency_score-index",
                "partition_key": "grade_level",
                "sort_key": "proficiency_score",
            },
        )
        
        try:
            client = DynamoDBClient(table_name=table_name)
            resource = create_dynamodb_resource()
            table = resource.Table(table_name)
            
            # Put items with GSI attributes
            items = [
                {
                    "student_id": f"student-{i}",
                    "timestamp": i,
                    "grade_level": 5,
                    "proficiency_score": 70 + i,
                    "data": f"item-{i}",
                }
                for i in range(1, 4)
            ]
            
            for item in items:
                table.put_item(Item=item)
            
            # Query using GSI with key_condition_expression
            results = client.query(
                key_condition_expression=Key("grade_level").eq(5) & Key("proficiency_score").gte(71),
                index_name="grade_level-proficiency_score-index",
            )
            
            # Should return items with proficiency_score >= 71
            assert len(results) == 2
            assert all(r["grade_level"] == 5 for r in results)
            assert all(r["proficiency_score"] >= 71 for r in results)
        finally:
            delete_test_table(table_name)
    
    def test_scan_table(self, dynamodb_client, test_table_name):
        """Test scanning the table."""
        # Put multiple items
        resource = create_dynamodb_resource()
        table = resource.Table(test_table_name)
        
        for i in range(5):
            table.put_item(
                Item={
                    "id": f"scan-{i}",
                    "version": 1,
                    "data": f"scan-item-{i}",
                }
            )
        
        # Scan (note: may return other test items, so check for at least our items)
        results = dynamodb_client.scan()
        
        scan_ids = [r["id"] for r in results if r["id"].startswith("scan-")]
        assert len(scan_ids) == 5
    
    def test_error_handling_not_found(self, dynamodb_client):
        """Test error handling for item not found."""
        # Should return None, not raise exception
        item = dynamodb_client.get_item(
            partition_key="id",
            partition_value="nonexistent",
            sort_key="version",
            sort_value=1,
        )
        assert item is None
    
    def test_error_handling_invalid_table(self, mock_aws_credentials, temp_env_vars):
        """Test error handling for invalid table name."""
        temp_env_vars(
            DYNAMODB_TABLE_PREFIX="test",
            S3_BUCKET_NAME="test-bucket",
            OPENAI_API_KEY="test-key",
        )
        with pytest.raises(DynamoDBError):
            DynamoDBClient(table_name="nonexistent-table")

