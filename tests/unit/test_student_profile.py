"""Unit tests for StudentProfile data model.

Tests cover model validation, vocabulary list management, and proficiency score calculation.
"""

import pytest
from datetime import datetime
from typing import Dict, List

from src.data.models.student_profile import (
    StudentProfile,
    VocabularyEntry,
)


class TestVocabularyEntry:
    """Test VocabularyEntry model."""
    
    def test_create_vocabulary_entry(self):
        """Test creating a vocabulary entry."""
        entry = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=5,
            contexts=["math", "science"],
        )
        
        assert entry.word == "analyze"
        assert entry.usage_count == 5
        assert len(entry.contexts) == 2
    
    def test_vocabulary_entry_defaults(self):
        """Test vocabulary entry with defaults."""
        entry = VocabularyEntry(word="test", first_seen=datetime.now())
        
        assert entry.usage_count == 1
        assert entry.contexts == []
    
    def test_vocabulary_entry_validation(self):
        """Test vocabulary entry validation."""
        # Usage count must be positive
        with pytest.raises(ValueError):
            VocabularyEntry(
                word="test",
                first_seen=datetime.now(),
                usage_count=-1,
            )


class TestStudentProfile:
    """Test StudentProfile model."""
    
    def test_create_student_profile(self):
        """Test creating a student profile."""
        profile = StudentProfile(
            student_id="STU-001",
            grade_level=7,
        )
        
        assert profile.student_id == "STU-001"
        assert profile.grade_level == 7
        assert profile.vocabulary_list == []
        assert profile.proficiency_score == 0.0
        assert profile.profile_version == 1
    
    def test_student_profile_grade_level_validation(self):
        """Test grade level validation (must be 6-8)."""
        # Valid grade levels
        for grade in [6, 7, 8]:
            profile = StudentProfile(student_id="STU-001", grade_level=grade)
            assert profile.grade_level == grade
        
        # Invalid grade levels
        for grade in [5, 9, 10]:
            with pytest.raises(ValueError):
                StudentProfile(student_id="STU-001", grade_level=grade)
    
    def test_student_profile_add_vocabulary(self):
        """Test adding vocabulary to profile."""
        profile = StudentProfile(student_id="STU-001", grade_level=7)
        
        entry = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=3,
        )
        
        profile.add_vocabulary(entry)
        
        assert len(profile.vocabulary_list) == 1
        assert profile.vocabulary_list[0].word == "analyze"
    
    def test_student_profile_add_vocabulary_dedupe(self):
        """Test that adding duplicate vocabulary updates count."""
        profile = StudentProfile(student_id="STU-001", grade_level=7)
        
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
        
        profile.add_vocabulary(entry1)
        profile.add_vocabulary(entry2)
        
        # Should have only one entry with combined count
        assert len(profile.vocabulary_list) == 1
        assert profile.vocabulary_list[0].usage_count == 5
    
    def test_student_profile_calculate_proficiency_score(self):
        """Test proficiency score calculation."""
        profile = StudentProfile(student_id="STU-001", grade_level=7)
        
        # Add some vocabulary
        words = ["analyze", "evaluate", "synthesize", "compare", "contrast"]
        for word in words:
            entry = VocabularyEntry(
                word=word,
                first_seen=datetime.now(),
                usage_count=2,
            )
            profile.add_vocabulary(entry)
        
        # Calculate proficiency score
        score = profile.calculate_proficiency_score()
        
        # Should be between 0 and 100
        assert 0 <= score <= 100
        assert profile.proficiency_score == score
    
    def test_student_profile_to_dict(self):
        """Test converting profile to dictionary."""
        profile = StudentProfile(student_id="STU-001", grade_level=7)
        
        entry = VocabularyEntry(
            word="analyze",
            first_seen=datetime.now(),
            usage_count=2,
        )
        profile.add_vocabulary(entry)
        
        profile_dict = profile.to_dict()
        
        assert profile_dict["student_id"] == "STU-001"
        assert profile_dict["grade_level"] == 7
        assert len(profile_dict["vocabulary_list"]) == 1
    
    def test_student_profile_from_dict(self):
        """Test creating profile from dictionary."""
        profile_dict = {
            "student_id": "STU-001",
            "grade_level": 7,
            "vocabulary_list": [
                {
                    "word": "analyze",
                    "first_seen": datetime.now().isoformat(),
                    "usage_count": 2,
                    "contexts": ["math"],
                }
            ],
            "proficiency_score": 45.5,
            "profile_version": 1,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        
        profile = StudentProfile.from_dict(profile_dict)
        
        assert profile.student_id == "STU-001"
        assert profile.grade_level == 7
        assert len(profile.vocabulary_list) == 1
        assert profile.proficiency_score == 45.5

