"""Unit tests for RecommendationRepository.

Tests cover CRUD operations, date range queries, and status updates.
"""

import pytest
from datetime import datetime, timedelta, timezone

from src.data.models.recommendation import (
    VocabularyRecommendation,
    RecommendedWord,
    RecommendationStatus,
)
from src.data.repositories.recommendation_repository import RecommendationRepository
from tests.fixtures.dynamodb_setup import (
    create_test_table,
    delete_test_table,
)


@pytest.fixture
def test_table_name(mock_aws_credentials, temp_env_vars):
    """Create a test table and return its name."""
    temp_env_vars(
        DYNAMODB_TABLE_PREFIX="test",
        S3_BUCKET_NAME="test-bucket",
        OPENAI_API_KEY="test-key",
    )
    
    table_name = "test-vocabulary-recommendations"
    
    # Create table with GSI
    create_test_table(
        table_name=table_name,
        partition_key="student_id",
        sort_key="recommendation_date",
        gsi={
            "index_name": "status-recommendation_date-index",
            "partition_key": "status",
            "sort_key": "recommendation_date",
        },
    )
    
    yield table_name
    
    # Cleanup
    try:
        delete_test_table(table_name)
    except Exception:
        pass


@pytest.fixture
def recommendation_repository(test_table_name):
    """Create a RecommendationRepository instance for testing."""
    return RecommendationRepository(table_name=test_table_name)


@pytest.mark.unit
@pytest.mark.aws
class TestRecommendationRepository:
    """Test suite for RecommendationRepository."""
    
    def test_create_recommendation(self, recommendation_repository):
        """Test creating a vocabulary recommendation."""
        words = [
            RecommendedWord(
                word="analyze",
                definition="examine in detail",
                grade_level=7,
            ),
        ]
        
        recommendation = VocabularyRecommendation(
            student_id="STU-001",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=words,
        )
        
        created = recommendation_repository.create(recommendation)
        
        assert created.student_id == "STU-001"
        assert len(created.words) == 1
    
    def test_get_recommendation(self, recommendation_repository):
        """Test retrieving a recommendation."""
        # Create recommendation
        recommendation = VocabularyRecommendation(
            student_id="STU-002",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=[
                RecommendedWord(
                    word="evaluate",
                    definition="assess the value",
                    grade_level=7,
                ),
            ],
        )
        recommendation_repository.create(recommendation)
        
        # Retrieve recommendation
        retrieved = recommendation_repository.get(
            student_id="STU-002",
            recommendation_date=recommendation.recommendation_date,
        )
        
        assert retrieved is not None
        assert retrieved.student_id == "STU-002"
        assert len(retrieved.words) == 1
    
    def test_get_nonexistent_recommendation(self, recommendation_repository):
        """Test retrieving a nonexistent recommendation returns None."""
        retrieved = recommendation_repository.get(
            student_id="STU-NONE",
            recommendation_date=datetime.now(timezone.utc).date().isoformat(),
        )
        assert retrieved is None
    
    def test_get_by_student(self, recommendation_repository):
        """Test getting all recommendations for a student."""
        # Create multiple recommendations for same student
        base_date = datetime.now(timezone.utc).date()
        
        for i in range(3):
            recommendation = VocabularyRecommendation(
                student_id="STU-003",
                recommendation_date=(base_date + timedelta(days=i)).isoformat(),
                words=[
                    RecommendedWord(
                        word=f"word-{i}",
                        definition=f"definition {i}",
                        grade_level=7,
                    ),
                ],
            )
            recommendation_repository.create(recommendation)
        
        # Get all recommendations for student
        recommendations = recommendation_repository.get_by_student(student_id="STU-003")
        
        assert len(recommendations) == 3
        assert all(r.student_id == "STU-003" for r in recommendations)
    
    def test_get_by_date_range(self, recommendation_repository):
        """Test getting recommendations by date range."""
        base_date = datetime.now(timezone.utc).date()
        
        # Create recommendations on different dates
        dates = [
            base_date - timedelta(days=5),
            base_date - timedelta(days=2),
            base_date,
            base_date + timedelta(days=2),
        ]
        
        for date in dates:
            recommendation = VocabularyRecommendation(
                student_id="STU-004",
                recommendation_date=date.isoformat(),
                words=[
                    RecommendedWord(
                        word="test",
                        definition="test",
                        grade_level=7,
                    ),
                ],
            )
            recommendation_repository.create(recommendation)
        
        # Get recommendations in date range
        start_date = (base_date - timedelta(days=3)).isoformat()
        end_date = (base_date + timedelta(days=1)).isoformat()
        
        recommendations = recommendation_repository.get_by_date_range(
            student_id="STU-004",
            start_date=start_date,
            end_date=end_date,
        )
        
        # Should get 2 recommendations (within range)
        assert len(recommendations) == 2
    
    def test_update_status(self, recommendation_repository):
        """Test updating recommendation status."""
        # Create recommendation
        recommendation = VocabularyRecommendation(
            student_id="STU-005",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=[
                RecommendedWord(
                    word="analyze",
                    definition="examine",
                    grade_level=7,
                ),
            ],
            status=RecommendationStatus.PENDING,
        )
        recommendation_repository.create(recommendation)
        
        # Update status
        updated = recommendation_repository.update_status(
            student_id="STU-005",
            recommendation_date=recommendation.recommendation_date,
            status=RecommendationStatus.ASSIGNED,
        )
        
        assert updated is not None
        assert updated.status == RecommendationStatus.ASSIGNED
    
    def test_delete_recommendation(self, recommendation_repository):
        """Test deleting a recommendation."""
        # Create recommendation
        recommendation = VocabularyRecommendation(
            student_id="STU-006",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=[],
        )
        recommendation_repository.create(recommendation)
        
        # Delete recommendation
        recommendation_repository.delete(
            student_id="STU-006",
            recommendation_date=recommendation.recommendation_date,
        )
        
        # Verify deleted
        retrieved = recommendation_repository.get(
            student_id="STU-006",
            recommendation_date=recommendation.recommendation_date,
        )
        assert retrieved is None
    
    def test_recommendation_ttl_set(self, recommendation_repository):
        """Test that TTL is set correctly on recommendations."""
        recommendation = VocabularyRecommendation(
            student_id="STU-007",
            recommendation_date=datetime.now(timezone.utc).date(),
            words=[],
        )
        
        created = recommendation_repository.create(recommendation)
        
        # TTL should be approximately 30 days from now
        expected_ttl = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        assert abs(created.expires_at - expected_ttl) < 60  # Within 1 minute

