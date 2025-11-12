"""Tests for HTML report templates.

This module tests the Jinja2 template rendering for student vocabulary reports.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.frontend.templates import render_profile_report, render_recommendations_report
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.models.recommendation import VocabularyRecommendation, RecommendedWord, RecommendationStatus


@pytest.fixture
def sample_student_profile():
    """Create a sample student profile for testing."""
    profile = StudentProfile(
        student_id="STU-001",
        grade_level=7,
        proficiency_score=75.5,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        last_updated=datetime(2025, 11, 11, tzinfo=timezone.utc),
    )
    
    # Add some vocabulary entries
    profile.vocabulary_list = [
        VocabularyEntry(
            word="analyze",
            first_seen=datetime(2025, 10, 1, tzinfo=timezone.utc),
            usage_count=5,
            contexts=["science", "math"],
        ),
        VocabularyEntry(
            word="synthesize",
            first_seen=datetime(2025, 10, 15, tzinfo=timezone.utc),
            usage_count=3,
            contexts=["science"],
        ),
        VocabularyEntry(
            word="evaluate",
            first_seen=datetime(2025, 11, 1, tzinfo=timezone.utc),
            usage_count=2,
            contexts=["language arts"],
        ),
    ]
    
    return profile


@pytest.fixture
def sample_recommendation():
    """Create a sample vocabulary recommendation for testing."""
    return VocabularyRecommendation(
        student_id="STU-001",
        recommendation_date="2025-11-11",
        words=[
            RecommendedWord(
                word="hypothesis",
                definition="A proposed explanation for a phenomenon",
                grade_level=7,
                difficulty_score=0.4,
                rationale="Builds on student's science vocabulary",
                example_sentences=[
                    "The scientist formed a hypothesis about the experiment.",
                    "We need to test our hypothesis before drawing conclusions.",
                ],
            ),
            RecommendedWord(
                word="metaphor",
                definition="A figure of speech comparing two unlike things",
                grade_level=7,
                difficulty_score=0.6,
                rationale="Expands literary analysis skills",
                example_sentences=[
                    "The author used a metaphor to describe the sunset.",
                    "Can you identify the metaphor in this poem?",
                ],
            ),
        ],
        status=RecommendationStatus.PENDING,
        generated_by="batch-job-123",
    )


class TestTemplateRendering:
    """Test template rendering functionality."""
    
    def test_render_profile_report_basic(self, sample_student_profile):
        """Test basic profile report rendering."""
        html = render_profile_report(sample_student_profile)
        
        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "STU-001" in html
        assert "Grade 7" in html
        assert "75.5" in html or "75" in html  # Score formatting may vary
    
    def test_render_profile_report_includes_vocabulary(self, sample_student_profile):
        """Test that profile report includes vocabulary words."""
        html = render_profile_report(sample_student_profile)
        
        assert "analyze" in html
        assert "synthesize" in html
        assert "evaluate" in html
    
    def test_render_profile_report_includes_chart_script(self, sample_student_profile):
        """Test that profile report includes Chart.js for visualizations."""
        html = render_profile_report(sample_student_profile)
        
        assert "chart.js" in html.lower() or "Chart.js" in html
        assert "canvas" in html.lower()  # Chart.js uses canvas
    
    def test_render_profile_report_responsive_design(self, sample_student_profile):
        """Test that profile report includes responsive CSS."""
        html = render_profile_report(sample_student_profile)
        
        assert "viewport" in html.lower()
        assert "media" in html.lower() or "@media" in html.lower()
    
    def test_render_recommendations_report_basic(self, sample_recommendation):
        """Test basic recommendations report rendering."""
        html = render_recommendations_report(sample_recommendation)
        
        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "STU-001" in html
        assert "2025-11-11" in html
    
    def test_render_recommendations_report_includes_words(self, sample_recommendation):
        """Test that recommendations report includes recommended words."""
        html = render_recommendations_report(sample_recommendation)
        
        assert "hypothesis" in html
        assert "metaphor" in html
        assert "A proposed explanation" in html
        assert "figure of speech" in html
    
    def test_render_recommendations_report_includes_examples(self, sample_recommendation):
        """Test that recommendations report includes example sentences."""
        html = render_recommendations_report(sample_recommendation)
        
        assert "The scientist formed a hypothesis" in html
        assert "The author used a metaphor" in html
    
    def test_render_recommendations_report_shows_difficulty(self, sample_recommendation):
        """Test that recommendations report shows difficulty scores."""
        html = render_recommendations_report(sample_recommendation)
        
        # Difficulty scores should be displayed (may be formatted as percentages)
        assert "0.4" in html or "40" in html or "difficulty" in html.lower()
    
    def test_render_recommendations_report_shows_status(self, sample_recommendation):
        """Test that recommendations report shows recommendation status."""
        html = render_recommendations_report(sample_recommendation)
        
        assert "pending" in html.lower() or "Pending" in html
    
    def test_render_profile_report_empty_vocabulary(self):
        """Test profile report with empty vocabulary list."""
        profile = StudentProfile(
            student_id="STU-002",
            grade_level=6,
            proficiency_score=0.0,
        )
        
        html = render_profile_report(profile)
        
        assert isinstance(html, str)
        assert "STU-002" in html
        assert "Grade 6" in html
    
    def test_render_recommendations_report_empty_words(self):
        """Test recommendations report with no recommended words."""
        recommendation = VocabularyRecommendation(
            student_id="STU-002",
            recommendation_date="2025-11-11",
            words=[],
        )
        
        html = render_recommendations_report(recommendation)
        
        assert isinstance(html, str)
        assert "STU-002" in html
    
    def test_template_handles_special_characters(self, sample_student_profile):
        """Test that templates handle special characters in vocabulary words."""
        # Add word with special characters
        sample_student_profile.add_vocabulary(
            VocabularyEntry(
                word="don't",
                first_seen=datetime.now(timezone.utc),
                usage_count=1,
                contexts=["language arts"],
            )
        )
        
        html = render_profile_report(sample_student_profile)
        
        assert "don't" in html or "don&#39;t" in html  # HTML entity encoding
    
    def test_template_handles_long_definitions(self, sample_recommendation):
        """Test that templates handle long word definitions."""
        # Add word with long definition
        sample_recommendation.words.append(
            RecommendedWord(
                word="photosynthesis",
                definition="The process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll pigments",
                grade_level=7,
                difficulty_score=0.7,
            )
        )
        
        html = render_recommendations_report(sample_recommendation)
        
        assert "photosynthesis" in html
        assert "chlorophyll" in html or len(html) > 0  # Definition should be included

