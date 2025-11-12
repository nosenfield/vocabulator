#!/usr/bin/env python3
"""Seed development database with test data.

This script loads generated test data into DynamoDB and S3:
- Student profiles from JSON files
- Transcripts and writing samples to S3
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.dynamodb_client import DynamoDBClient
from src.data.models.student_profile import StudentProfile
from src.data.repositories.student_repository import StudentRepository
from src.data.s3_client import S3Client
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("scripts.seed_test_data")


def load_student_profiles(profiles_file: Path) -> List[StudentProfile]:
    """Load student profiles from JSON file.
    
    Args:
        profiles_file: Path to JSON file containing student profiles
        
    Returns:
        List of StudentProfile objects
    """
    if not profiles_file.exists():
        raise FileNotFoundError(f"Profiles file not found: {profiles_file}")
    
    with open(profiles_file, "r") as f:
        profiles_data = json.load(f)
    
    profiles = []
    for profile_data in profiles_data:
        profile = StudentProfile.from_dict(profile_data)
        profiles.append(profile)
    
    logger.info(f"Loaded {len(profiles)} student profiles from {profiles_file}")
    return profiles


def seed_student_profiles(
    profiles: List[StudentProfile],
    table_name: Optional[str] = None
) -> None:
    """Seed student profiles into DynamoDB.
    
    Args:
        profiles: List of StudentProfile objects to seed
        table_name: Optional table name override
    """
    config = get_config()
    
    if table_name is None:
        table_name = config.get_dynamodb_table_name("StudentProfiles")
    
    repository = StudentRepository(table_name=table_name)
    
    logger.info(f"Seeding {len(profiles)} student profiles to {table_name}...")
    
    for i, profile in enumerate(profiles, 1):
        try:
            repository.create_profile(profile)
            if i % 10 == 0:
                logger.info(f"  Seeded {i}/{len(profiles)} profiles...")
        except Exception as e:
            logger.error(f"Failed to seed profile {profile.student_id}: {e}")
            raise
    
    logger.info(f"Successfully seeded {len(profiles)} student profiles")


def seed_transcripts_and_writing(
    transcripts_dir: Path,
    writing_dir: Path,
    bucket_name: Optional[str] = None
) -> None:
    """Seed transcripts and writing samples to S3.
    
    Args:
        transcripts_dir: Directory containing transcript files
        writing_dir: Directory containing writing sample files
        bucket_name: Optional S3 bucket name override
    """
    config = get_config()
    
    if bucket_name is None:
        bucket_name = config.s3_bucket_name
    
    s3_client = S3Client(bucket_name=bucket_name)
    
    # Seed transcripts
    if transcripts_dir.exists():
        transcript_files = list(transcripts_dir.glob("*.txt"))
        logger.info(f"Seeding {len(transcript_files)} transcripts to S3...")
        
        for i, transcript_file in enumerate(transcript_files, 1):
            student_id = transcript_file.stem
            content = transcript_file.read_text()
            
            # Construct S3 key: transcripts/{student_id}/raw.txt
            s3_key = f"transcripts/{student_id}/raw.txt"
            
            try:
                s3_client.upload_file(
                    file_content=content.encode("utf-8"),
                    s3_key=s3_key,
                    content_type="text/plain"
                )
                if i % 10 == 0:
                    logger.info(f"  Uploaded {i}/{len(transcript_files)} transcripts...")
            except Exception as e:
                logger.error(f"Failed to upload transcript {transcript_file}: {e}")
                raise
        
        logger.info(f"Successfully uploaded {len(transcript_files)} transcripts")
    else:
        logger.warning(f"Transcripts directory not found: {transcripts_dir}")
    
    # Seed writing samples
    if writing_dir.exists():
        writing_files = list(writing_dir.glob("*.txt"))
        logger.info(f"Seeding {len(writing_files)} writing samples to S3...")
        
        for i, writing_file in enumerate(writing_files, 1):
            # Extract student ID from filename (format: STU-XXX-WR-Y-ZZZ)
            # Remove the -WR-Y- part to get base student ID
            filename_parts = writing_file.stem.split("-WR-")
            if len(filename_parts) == 2:
                # Format: STU-XXX-WR-Y-ZZZ -> STU-XXX
                student_id = filename_parts[0]
            else:
                # Fallback: use stem as-is
                student_id = writing_file.stem
            content = writing_file.read_text()
            
            # Construct S3 key: writing/{student_id}/raw.txt
            s3_key = f"writing/{student_id}/raw.txt"
            
            try:
                s3_client.upload_file(
                    file_content=content.encode("utf-8"),
                    s3_key=s3_key,
                    content_type="text/plain"
                )
                if i % 10 == 0:
                    logger.info(f"  Uploaded {i}/{len(writing_files)} writing samples...")
            except Exception as e:
                logger.error(f"Failed to upload writing sample {writing_file}: {e}")
                raise
        
        logger.info(f"Successfully uploaded {len(writing_files)} writing samples")
    else:
        logger.warning(f"Writing directory not found: {writing_dir}")


def seed_all_test_data(
    fixtures_dir: Path,
    table_name: Optional[str] = None,
    bucket_name: Optional[str] = None
) -> None:
    """Seed all test data into development database.
    
    Args:
        fixtures_dir: Directory containing test fixtures
        table_name: Optional DynamoDB table name override
        bucket_name: Optional S3 bucket name override
    """
    profiles_file = fixtures_dir / "all_student_profiles.json"
    transcripts_dir = fixtures_dir / "sample_transcripts"
    writing_dir = fixtures_dir / "sample_writing"
    
    # Load and seed student profiles
    if profiles_file.exists():
        profiles = load_student_profiles(profiles_file)
        seed_student_profiles(profiles, table_name=table_name)
    else:
        logger.warning(f"Profiles file not found: {profiles_file}")
        logger.info("Skipping student profile seeding")
    
    # Seed transcripts and writing samples
    seed_transcripts_and_writing(
        transcripts_dir=transcripts_dir,
        writing_dir=writing_dir,
        bucket_name=bucket_name
    )
    
    logger.info("Test data seeding completed successfully")


def main():
    """Main entry point for seeding test data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed development database with test data")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("tests/fixtures"),
        help="Directory containing test fixtures (default: tests/fixtures)",
    )
    parser.add_argument(
        "--table-name",
        type=str,
        default=None,
        help="DynamoDB table name (defaults to configured name)",
    )
    parser.add_argument(
        "--bucket-name",
        type=str,
        default=None,
        help="S3 bucket name (defaults to configured name)",
    )
    
    args = parser.parse_args()
    
    if not args.fixtures_dir.exists():
        logger.error(f"Fixtures directory not found: {args.fixtures_dir}")
        logger.info("Run scripts/generate_test_data.py first to generate test data")
        sys.exit(1)
    
    try:
        seed_all_test_data(
            fixtures_dir=args.fixtures_dir,
            table_name=args.table_name,
            bucket_name=args.bucket_name
        )
        logger.info("Test data seeding completed successfully")
    except Exception as e:
        logger.error(f"Failed to seed test data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

