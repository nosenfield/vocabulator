"""Grade level mapping utilities for vocabulary.

This module provides utilities for mapping words to grade levels and
determining appropriate grade levels based on word characteristics.
"""

from typing import Dict, List, Optional
from src.vocabulary.common_core_loader import VocabularyWord
from src.utils.logger import get_logger

logger = get_logger("vocabulary.grade_level_mapper")


class GradeLevelMapper:
    """Utility for mapping vocabulary to grade levels.
    
    Provides methods for determining appropriate grade levels for words
    and mapping between different grade level representations.
    """
    
    # Common grade level mappings
    GRADE_LEVEL_NAMES: Dict[int, str] = {
        6: "sixth",
        7: "seventh",
        8: "eighth",
    }
    
    def __init__(self):
        """Initialize grade level mapper."""
        logger.debug("Initialized GradeLevelMapper")
    
    def get_grade_level_name(self, grade_level: int) -> str:
        """Get the name of a grade level.
        
        Args:
            grade_level: Grade level number (6, 7, or 8)
            
        Returns:
            Grade level name (e.g., "sixth", "seventh", "eighth")
        """
        return self.GRADE_LEVEL_NAMES.get(grade_level, f"grade_{grade_level}")
    
    def normalize_grade_level(self, grade_level: int) -> int:
        """Normalize grade level to valid range (6-8).
        
        Args:
            grade_level: Grade level to normalize
            
        Returns:
            Normalized grade level (clamped to 6-8)
        """
        if grade_level < 6:
            return 6
        if grade_level > 8:
            return 8
        return grade_level
    
    def get_words_for_grade_range(
        self,
        words: List[VocabularyWord],
        min_grade: int,
        max_grade: int,
    ) -> List[VocabularyWord]:
        """Get words within a grade level range.
        
        Args:
            words: List of vocabulary words
            min_grade: Minimum grade level (inclusive)
            max_grade: Maximum grade level (inclusive)
            
        Returns:
            Filtered list of words within the grade range
        """
        min_grade = self.normalize_grade_level(min_grade)
        max_grade = self.normalize_grade_level(max_grade)
        
        return [
            w for w in words
            if min_grade <= w.grade_level <= max_grade
        ]

