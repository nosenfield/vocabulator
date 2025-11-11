"""Common Core vocabulary loader and utilities.

This module provides functionality for loading and querying Common Core
vocabulary words from JSON corpus files and DynamoDB.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger("vocabulary.common_core")

__all__ = [
    "VocabularyWord",
    "CommonCoreLoader",
    "load_vocabulary_from_json",
]


class VocabularyWord(BaseModel):
    """A Common Core vocabulary word.
    
    Attributes:
        word: The vocabulary word
        grade_level: Grade level (6, 7, or 8)
        definition: Definition of the word
        subject_areas: List of subject areas where word is used
        complexity_tier: Complexity tier (1=easy, 2=medium, 3=hard)
        word_family: Related words (e.g., analyze -> analysis, analytical)
    """
    
    word: str = Field(..., description="The vocabulary word")
    grade_level: int = Field(..., ge=6, le=8, description="Grade level (6-8)")
    definition: str = Field(..., description="Definition of the word")
    subject_areas: List[str] = Field(
        default_factory=list,
        description="Subject areas (math, science, ela, etc.)",
    )
    complexity_tier: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Complexity tier (1-3)",
    )
    word_family: List[str] = Field(
        default_factory=list,
        description="Related words in the same family",
    )


def load_vocabulary_from_json(file_path: Path) -> List[VocabularyWord]:
    """Load vocabulary words from a JSON corpus file.
    
    Args:
        file_path: Path to JSON corpus file
        
    Returns:
        List of VocabularyWord instances
        
    Raises:
        ValueError: If file cannot be read or parsed
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        words = []
        for item in data:
            word = VocabularyWord(**item)
            words.append(word)
        
        logger.debug(f"Loaded {len(words)} words from {file_path}")
        return words
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in corpus file {file_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"Failed to load vocabulary from {file_path}: {e}") from e


class CommonCoreLoader:
    """Loader and query utilities for Common Core vocabulary.
    
    Provides methods for loading vocabulary from JSON files and querying
    by grade level, word, subject area, and complexity tier.
    """
    
    def __init__(self):
        """Initialize Common Core loader."""
        self._vocabulary_cache: Optional[List[VocabularyWord]] = None
        logger.debug("Initialized CommonCoreLoader")
    
    def load_from_json_files(
        self,
        grade_6_file: Optional[Path] = None,
        grade_7_file: Optional[Path] = None,
        grade_8_file: Optional[Path] = None,
    ) -> List[VocabularyWord]:
        """Load vocabulary from grade-level JSON files.
        
        Args:
            grade_6_file: Path to grade 6 corpus file
            grade_7_file: Path to grade 7 corpus file
            grade_8_file: Path to grade 8 corpus file
            
        Returns:
            Combined list of all vocabulary words
        """
        all_words = []
        
        if grade_6_file and grade_6_file.exists():
            words = load_vocabulary_from_json(grade_6_file)
            all_words.extend(words)
        
        if grade_7_file and grade_7_file.exists():
            words = load_vocabulary_from_json(grade_7_file)
            all_words.extend(words)
        
        if grade_8_file and grade_8_file.exists():
            words = load_vocabulary_from_json(grade_8_file)
            all_words.extend(words)
        
        self._vocabulary_cache = all_words
        logger.info(f"Loaded {len(all_words)} vocabulary words total")
        return all_words
    
    def filter_by_grade(
        self,
        words: List[VocabularyWord],
        grade_level: int,
    ) -> List[VocabularyWord]:
        """Filter words by grade level.
        
        Args:
            words: List of vocabulary words
            grade_level: Grade level to filter (6, 7, or 8)
            
        Returns:
            Filtered list of words for the specified grade
        """
        return [w for w in words if w.grade_level == grade_level]
    
    def get_by_word(
        self,
        words: List[VocabularyWord],
        word: str,
    ) -> Optional[VocabularyWord]:
        """Get a vocabulary word by its text (case-insensitive).
        
        Args:
            words: List of vocabulary words to search
            word: Word to find
            
        Returns:
            VocabularyWord if found, None otherwise
        """
        word_lower = word.lower()
        for w in words:
            if w.word.lower() == word_lower:
                return w
        return None
    
    def filter_by_subject_area(
        self,
        words: List[VocabularyWord],
        subject_area: str,
    ) -> List[VocabularyWord]:
        """Filter words by subject area.
        
        Args:
            words: List of vocabulary words
            subject_area: Subject area to filter (e.g., "math", "science", "ela")
            
        Returns:
            Filtered list of words for the specified subject area
        """
        return [w for w in words if subject_area.lower() in [s.lower() for s in w.subject_areas]]
    
    def filter_by_complexity_tier(
        self,
        words: List[VocabularyWord],
        tier: int,
    ) -> List[VocabularyWord]:
        """Filter words by complexity tier.
        
        Args:
            words: List of vocabulary words
            tier: Complexity tier (1, 2, or 3)
            
        Returns:
            Filtered list of words for the specified tier
        """
        return [w for w in words if w.complexity_tier == tier]
    
    def get_word_family(
        self,
        words: List[VocabularyWord],
        base_word: str,
    ) -> List[VocabularyWord]:
        """Get all words in the same word family as the base word.
        
        Args:
            words: List of vocabulary words
            base_word: Base word to find family for
            
        Returns:
            List of words in the same family (including the base word)
        """
        base_word_obj = self.get_by_word(words, base_word)
        if base_word_obj is None:
            return []
        
        family_words = [base_word_obj]
        base_word_lower = base_word.lower()
        
        # Find words that have the base word in their word_family
        for w in words:
            if w.word.lower() != base_word_lower:
                if any(base_word_lower == f.lower() for f in w.word_family):
                    family_words.append(w)
        
        # Find words that are in the base word's word_family
        for w in words:
            if w.word.lower() != base_word_lower:
                if w.word.lower() in [f.lower() for f in base_word_obj.word_family]:
                    if w not in family_words:
                        family_words.append(w)
        
        return family_words

