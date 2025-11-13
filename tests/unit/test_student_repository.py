"""Unit tests for StudentRepository.

Tests cover CRUD operations, vocabulary management, and grade-level queries.
"""

import pytest
from datetime import datetime
from typing import Dict

from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.student_repository import StudentRepository
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
    
    table_name = "test-student-profiles"
    
    # Create table with GSI
    create_test_table(
        table_name=table_name,
        partition_key="student_id",
        sort_key="profile_version",
        gsi={
            "index_name": "grade_level-proficiency_score-index",
            "partition_key": "grade_level",
            "sort_key": "proficiency_score",
        },
    )
    
    yield table_name
    
    # Cleanup
    try:
        delete_test_table(table_name)
    except Exception:
        pass


@pytest.fixture
def student_repository(test_table_name):
    """Create a StudentRepository instance for testing."""
    return StudentRepository(table_name=test_table_name)


@pytest.mark.unit
@pytest.mark.aws
class TestStudentRepository:
    """Test suite for StudentRepository."""
    
    def test_create_student_profile(self, student_repository):
        """Test creating a student profile."""
        profile = StudentProfile(
            student_id="STU-001",
            grade_level=7,
        )
        
        created = student_repository.create(profile)
        
        assert created.student_id == "STU-001"
        assert created.grade_level == 7
    
    def test_get_student_profile(self, student_repository):
        """Test retrieving a student profile."""
        # Create profile
        profile = StudentProfile(
            student_id="STU-002",
            grade_level=7,
        )
        student_repository.create(profile)
        
        # Retrieve profile
        retrieved = student_repository.get(student_id="STU-002")
        
        assert retrieved is not None
        assert retrieved.student_id == "STU-002"
        assert retrieved.grade_level == 7
    
    def test_get_nonexistent_student(self, student_repository):
        """Test retrieving a nonexistent student returns None."""
        retrieved = student_repository.get(student_id="STU-NONE")
        assert retrieved is None
    
    def test_update_student_profile(self, student_repository):
        """Test updating a student profile."""
        # Create profile
        profile = StudentProfile(
            student_id="STU-003",
            grade_level=7,
        )
        student_repository.create(profile)
        
        # Add vocabulary
        entry = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=2,
        )
        profile.add_vocabulary(entry)
        profile.calculate_proficiency_score()
        
        # Update profile
        updated = student_repository.update(profile)
        
        assert updated is not None
        assert len(updated.vocabulary_list) == 1
        assert updated.proficiency_score > 0
    
    def test_delete_student_profile(self, student_repository):
        """Test deleting a student profile."""
        # Create profile
        profile = StudentProfile(
            student_id="STU-004",
            grade_level=7,
        )
        student_repository.create(profile)
        
        # Delete profile
        student_repository.delete(student_id="STU-004")
        
        # Verify deleted
        retrieved = student_repository.get(student_id="STU-004")
        assert retrieved is None
    
    def test_add_vocabulary(self, student_repository):
        """Test adding vocabulary to a student profile."""
        # Create profile
        profile = StudentProfile(
            student_id="STU-005",
            grade_level=7,
        )
        student_repository.create(profile)
        
        # Add vocabulary
        entry = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=3,
            contexts=["math", "science"],
        )
        
        updated = student_repository.add_vocabulary(
            student_id="STU-005",
            entry=entry,
        )
        
        assert updated is not None
        assert len(updated.vocabulary_list) == 1
        assert updated.vocabulary_list[0].word == "analyze"
        assert updated.vocabulary_list[0].usage_count == 3
    
    def test_add_vocabulary_dedupe(self, student_repository):
        """Test that adding duplicate vocabulary updates count."""
        # Create profile
        profile = StudentProfile(
            student_id="STU-006",
            grade_level=7,
        )
        student_repository.create(profile)
        
        # Add vocabulary twice
        entry1 = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=2,
        )
        entry2 = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=3,
        )
        
        student_repository.add_vocabulary(student_id="STU-006", entry=entry1)
        updated = student_repository.add_vocabulary(student_id="STU-006", entry=entry2)
        
        # Should have only one entry with combined count
        assert len(updated.vocabulary_list) == 1
        assert updated.vocabulary_list[0].usage_count == 5
    
    def test_list_by_grade_level(self, student_repository):
        """Test listing students by grade level."""
        # Create profiles for different grades
        for grade in [6, 7, 8]:
            profile = StudentProfile(
                student_id=f"STU-GRADE-{grade}",
                grade_level=grade,
            )
            student_repository.create(profile)
        
        # Query grade 7 students
        grade_7_students = student_repository.list_by_grade_level(grade_level=7)
        
        assert len(grade_7_students) >= 1
        assert all(s.grade_level == 7 for s in grade_7_students)
    
    def test_update_proficiency_score(self, student_repository):
        """Test that proficiency score updates when vocabulary changes."""
        # Create profile
        profile = StudentProfile(
            student_id="STU-007",
            grade_level=7,
        )
        student_repository.create(profile)
        
        # Add vocabulary
        words = ["analyze", "evaluate", "synthesize"]
        for word in words:
            entry = VocabularyEntry(
                word=word,
                first_seen=datetime.now(),
                usage_count=2,
            )
            student_repository.add_vocabulary(student_id="STU-007", entry=entry)
        
        # Get updated profile
        updated = student_repository.get(student_id="STU-007")
        
        assert updated is not None
        assert updated.proficiency_score > 0
        assert len(updated.vocabulary_list) == 3

