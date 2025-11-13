"""Tests for test data generation script."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.generate_test_data import (
    generate_student_profile,
    generate_transcript,
    generate_writing_sample,
)


def test_generate_transcript_high_quality():
    """Test generating high-quality transcript."""
    transcript = generate_transcript(grade_level=6, quality="high_quality")
    
    assert isinstance(transcript, str)
    assert len(transcript) > 0
    assert "class" in transcript.lower() or "learned" in transcript.lower()


def test_generate_transcript_medium_quality():
    """Test generating medium-quality transcript."""
    transcript = generate_transcript(grade_level=7, quality="medium_quality")
    
    assert isinstance(transcript, str)
    assert len(transcript) > 0


def test_generate_transcript_low_quality():
    """Test generating low-quality transcript."""
    transcript = generate_transcript(grade_level=8, quality="low_quality")
    
    assert isinstance(transcript, str)
    assert len(transcript) > 0


def test_generate_transcript_all_grades():
    """Test generating transcripts for all grade levels."""
    for grade in [6, 7, 8]:
        transcript = generate_transcript(grade_level=grade)
        assert isinstance(transcript, str)
        assert len(transcript) > 0


def test_generate_writing_sample_essay():
    """Test generating essay writing sample."""
    writing = generate_writing_sample(grade_level=6, sample_type="essay")
    
    assert isinstance(writing, str)
    assert len(writing) > 0


def test_generate_writing_sample_response():
    """Test generating response writing sample."""
    writing = generate_writing_sample(grade_level=7, sample_type="response")
    
    assert isinstance(writing, str)
    assert len(writing) > 0


def test_generate_writing_sample_report():
    """Test generating report writing sample."""
    writing = generate_writing_sample(grade_level=8, sample_type="report")
    
    assert isinstance(writing, str)
    assert len(writing) > 0


def test_generate_writing_sample_all_grades():
    """Test generating writing samples for all grade levels."""
    for grade in [6, 7, 8]:
        writing = generate_writing_sample(grade_level=grade)
        assert isinstance(writing, str)
        assert len(writing) > 0


def test_generate_student_profile():
    """Test generating student profile."""
    profile = generate_student_profile(
        student_id="STU-001",
        grade_level=6,
        vocabulary_size=50
    )
    
    assert profile.student_id == "STU-001"
    assert profile.grade_level == 6
    assert len(profile.vocabulary_list) == 50
    assert 0.0 <= profile.proficiency_score <= 100.0


def test_generate_student_profile_all_grades():
    """Test generating profiles for all grade levels."""
    for grade in [6, 7, 8]:
        profile = generate_student_profile(
            student_id=f"STU-{grade:03d}",
            grade_level=grade,
            vocabulary_size=100
        )
        assert profile.grade_level == grade
        assert len(profile.vocabulary_list) == 100


def test_generate_student_profile_vocabulary_entries():
    """Test that vocabulary entries are valid."""
    profile = generate_student_profile(
        student_id="STU-002",
        grade_level=7,
        vocabulary_size=25
    )
    
    for entry in profile.vocabulary_list:
        assert entry.word
        assert entry.usage_count >= 1
        assert len(entry.contexts) > 0


def test_generate_student_profile_proficiency_score():
    """Test that proficiency score is calculated."""
    profile = generate_student_profile(
        student_id="STU-003",
        grade_level=8,
        vocabulary_size=150
    )
    
    assert profile.proficiency_score > 0.0
    assert profile.proficiency_score <= 100.0


def test_generate_all_test_data_creates_files(tmp_path):
    """Test that generate_all_test_data creates expected files."""
    from scripts.generate_test_data import generate_all_test_data
    
    output_dir = tmp_path / "fixtures"
    generate_all_test_data(output_dir)
    
    # Check directories exist
    assert (output_dir / "sample_transcripts").exists()
    assert (output_dir / "sample_writing").exists()
    assert (output_dir / "student_profiles").exists()
    
    # Check transcript files (should have 54: 6 per quality per grade * 3 qualities * 3 grades)
    transcript_files = list((output_dir / "sample_transcripts").glob("*.txt"))
    assert len(transcript_files) >= 50  # At least 50 transcripts
    
    # Check writing sample files (should have 27: 3 per type per grade * 3 types * 3 grades)
    writing_files = list((output_dir / "sample_writing").glob("*.txt"))
    assert len(writing_files) >= 20  # At least 20 writing samples
    
    # Check profile files (should have 30: 10 per grade * 3 grades)
    profile_files = list((output_dir / "student_profiles").glob("*.json"))
    assert len(profile_files) == 30
    
    # Check combined profiles file
    all_profiles_file = output_dir / "all_student_profiles.json"
    assert all_profiles_file.exists()
    
    # Verify JSON is valid
    with open(all_profiles_file) as f:
        profiles_data = json.load(f)
        assert len(profiles_data) == 30


def test_generate_all_test_data_transcript_content(tmp_path):
    """Test that generated transcripts have content."""
    from scripts.generate_test_data import generate_all_test_data
    
    output_dir = tmp_path / "fixtures"
    generate_all_test_data(output_dir)
    
    transcript_files = list((output_dir / "sample_transcripts").glob("*.txt"))
    assert len(transcript_files) > 0
    
    # Check a few transcripts have content
    for transcript_file in transcript_files[:5]:
        content = transcript_file.read_text()
        assert len(content) > 0
        assert len(content.strip()) > 0


def test_generate_all_test_data_writing_content(tmp_path):
    """Test that generated writing samples have content."""
    from scripts.generate_test_data import generate_all_test_data
    
    output_dir = tmp_path / "fixtures"
    generate_all_test_data(output_dir)
    
    writing_files = list((output_dir / "sample_writing").glob("*.txt"))
    assert len(writing_files) > 0
    
    # Check a few writing samples have content
    for writing_file in writing_files[:5]:
        content = writing_file.read_text()
        assert len(content) > 0
        assert len(content.strip()) > 0


def test_generate_all_test_data_profile_structure(tmp_path):
    """Test that generated profiles have correct structure."""
    from scripts.generate_test_data import generate_all_test_data
    
    output_dir = tmp_path / "fixtures"
    generate_all_test_data(output_dir)
    
    all_profiles_file = output_dir / "all_student_profiles.json"
    with open(all_profiles_file) as f:
        profiles_data = json.load(f)
    
    # Check structure of first profile
    profile = profiles_data[0]
    assert "student_id" in profile
    assert "grade_level" in profile
    assert profile["grade_level"] in [6, 7, 8]
    assert "vocabulary_list" in profile
    assert "proficiency_score" in profile
    assert 0.0 <= profile["proficiency_score"] <= 100.0

