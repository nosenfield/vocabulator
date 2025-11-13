"""Unit tests for VocabularyRecommendation data model.

Tests cover model validation, word list management, and TTL handling.
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from src.data.models.recommendation import (
    VocabularyRecommendation,
    RecommendedWord,
    RecommendationStatus,
)


class TestRecommendedWord:
    """Test RecommendedWord model."""
    
    def test_create_recommended_word(self):
        """Test creating a recommended word."""
        word = RecommendedWord(
            word="analyze",
            definition="examine in detail to understand",
            grade_level=7,
            difficulty_score=0.65,
            rationale="High utility across subjects",
            example_sentences=["Let's analyze the data.", "She will analyze the results."],
        )
        
        assert word.word == "analyze"
        assert word.grade_level == 7
        assert word.difficulty_score == 0.65
        assert len(word.example_sentences) == 2
    
    def test_recommended_word_defaults(self):
        """Test recommended word with defaults."""
        word = RecommendedWord(
            word="test",
            definition="test definition",
            grade_level=6,
        )
        
        assert word.difficulty_score == 0.5
        assert word.example_sentences == []
    
    def test_recommended_word_validation(self):
        """Test recommended word validation."""
        # Difficulty score must be 0-1
        with pytest.raises(ValueError):
            RecommendedWord(
                word="test",
                definition="test",
                grade_level=6,
                difficulty_score=1.5,
            )
        
        # Grade level must be 6-8
        with pytest.raises(ValueError):
            RecommendedWord(
                word="test",
                definition="test",
                grade_level=5,
            )


class TestVocabularyRecommendation:
    """Test VocabularyRecommendation model."""
    
    def test_create_recommendation(self):
        """Test creating a vocabulary recommendation."""
        words = [
            RecommendedWord(
                word="analyze",
                definition="examine in detail",
                grade_level=7,
            ),
            RecommendedWord(
                word="evaluate",
                definition="assess the value",
                grade_level=7,
            ),
        ]
        
        recommendation = VocabularyRecommendation(
            student_id="STU-001",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=words,
        )
        
        assert recommendation.student_id == "STU-001"
        assert len(recommendation.words) == 2
        assert recommendation.status == RecommendationStatus.PENDING
        assert recommendation.expires_at is not None
    
    def test_recommendation_ttl_calculation(self):
        """Test that TTL is set to 30 days from creation."""
        recommendation = VocabularyRecommendation(
            student_id="STU-002",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=[],
        )
        
        # TTL should be approximately 30 days from now
        expected_ttl = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        assert abs(recommendation.expires_at - expected_ttl) < 60  # Within 1 minute
    
    def test_recommendation_status_enum(self):
        """Test recommendation status enum values."""
        assert RecommendationStatus.PENDING == "pending"
        assert RecommendationStatus.ASSIGNED == "assigned"
        assert RecommendationStatus.LEARNED == "learned"
    
    def test_update_status(self):
        """Test updating recommendation status."""
        recommendation = VocabularyRecommendation(
            student_id="STU-003",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=[],
        )
        
        assert recommendation.status == RecommendationStatus.PENDING
        
        recommendation.status = RecommendationStatus.ASSIGNED
        assert recommendation.status == RecommendationStatus.ASSIGNED
        
        recommendation.status = RecommendationStatus.LEARNED
        assert recommendation.status == RecommendationStatus.LEARNED
    
    def test_recommendation_to_dict(self):
        """Test converting recommendation to dictionary."""
        words = [
            RecommendedWord(
                word="analyze",
                definition="examine in detail",
                grade_level=7,
            ),
        ]
        
        recommendation = VocabularyRecommendation(
            student_id="STU-004",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=words,
            status=RecommendationStatus.ASSIGNED,
            generated_by="batch-job-123",
        )
        
        rec_dict = recommendation.to_dict()
        
        assert rec_dict["student_id"] == "STU-004"
        assert rec_dict["status"] == "assigned"
        assert rec_dict["generated_by"] == "batch-job-123"
        assert len(rec_dict["words"]) == 1
        assert "expires_at" in rec_dict
    
    def test_recommendation_from_dict(self):
        """Test creating recommendation from dictionary."""
        rec_dict = {
            "student_id": "STU-005",
            "recommendation_date": datetime.now(timezone.utc).date().isoformat(),
            "words": [
                {
                    "word": "analyze",
                    "definition": "examine in detail",
                    "grade_level": 7,
                    "difficulty_score": 0.65,
                    "rationale": "High utility",
                    "example_sentences": ["Let's analyze the data."],
                }
            ],
            "status": "assigned",
            "generated_by": "batch-job-456",
            "expires_at": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        }
        
        recommendation = VocabularyRecommendation.from_dict(rec_dict)
        
        assert recommendation.student_id == "STU-005"
        assert recommendation.status == RecommendationStatus.ASSIGNED
        assert recommendation.generated_by == "batch-job-456"
        assert len(recommendation.words) == 1

