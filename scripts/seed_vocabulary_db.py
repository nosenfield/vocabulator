#!/usr/bin/env python3
"""Seed Common Core vocabulary database.

This script loads vocabulary words from JSON corpus files into DynamoDB.
"""

import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vocabulary.common_core_loader import (
    CommonCoreLoader,
    load_vocabulary_from_json,
    VocabularyWord,
)
from src.data.dynamodb_client import DynamoDBClient
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("scripts.seed_vocabulary")


def seed_vocabulary_to_dynamodb(
    grade_6_file: Path,
    grade_7_file: Path,
    grade_8_file: Path,
    table_name: Optional[str] = None,
) -> None:
    """Load vocabulary from JSON files and seed DynamoDB table.
    
    Args:
        grade_6_file: Path to grade 6 corpus JSON file
        grade_7_file: Path to grade 7 corpus JSON file
        grade_8_file: Path to grade 8 corpus JSON file
        table_name: Optional table name override
    """
    config = get_config()
    
    if table_name is None:
        table_name = config.get_dynamodb_table_name("CommonCoreVocabulary")
    
    # Load vocabulary from JSON files
    loader = CommonCoreLoader()
    all_words = loader.load_from_json_files(
        grade_6_file=grade_6_file,
        grade_7_file=grade_7_file,
        grade_8_file=grade_8_file,
    )
    
    logger.info(f"Loaded {len(all_words)} vocabulary words")
    
    # Initialize DynamoDB client
    client = DynamoDBClient(table_name=table_name)
    
    # Batch write words to DynamoDB
    # DynamoDB batch_write_items handles up to 25 items per batch
    batch_size = 25
    total_written = 0
    
    for i in range(0, len(all_words), batch_size):
        batch = all_words[i : i + batch_size]
        
        # Convert VocabularyWord to DynamoDB item format
        items = []
        for word in batch:
            item = {
                "grade_level": word.grade_level,
                "word": word.word,
                "definition": word.definition,
                "subject_areas": word.subject_areas,
                "complexity_tier": word.complexity_tier,
                "word_family": word.word_family,
            }
            items.append(item)
        
        # Write batch
        try:
            client.batch_write_items(items=items)
            total_written += len(items)
            logger.info(f"Wrote batch {i // batch_size + 1}: {len(items)} words")
        except Exception as e:
            logger.error(f"Failed to write batch {i // batch_size + 1}: {e}")
            raise
    
    logger.info(f"Successfully seeded {total_written} vocabulary words to {table_name}")


def main():
    """Main entry point for seeding vocabulary database."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Common Core vocabulary database")
    parser.add_argument(
        "--grade-6",
        type=Path,
        default=Path("src/vocabulary/corpus/common_core_grade_6.json"),
        help="Path to grade 6 corpus file",
    )
    parser.add_argument(
        "--grade-7",
        type=Path,
        default=Path("src/vocabulary/corpus/common_core_grade_7.json"),
        help="Path to grade 7 corpus file",
    )
    parser.add_argument(
        "--grade-8",
        type=Path,
        default=Path("src/vocabulary/corpus/common_core_grade_8.json"),
        help="Path to grade 8 corpus file",
    )
    parser.add_argument(
        "--table-name",
        type=str,
        default=None,
        help="DynamoDB table name (defaults to configured name)",
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    for grade_file in [args.grade_6, args.grade_7, args.grade_8]:
        if not grade_file.exists():
            logger.error(f"Corpus file not found: {grade_file}")
            sys.exit(1)
    
    try:
        seed_vocabulary_to_dynamodb(
            grade_6_file=args.grade_6,
            grade_7_file=args.grade_7,
            grade_8_file=args.grade_8,
            table_name=args.table_name,
        )
        logger.info("Vocabulary seeding completed successfully")
    except Exception as e:
        logger.error(f"Failed to seed vocabulary database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

