#!/usr/bin/env python3
"""Clear all items from DynamoDB tables.

This script deletes all items from all Vocabulator DynamoDB tables.
Use with caution - this operation cannot be undone!
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.exceptions import ClientError

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("scripts.clear_dynamodb")


def clear_table(table_name: str, dynamodb_resource) -> int:
    """Clear all items from a DynamoDB table.
    
    Args:
        table_name: Name of the table to clear
        dynamodb_resource: boto3 DynamoDB resource
        
    Returns:
        Number of items deleted
    """
    try:
        table = dynamodb_resource.Table(table_name)
        
        # Scan the table to get all items
        deleted_count = 0
        scan_kwargs = {}
        
        while True:
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            if not items:
                break
            
            # Delete items in batches (DynamoDB batch_write_item limit is 25)
            batch_size = 25
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                with table.batch_writer() as batch_writer:
                    for item in batch:
                        # Get the key attributes
                        key = {}
                        # StudentProfiles table has student_id and profile_version
                        if 'student_id' in item:
                            key['student_id'] = item['student_id']
                            if 'profile_version' in item:
                                key['profile_version'] = item['profile_version']
                        # VocabularyRecommendations has recommendation_id
                        elif 'recommendation_id' in item:
                            key['recommendation_id'] = item['recommendation_id']
                        # CommonCoreVocabulary has word and grade_level
                        elif 'word' in item:
                            key['word'] = item['word']
                            if 'grade_level' in item:
                                key['grade_level'] = item['grade_level']
                        # ProcessingJobs has job_id
                        elif 'job_id' in item:
                            key['job_id'] = item['job_id']
                        else:
                            logger.warning(f"Unknown key structure in {table_name}, skipping item")
                            continue
                        
                        batch_writer.delete_item(Key=key)
                        deleted_count += 1
            
            # Check if there are more items
            if 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            else:
                break
        
        return deleted_count
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.warning(f"Table {table_name} does not exist, skipping")
            return 0
        else:
            logger.error(f"Error clearing table {table_name}: {e}")
            raise


def main():
    """Clear all DynamoDB tables."""
    config = get_config()
    
    print("\n" + "=" * 80)
    print("  ⚠️  CLEARING ALL DYNAMODB TABLES")
    print("=" * 80)
    print("\nThis will delete ALL data from all Vocabulator tables!")
    print("This operation cannot be undone.\n")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Initialize DynamoDB resource
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=config.localstack_endpoint_url if hasattr(config, 'localstack_endpoint_url') else None,
        region_name=config.aws_region,
        aws_access_key_id=config.aws_access_key_id or 'test',
        aws_secret_access_key=config.aws_secret_access_key or 'test',
    )
    
    # Get all table names
    tables = [
        config.get_dynamodb_table_name("StudentProfiles"),
        config.get_dynamodb_table_name("VocabularyRecommendations"),
        config.get_dynamodb_table_name("CommonCoreVocabulary"),
        config.get_dynamodb_table_name("ProcessingJobs"),
    ]
    
    total_deleted = 0
    
    for table_name in tables:
        print(f"\nClearing {table_name}...")
        try:
            deleted = clear_table(table_name, dynamodb)
            print(f"  ✅ Deleted {deleted} items from {table_name}")
            total_deleted += deleted
        except Exception as e:
            print(f"  ❌ Error clearing {table_name}: {e}")
            logger.error(f"Failed to clear {table_name}: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print(f"  ✅ Cleared {total_deleted} total items from {len(tables)} tables")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to clear DynamoDB: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)

