#!/usr/bin/env python3
"""
Setup DynamoDB tables in LocalStack for local development and testing

This script creates all required DynamoDB tables with proper schemas,
indexes, and configurations as defined in architecture.md
"""

import sys
import boto3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_student_profiles_table(dynamodb, table_name: str):
    """Create StudentProfiles table"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "student_id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "profile_version", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "student_id", "AttributeType": "S"},
                {"AttributeName": "profile_version", "AttributeType": "N"},
                {"AttributeName": "grade_level", "AttributeType": "N"},
                {"AttributeName": "proficiency_score", "AttributeType": "N"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "grade_level-proficiency_score-index",
                    "KeySchema": [
                        {"AttributeName": "grade_level", "KeyType": "HASH"},
                        {"AttributeName": "proficiency_score", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        print(f"✅ Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"ℹ️  Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_vocabulary_recommendations_table(dynamodb, table_name: str):
    """Create VocabularyRecommendations table"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "student_id", "KeyType": "HASH"},  # Partition key
                {
                    "AttributeName": "recommendation_date",
                    "KeyType": "RANGE",
                },  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "student_id", "AttributeType": "S"},
                {"AttributeName": "recommendation_date", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "status-recommendation_date-index",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"},
                        {"AttributeName": "recommendation_date", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        print(f"✅ Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"ℹ️  Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_common_core_vocabulary_table(dynamodb, table_name: str):
    """Create CommonCoreVocabulary table"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "grade_level", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "word", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "grade_level", "AttributeType": "N"},
                {"AttributeName": "word", "AttributeType": "S"},
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        print(f"✅ Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"ℹ️  Table {table_name} already exists")
        return dynamodb.Table(table_name)


def create_processing_jobs_table(dynamodb, table_name: str):
    """Create ProcessingJobs table"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "job_id", "KeyType": "HASH"},  # Partition key
            ],
            AttributeDefinitions=[
                {"AttributeName": "job_id", "AttributeType": "S"},
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        print(f"✅ Created table: {table_name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"ℹ️  Table {table_name} already exists")
        return dynamodb.Table(table_name)


def main():
    """Create all DynamoDB tables"""
    print("\n" + "=" * 80)
    print("  Setting up DynamoDB Tables in LocalStack")
    print("=" * 80 + "\n")

    # Load configuration
    config = load_config()
    print(f"ℹ️  Environment: {config.environment}")
    print(f"ℹ️  Endpoint: {config.localstack_endpoint_url}\n")

    # Initialize DynamoDB resource
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=config.localstack_endpoint_url,
        region_name=config.aws_region,
        aws_access_key_id=config.aws_access_key_id or "test",
        aws_secret_access_key=config.aws_secret_access_key or "test",
    )

    # Create tables
    student_profiles_table = config.get_dynamodb_table_name("StudentProfiles")
    vocab_recommendations_table = config.get_dynamodb_table_name(
        "VocabularyRecommendations"
    )
    common_core_table = config.get_dynamodb_table_name("CommonCoreVocabulary")
    processing_jobs_table = config.get_dynamodb_table_name("ProcessingJobs")

    create_student_profiles_table(dynamodb, student_profiles_table)
    create_vocabulary_recommendations_table(dynamodb, vocab_recommendations_table)
    create_common_core_vocabulary_table(dynamodb, common_core_table)
    create_processing_jobs_table(dynamodb, processing_jobs_table)

    print("\n" + "=" * 80)
    print("  ✅ All tables created successfully!")
    print("=" * 80 + "\n")

    # List all tables
    client = boto3.client(
        "dynamodb",
        endpoint_url=config.localstack_endpoint_url,
        region_name=config.aws_region,
        aws_access_key_id=config.aws_access_key_id or "test",
        aws_secret_access_key=config.aws_secret_access_key or "test",
    )

    response = client.list_tables()
    print("Available tables:")
    for table_name in response["TableNames"]:
        print(f"  • {table_name}")

    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.exception("Failed to create tables", exc_info=e)
        sys.exit(1)
