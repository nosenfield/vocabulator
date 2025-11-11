"""Unit tests for Common Core vocabulary loader.

Tests cover vocabulary loading, grade-level lookups, and DynamoDB operations.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List

from src.vocabulary.common_core_loader import (
    CommonCoreLoader,
    VocabularyWord,
    load_vocabulary_from_json,
)


@pytest.fixture
def sample_corpus_file(tmp_path):
    """Create a sample corpus JSON file for testing."""
    corpus_data = [
        {
            "word": "analyze",
            "grade_level": 6,
            "definition": "examine in detail to understand",
            "subject_areas": ["math", "science", "ela"],
            "complexity_tier": 2,
            "word_family": ["analysis", "analytical", "analyzer"],
        },
        {
            "word": "evaluate",
            "grade_level": 6,
            "definition": "assess the value or quality",
            "subject_areas": ["math", "ela"],
            "complexity_tier": 2,
            "word_family": ["evaluation", "evaluative"],
        },
        {
            "word": "synthesize",
            "grade_level": 7,
            "definition": "combine elements into a coherent whole",
            "subject_areas": ["science", "ela"],
            "complexity_tier": 3,
            "word_family": ["synthesis", "synthetic"],
        },
    ]
    
    corpus_file = tmp_path / "test_corpus.json"
    with open(corpus_file, "w") as f:
        json.dump(corpus_data, f)
    
    return corpus_file


@pytest.mark.unit
class TestVocabularyWord:
    """Test VocabularyWord model."""
    
    def test_create_vocabulary_word(self):
        """Test creating a vocabulary word."""
        word = VocabularyWord(
            word="analyze",
            grade_level=6,
            definition="examine in detail",
            subject_areas=["math", "science"],
            complexity_tier=2,
            word_family=["analysis"],
        )
        
        assert word.word == "analyze"
        assert word.grade_level == 6
        assert len(word.subject_areas) == 2
    
    def test_vocabulary_word_defaults(self):
        """Test vocabulary word with defaults."""
        word = VocabularyWord(
            word="test",
            grade_level=7,
            definition="test definition",
        )
        
        assert word.complexity_tier == 1
        assert word.subject_areas == []
        assert word.word_family == []


@pytest.mark.unit
class TestLoadVocabularyFromJson:
    """Test loading vocabulary from JSON files."""
    
    def test_load_vocabulary_from_json(self, sample_corpus_file):
        """Test loading vocabulary from a JSON file."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        assert len(words) == 3
        assert all(isinstance(w, VocabularyWord) for w in words)
        assert words[0].word == "analyze"
    
    def test_load_empty_json_file(self, tmp_path):
        """Test loading from empty JSON file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")
        
        words = load_vocabulary_from_json(empty_file)
        assert words == []
    
    def test_load_invalid_json_file(self, tmp_path):
        """Test loading from invalid JSON file raises error."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_vocabulary_from_json(invalid_file)


@pytest.mark.unit
@pytest.mark.aws
class TestCommonCoreLoader:
    """Test suite for CommonCoreLoader."""
    
    @pytest.fixture
    def loader(self, mock_aws_credentials, temp_env_vars):
        """Create a CommonCoreLoader instance for testing."""
        temp_env_vars(
            DYNAMODB_TABLE_PREFIX="test",
            S3_BUCKET_NAME="test-bucket",
            OPENAI_API_KEY="test-key",
        )
        return CommonCoreLoader()
    
    def test_get_by_grade_level(self, loader, sample_corpus_file):
        """Test getting words by grade level."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        # Filter grade 6 words
        grade_6_words = loader.filter_by_grade(words, grade_level=6)
        
        assert len(grade_6_words) == 2
        assert all(w.grade_level == 6 for w in grade_6_words)
    
    def test_get_by_word(self, loader, sample_corpus_file):
        """Test getting a word by its text."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        word = loader.get_by_word(words, word="analyze")
        
        assert word is not None
        assert word.word == "analyze"
        assert word.grade_level == 6
    
    def test_get_by_word_case_insensitive(self, loader, sample_corpus_file):
        """Test word lookup is case-insensitive."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        word1 = loader.get_by_word(words, word="analyze")
        word2 = loader.get_by_word(words, word="ANALYZE")
        
        assert word1 is not None
        assert word2 is not None
        assert word1.word == word2.word
    
    def test_get_by_word_not_found(self, loader, sample_corpus_file):
        """Test getting a word that doesn't exist returns None."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        word = loader.get_by_word(words, word="nonexistent")
        assert word is None
    
    def test_filter_by_subject_area(self, loader, sample_corpus_file):
        """Test filtering words by subject area."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        math_words = loader.filter_by_subject_area(words, subject_area="math")
        
        assert len(math_words) >= 1
        assert all("math" in w.subject_areas for w in math_words)
    
    def test_filter_by_complexity_tier(self, loader, sample_corpus_file):
        """Test filtering words by complexity tier."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        tier_2_words = loader.filter_by_complexity_tier(words, tier=2)
        
        assert len(tier_2_words) >= 1
        assert all(w.complexity_tier == 2 for w in tier_2_words)
    
    def test_get_word_family(self, loader, sample_corpus_file):
        """Test getting words in the same word family."""
        words = load_vocabulary_from_json(sample_corpus_file)
        
        # Get word family for "analyze"
        analyze_word = loader.get_by_word(words, word="analyze")
        family_words = loader.get_word_family(words, base_word="analyze")
        
        assert analyze_word is not None
        assert "analysis" in analyze_word.word_family
        # Should find words that have "analyze" in their word_family
        assert len(family_words) >= 1

