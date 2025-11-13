"""Vocabulary gap identification using Zone of Proximal Development (ZPD).

This module identifies vocabulary gaps by comparing student vocabulary
against Common Core standards and applying ZPD principles to select
appropriate challenge words.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.ai.cost_tracker import OperationType
from src.ai.openai_client import OpenAIClient, OpenAIError
from src.ai.prompts.gap_analysis import build_gap_analysis_prompt
from src.ai.vocabulary_extractor import ExtractedWord
from src.data.models.student_profile import StudentProfile
from src.vocabulary.common_core_loader import CommonCoreLoader, VocabularyWord
from src.utils.logger import get_logger

logger = get_logger("processing.gap_identifier")


@dataclass
class GapWord:
    """Represents a vocabulary gap word identified for a student."""

    word: str
    rationale: str
    difficulty_score: int  # 1-10 scale
    cc_grade_level: int  # Common Core grade level
    subject_areas: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "word": self.word,
            "rationale": self.rationale,
            "difficulty_score": self.difficulty_score,
            "cc_grade_level": self.cc_grade_level,
            "subject_areas": self.subject_areas,
        }


class GapIdentifier:
    """Identify vocabulary gaps using ZPD principles.

    Compares student vocabulary against Common Core standards and uses
    OpenAI (default: gpt-4o-mini for speed) to identify appropriate challenge words.
    """

    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        common_core_loader: Optional[CommonCoreLoader] = None,
        model: str = "gpt-4o-mini",  # Use faster model for gap analysis
        temperature: float = 0.7,
    ):
        """Initialize gap identifier.

        Args:
            openai_client: OpenAI client instance (creates new if None)
            common_core_loader: CommonCoreLoader instance (creates new if None)
            model: Model to use for gap analysis (default: gpt-4o-mini for speed)
            temperature: Sampling temperature (default: 0.7)
        """
        self.client = openai_client or OpenAIClient()
        self.common_core_loader = common_core_loader or CommonCoreLoader()
        self.model = model
        self.temperature = temperature

    async def identify_gaps(
        self,
        extracted_words: List[ExtractedWord],
        student_profile: StudentProfile,
        request_id: Optional[str] = None,
    ) -> List[GapWord]:
        """Identify vocabulary gaps for a student.

        Args:
            extracted_words: Words extracted from student's recent text
            student_profile: Student profile with current vocabulary
            request_id: Optional request ID for correlation

        Returns:
            List of GapWord objects representing vocabulary gaps

        Raises:
            OpenAIError: If gap analysis fails
        """
        logger.info(
            f"Identifying vocabulary gaps",
            extra={
                "student_id": student_profile.student_id,
                "grade_level": student_profile.grade_level,
                "vocab_size": len(student_profile.vocabulary_list),
                "extracted_words_count": len(extracted_words),
                "request_id": request_id,
            },
        )

        # Load Common Core vocabulary for student's grade
        common_core_words = self._load_common_core_vocabulary(
            student_profile.grade_level
        )

        if not common_core_words:
            logger.warning(
                f"No Common Core vocabulary found for grade {student_profile.grade_level}",
                extra={"student_id": student_profile.student_id, "request_id": request_id},
            )
            return []

        # Prepare data for prompt
        student_profile_dict = student_profile.to_dict()
        extracted_words_dict = [word.to_dict() for word in extracted_words]
        common_core_dict = [
            {
                "word": w.word,
                "grade_level": w.grade_level,
                "definition": w.definition,
                "subject_areas": w.subject_areas,
                "complexity_tier": w.complexity_tier,
            }
            for w in common_core_words
        ]

        # Build prompt
        messages = build_gap_analysis_prompt(
            student_profile=student_profile_dict,
            extracted_words=extracted_words_dict,
            common_core_words=common_core_dict,
        )

        # Call OpenAI API
        try:
            response = await self.client.complete(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2000,
                operation_type=OperationType.ANALYSIS,
                request_id=request_id,
            )
        except OpenAIError as e:
            logger.error(
                f"Failed to identify gaps",
                extra={
                    "student_id": student_profile.student_id,
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            raise

        # Parse response
        gaps = self._parse_response(response, student_profile)

        logger.info(
            "Identified vocabulary gaps",
            extra={
                "student_id": student_profile.student_id,
                "gaps_count": len(gaps),
                "request_id": request_id,
            },
        )

        return gaps

    def _load_common_core_vocabulary(self, grade_level: int) -> List[VocabularyWord]:
        """Load Common Core vocabulary for a grade level.

        Args:
            grade_level: Grade level (6, 7, or 8)

        Returns:
            List of VocabularyWord instances for the grade level
        """
        # Use CommonCoreLoader to load from JSON files
        corpus_dir = Path(__file__).parent.parent / "vocabulary" / "corpus"

        grade_files = {
            6: corpus_dir / "common_core_grade_6.json",
            7: corpus_dir / "common_core_grade_7.json",
            8: corpus_dir / "common_core_grade_8.json",
        }

        # Build file paths for loader
        file_paths = {
            "grade_6_file": grade_files.get(6),
            "grade_7_file": grade_files.get(7),
            "grade_8_file": grade_files.get(8),
        }

        # Filter out None values
        file_paths = {k: v for k, v in file_paths.items() if v and v.exists()}

        if not file_paths:
            logger.warning(
                f"No Common Core corpus files found",
                extra={"grade_level": grade_level},
            )
            return []

        try:
            # Use CommonCoreLoader to load all files
            all_words = self.common_core_loader.load_from_json_files(**file_paths)
            # Filter to only words for this grade level
            filtered = self.common_core_loader.filter_by_grade(all_words, grade_level)
            logger.debug(
                f"Loaded {len(filtered)} Common Core words for grade {grade_level}"
            )
            return filtered
        except Exception as e:
            logger.error(
                f"Failed to load Common Core vocabulary",
                extra={"grade_level": grade_level, "error": str(e)},
            )
            return []

    def _parse_response(
        self, response: str, student_profile: StudentProfile
    ) -> List[GapWord]:
        """Parse OpenAI API response into GapWord objects.

        Args:
            response: JSON response string from OpenAI
            student_profile: Student profile for validation

        Returns:
            List of GapWord objects

        Raises:
            ValueError: If response cannot be parsed
        """
        if not response or not response.strip():
            logger.warning("Empty response from OpenAI API")
            return []

        # Try to extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse gap analysis response as JSON",
                extra={"response_preview": response[:200], "error": str(e)},
            )
            raise ValueError(f"Invalid JSON response from OpenAI: {e}") from e

        # Extract gaps
        if not isinstance(data, dict) or "gaps" not in data:
            logger.warning("Response missing 'gaps' key")
            return []

        gaps_list = data.get("gaps", [])
        if not isinstance(gaps_list, list):
            logger.warning("'gaps' is not a list")
            return []

        # Get student's known words for filtering
        known_words = {
            entry.word.lower() for entry in student_profile.vocabulary_list
        }

        gap_words = []

        for gap_data in gaps_list:
            if not isinstance(gap_data, dict):
                continue

            word = gap_data.get("word", "").strip().lower()
            if not word:
                continue

            # Filter out words student already knows
            if word in known_words:
                logger.debug(f"Filtering out known word: {word}")
                continue

            rationale = gap_data.get("rationale", "").strip()
            if not rationale:
                rationale = f"Appropriate challenge word for grade {student_profile.grade_level}"

            difficulty_score = gap_data.get("difficulty_score", 5)
            if not isinstance(difficulty_score, int) or not (1 <= difficulty_score <= 10):
                difficulty_score = 5

            cc_grade_level = gap_data.get("cc_grade_level", student_profile.grade_level)
            if not isinstance(cc_grade_level, int) or cc_grade_level not in [6, 7, 8]:
                cc_grade_level = student_profile.grade_level

            subject_areas = gap_data.get("subject_areas", [])
            if not isinstance(subject_areas, list):
                subject_areas = []

            gap_words.append(
                GapWord(
                    word=word,
                    rationale=rationale,
                    difficulty_score=difficulty_score,
                    cc_grade_level=cc_grade_level,
                    subject_areas=subject_areas,
                )
            )

        return gap_words

    def _calculate_zpd_difficulty(
        self, student_vocab_size: int, grade_level: int
    ) -> Tuple[int, int]:
        """Calculate appropriate difficulty range for student (ZPD).

        Args:
            student_vocab_size: Number of unique words student knows
            grade_level: Student's grade level (6, 7, or 8)

        Returns:
            Tuple of (min_difficulty, max_difficulty) on 1-10 scale
        """
        # Expected vocabulary sizes by grade (approximate benchmarks)
        expected_sizes = {6: 100, 7: 150, 8: 200}

        expected_size = expected_sizes.get(grade_level, 150)

        # Base difficulty for grade (5 = grade-appropriate)
        base_difficulty = 5

        # Adjust based on vocabulary size relative to expected
        # Student at expected level → target difficulty 5-7
        # Student above expected → target difficulty 7-9
        # Student below expected → target difficulty 3-5
        adjustment = (student_vocab_size - expected_size) / 50.0
        adjustment = max(-2, min(2, adjustment))  # Clamp to -2 to +2

        min_difficulty = max(1, int(base_difficulty + adjustment))
        max_difficulty = min(10, int(base_difficulty + adjustment + 2))

        return (min_difficulty, max_difficulty)

    def _filter_missing_words(
        self,
        student_profile: StudentProfile,
        common_core_words: List[VocabularyWord],
    ) -> List[VocabularyWord]:
        """Filter Common Core words that student doesn't know.

        Args:
            student_profile: Student profile with vocabulary list
            common_core_words: List of Common Core vocabulary words

        Returns:
            List of VocabularyWord instances student doesn't know
        """
        known_words = {entry.word.lower() for entry in student_profile.vocabulary_list}

        missing = []
        for word in common_core_words:
            if word.word.lower() not in known_words:
                missing.append(word)

        return missing

    def _filter_by_difficulty_range(
        self, words: List[VocabularyWord], min_difficulty: int, max_difficulty: int
    ) -> List[VocabularyWord]:
        """Filter words by difficulty range.

        Args:
            words: List of vocabulary words
            min_difficulty: Minimum difficulty score (1-10)
            max_difficulty: Maximum difficulty score (1-10)

        Returns:
            Filtered list of words within difficulty range
        """
        filtered = []
        for word in words:
            # Calculate difficulty based on grade level and complexity tier
            difficulty = self._calculate_word_difficulty(word, word.grade_level)
            if min_difficulty <= difficulty <= max_difficulty:
                filtered.append(word)

        return filtered

    def _calculate_word_difficulty(
        self, word: VocabularyWord, student_grade: int
    ) -> int:
        """Calculate difficulty score for a word relative to student grade.

        Args:
            word: Vocabulary word to score
            student_grade: Student's grade level

        Returns:
            Difficulty score (1-10 scale)
        """
        # Base difficulty from grade level
        # Grade 6 word for grade 6 student = difficulty 5
        # Grade 7 word for grade 6 student = difficulty 7
        # Grade 8 word for grade 6 student = difficulty 9
        grade_diff = word.grade_level - student_grade
        base_difficulty = 5 + (grade_diff * 2)

        # Adjust for complexity tier
        # Tier 1 (easy) = -1, Tier 2 (medium) = 0, Tier 3 (hard) = +1
        tier_adjustment = word.complexity_tier - 2

        difficulty = base_difficulty + tier_adjustment

        # Clamp to 1-10 range
        return max(1, min(10, int(difficulty)))

