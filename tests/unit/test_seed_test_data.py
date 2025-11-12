"""Tests for test data seeding script."""

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.data.models.student_profile import StudentProfile


@pytest.fixture
def sample_profiles_file(tmp_path):
    """Create a sample profiles JSON file."""
    profiles_file = tmp_path / "all_student_profiles.json"
    
    # Create a minimal valid profile
    profile = StudentProfile(
        student_id="STU-001",
        grade_level=6,
        vocabulary_list=[]
    )
    profile.calculate_proficiency_score()
    
    profiles_data = [profile.to_dict()]
    # Convert datetime objects to ISO strings
    profiles_data[0]["created_at"] = profile.created_at.isoformat()
    profiles_data[0]["last_updated"] = profile.last_updated.isoformat()
    # Vocabulary list entries already have ISO string timestamps from to_dict()
    
    with open(profiles_file, "w") as f:
        json.dump(profiles_data, f, default=str)
    
    return profiles_file


@pytest.fixture
def sample_transcripts_dir(tmp_path):
    """Create sample transcripts directory."""
    transcripts_dir = tmp_path / "sample_transcripts"
    transcripts_dir.mkdir()
    
    # Create a few sample transcript files
    for i in range(3):
        transcript_file = transcripts_dir / f"STU-{i+1:03d}.txt"
        transcript_file.write_text(f"Sample transcript {i+1}")
    
    return transcripts_dir


@pytest.fixture
def sample_writing_dir(tmp_path):
    """Create sample writing directory."""
    writing_dir = tmp_path / "sample_writing"
    writing_dir.mkdir()
    
    # Create a few sample writing files
    for i in range(3):
        writing_file = writing_dir / f"STU-{i+1:03d}-WR-001.txt"
        writing_file.write_text(f"Sample writing {i+1}")
    
    return writing_dir


def test_load_student_profiles(sample_profiles_file):
    """Test loading student profiles from JSON file."""
    from scripts.seed_test_data import load_student_profiles
    
    profiles = load_student_profiles(sample_profiles_file)
    
    assert len(profiles) == 1
    assert profiles[0].student_id == "STU-001"
    assert profiles[0].grade_level == 6


def test_load_student_profiles_file_not_found(tmp_path):
    """Test loading profiles when file doesn't exist."""
    from scripts.seed_test_data import load_student_profiles
    
    missing_file = tmp_path / "missing.json"
    
    with pytest.raises(FileNotFoundError):
        load_student_profiles(missing_file)


@patch("scripts.seed_test_data.StudentRepository")
def test_seed_student_profiles(mock_repo_class, sample_profiles_file):
    """Test seeding student profiles to DynamoDB."""
    from scripts.seed_test_data import seed_student_profiles, load_student_profiles
    
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    profiles = load_student_profiles(sample_profiles_file)
    seed_student_profiles(profiles, table_name="test-table")
    
    assert mock_repo.create_profile.call_count == len(profiles)
    mock_repo_class.assert_called_once_with(table_name="test-table")


@patch("scripts.seed_test_data.S3Client")
def test_seed_transcripts_and_writing(mock_s3_class, sample_transcripts_dir, sample_writing_dir):
    """Test seeding transcripts and writing samples to S3."""
    from scripts.seed_test_data import seed_transcripts_and_writing
    
    mock_s3 = MagicMock()
    mock_s3_class.return_value = mock_s3
    
    seed_transcripts_and_writing(
        transcripts_dir=sample_transcripts_dir,
        writing_dir=sample_writing_dir,
        bucket_name="test-bucket"
    )
    
    # Should upload 3 transcripts + 3 writing samples = 6 uploads
    assert mock_s3.upload_file.call_count == 6
    mock_s3_class.assert_called_once_with(bucket_name="test-bucket")


@patch("scripts.seed_test_data.S3Client")
def test_seed_transcripts_and_writing_missing_dirs(mock_s3_class, tmp_path):
    """Test seeding when directories don't exist."""
    from scripts.seed_test_data import seed_transcripts_and_writing
    
    mock_s3 = MagicMock()
    mock_s3_class.return_value = mock_s3
    
    missing_transcripts = tmp_path / "missing_transcripts"
    missing_writing = tmp_path / "missing_writing"
    
    # Should not raise error, just log warning
    seed_transcripts_and_writing(
        transcripts_dir=missing_transcripts,
        writing_dir=missing_writing,
        bucket_name="test-bucket"
    )
    
    # Should not upload anything
    assert mock_s3.upload_file.call_count == 0


@patch("scripts.seed_test_data.seed_transcripts_and_writing")
@patch("scripts.seed_test_data.seed_student_profiles")
@patch("scripts.seed_test_data.load_student_profiles")
def test_seed_all_test_data(
    mock_load_profiles,
    mock_seed_profiles,
    mock_seed_files,
    tmp_path,
    sample_profiles_file,
    sample_transcripts_dir,
    sample_writing_dir
):
    """Test seeding all test data."""
    from scripts.seed_test_data import seed_all_test_data
    
    # Set up fixtures directory structure
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    
    # Copy sample files to fixtures directory
    shutil.copy(sample_profiles_file, fixtures_dir / "all_student_profiles.json")
    shutil.copytree(sample_transcripts_dir, fixtures_dir / "sample_transcripts")
    shutil.copytree(sample_writing_dir, fixtures_dir / "sample_writing")
    
    mock_load_profiles.return_value = [StudentProfile(
        student_id="STU-001",
        grade_level=6,
        vocabulary_list=[]
    )]
    
    seed_all_test_data(
        fixtures_dir=fixtures_dir,
        table_name="test-table",
        bucket_name="test-bucket"
    )
    
    mock_load_profiles.assert_called_once()
    mock_seed_profiles.assert_called_once()
    mock_seed_files.assert_called_once()


@patch("scripts.seed_test_data.seed_transcripts_and_writing")
@patch("scripts.seed_test_data.seed_student_profiles")
@patch("scripts.seed_test_data.load_student_profiles")
def test_seed_all_test_data_missing_profiles_file(
    mock_load_profiles,
    mock_seed_profiles,
    mock_seed_files,
    tmp_path,
    sample_transcripts_dir,
    sample_writing_dir
):
    """Test seeding when profiles file is missing."""
    from scripts.seed_test_data import seed_all_test_data
    
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    
    # Only create transcripts and writing directories
    shutil.copytree(sample_transcripts_dir, fixtures_dir / "sample_transcripts")
    shutil.copytree(sample_writing_dir, fixtures_dir / "sample_writing")
    
    # Should not raise error, just skip profile seeding
    seed_all_test_data(
        fixtures_dir=fixtures_dir,
        table_name="test-table",
        bucket_name="test-bucket"
    )
    
    # Should not call profile functions
    mock_load_profiles.assert_not_called()
    mock_seed_profiles.assert_not_called()
    
    # Should still seed files
    mock_seed_files.assert_called_once()

