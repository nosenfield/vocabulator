"""Text processing pipeline for vocabulary analysis.

This module provides an end-to-end pipeline that orchestrates:
1. Vocabulary extraction from student text
2. Student profile updates
3. Gap identification
4. Recommendation generation
5. Recommendation persistence
"""

from datetime import datetime, timezone
from typing import Optional

from src.ai.vocabulary_extractor import ExtractedWord, VocabularyExtractor
from src.data.models.recommendation import VocabularyRecommendation
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.repositories.student_repository import StudentRepository
from src.processing.gap_identifier import GapIdentifier, GapWord
from src.processing.recommender import Recommender
from src.utils.logger import get_logger

logger = get_logger("processing.text_processing_pipeline")


class TextProcessingPipeline:
    """End-to-end text processing pipeline.

    Orchestrates the complete workflow:
    - Extract vocabulary from text
    - Update student profile with extracted words
    - Identify vocabulary gaps
    - Generate personalized recommendations
    - Persist recommendations
    """

    def __init__(
        self,
        extractor: Optional[VocabularyExtractor] = None,
        gap_identifier: Optional[GapIdentifier] = None,
        recommender: Optional[Recommender] = None,
        student_repository: Optional[StudentRepository] = None,
        recommendation_repository: Optional[RecommendationRepository] = None,
        default_grade_level: int = 7,
    ):
        """Initialize text processing pipeline.

        Args:
            extractor: Vocabulary extractor instance (creates new if None)
            gap_identifier: Gap identifier instance (creates new if None)
            recommender: Recommender instance (creates new if None)
            student_repository: Student repository instance (creates new if None)
            recommendation_repository: Recommendation repository instance (creates new if None)
            default_grade_level: Default grade level for new profiles (default: 7)
        """
        self.extractor = extractor or VocabularyExtractor()
        self.gap_identifier = gap_identifier or GapIdentifier()
        self.recommender = recommender or Recommender()
        self.student_repository = student_repository or StudentRepository()
        self.recommendation_repository = (
            recommendation_repository or RecommendationRepository()
        )
        self.default_grade_level = default_grade_level

    async def process_text(
        self,
        text: str,
        student_id: str,
        grade_level: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> VocabularyRecommendation:
        """Process student text through complete pipeline.

        Args:
            text: Student text to process (transcript or writing sample)
            student_id: Anonymous student identifier
            grade_level: Optional grade level (uses profile grade if not provided)
            request_id: Optional request ID for correlation

        Returns:
            VocabularyRecommendation with generated recommendations

        Raises:
            ValueError: If student_id is invalid
            OpenAIError: If extraction or analysis fails
        """
        if not student_id or not student_id.strip():
            raise ValueError("student_id is required")

        logger.info(
            f"Starting text processing pipeline",
            extra={
                "student_id": student_id,
                "text_length": len(text) if text else 0,
                "request_id": request_id,
            },
        )

        # Step 1: Extract vocabulary from text
        extracted_words = await self._extract_vocabulary(text, request_id)

        # Step 2: Get or create student profile
        student_profile = await self._get_or_create_profile(
            student_id, grade_level, request_id
        )

        # Step 3: Update profile with extracted words
        updated_profile = await self._update_profile_with_words(
            student_profile, extracted_words, request_id
        )

        # Step 4: Identify vocabulary gaps
        gap_words = await self._identify_gaps(
            extracted_words, updated_profile, request_id
        )

        # Step 5: Generate recommendations
        recommendation = await self._generate_recommendations(
            gap_words, updated_profile, request_id
        )

        # Step 6: Persist recommendations
        await self._persist_recommendations(recommendation, request_id)

        logger.info(
            f"Text processing pipeline completed",
            extra={
                "student_id": student_id,
                "extracted_words": len(extracted_words),
                "gap_words": len(gap_words),
                "recommendations": len(recommendation.words),
                "request_id": request_id,
            },
        )

        return recommendation

    async def _extract_vocabulary(
        self, text: str, request_id: Optional[str] = None
    ) -> list[ExtractedWord]:
        """Extract vocabulary from text.

        Args:
            text: Text to extract vocabulary from
            request_id: Optional request ID

        Returns:
            List of extracted vocabulary words
        """
        logger.debug(
            f"Extracting vocabulary from text",
            extra={"text_length": len(text) if text else 0, "request_id": request_id},
        )

        extracted_words = await self.extractor.extract(
            text=text,
            use_cache=True,
            request_id=request_id,
        )

        logger.debug(
            f"Extracted {len(extracted_words)} vocabulary words",
            extra={"word_count": len(extracted_words), "request_id": request_id},
        )

        return extracted_words

    async def _get_or_create_profile(
        self,
        student_id: str,
        grade_level: Optional[int],
        request_id: Optional[str] = None,
    ) -> StudentProfile:
        """Get existing student profile or create new one.

        Args:
            student_id: Student identifier
            grade_level: Optional grade level (uses default if not provided)
            request_id: Optional request ID

        Returns:
            StudentProfile instance
        """
        logger.debug(
            f"Getting or creating student profile",
            extra={"student_id": student_id, "request_id": request_id},
        )

        # Try to get existing profile
        profile = self.student_repository.get(student_id, profile_version=1)

        if profile is None:
            # Create new profile
            grade = grade_level or self.default_grade_level
            profile = StudentProfile(
                student_id=student_id,
                grade_level=grade,
            )
            profile = self.student_repository.create(profile)
            logger.info(
                f"Created new student profile",
                extra={
                    "student_id": student_id,
                    "grade_level": grade,
                    "request_id": request_id,
                },
            )
        else:
            logger.debug(
                f"Found existing student profile",
                extra={
                    "student_id": student_id,
                    "vocab_size": len(profile.vocabulary_list),
                    "request_id": request_id,
                },
            )

        return profile

    async def _update_profile_with_words(
        self,
        profile: StudentProfile,
        extracted_words: list[ExtractedWord],
        request_id: Optional[str] = None,
    ) -> StudentProfile:
        """Update student profile with extracted words.

        Args:
            profile: Student profile to update
            extracted_words: List of extracted vocabulary words
            request_id: Optional request ID

        Returns:
            Updated StudentProfile instance
        """
        if not extracted_words:
            logger.debug(
                f"No words to add to profile",
                extra={"student_id": profile.student_id, "request_id": request_id},
            )
            return profile

        logger.debug(
            f"Updating profile with extracted words",
            extra={
                "student_id": profile.student_id,
                "words_to_add": len(extracted_words),
                "request_id": request_id,
            },
        )

        # Add each extracted word to profile
        for extracted_word in extracted_words:
            # Determine context from example (simplified)
            # In production, this could be more sophisticated
            contexts = ["general"]
            if extracted_word.example:
                example_lower = extracted_word.example.lower()
                if any(subject in example_lower for subject in ["science", "scientific"]):
                    contexts.append("science")
                if any(subject in example_lower for subject in ["math", "mathematical", "calculate"]):
                    contexts.append("math")
                if any(subject in example_lower for subject in ["history", "historical", "past"]):
                    contexts.append("history")
                if any(subject in example_lower for subject in ["english", "literature", "writing"]):
                    contexts.append("ela")

            # Create vocabulary entry
            entry = VocabularyEntry(
                word=extracted_word.word,
                first_seen=datetime.now(timezone.utc),
                usage_count=extracted_word.count,
                contexts=contexts,
            )

            # Use the add_vocabulary method which handles deduplication
            profile.add_vocabulary(entry)

        # Recalculate proficiency score
        profile.calculate_proficiency_score()

        # Update timestamp
        profile.last_updated = datetime.now(timezone.utc)

        # Save updated profile
        updated_profile = self.student_repository.update(profile)

        logger.info(
            f"Updated student profile with {len(extracted_words)} words",
            extra={
                "student_id": profile.student_id,
                "total_vocab_size": len(updated_profile.vocabulary_list),
                "request_id": request_id,
            },
        )

        return updated_profile

    async def _identify_gaps(
        self,
        extracted_words: list[ExtractedWord],
        profile: StudentProfile,
        request_id: Optional[str] = None,
    ) -> list[GapWord]:
        """Identify vocabulary gaps for student.

        Args:
            extracted_words: List of extracted vocabulary words
            profile: Student profile
            request_id: Optional request ID

        Returns:
            List of GapWord objects representing vocabulary gaps
        """
        logger.debug(
            f"Identifying vocabulary gaps",
            extra={
                "student_id": profile.student_id,
                "extracted_words": len(extracted_words),
                "request_id": request_id,
            },
        )

        gap_words = await self.gap_identifier.identify_gaps(
            extracted_words=extracted_words,
            student_profile=profile,
            request_id=request_id,
        )

        logger.debug(
            f"Identified {len(gap_words)} vocabulary gaps",
            extra={
                "student_id": profile.student_id,
                "gap_count": len(gap_words),
                "request_id": request_id,
            },
        )

        return gap_words

    async def _generate_recommendations(
        self,
        gap_words: list[GapWord],
        profile: StudentProfile,
        request_id: Optional[str] = None,
    ) -> VocabularyRecommendation:
        """Generate vocabulary recommendations from gap words.

        Args:
            gap_words: List of gap words
            profile: Student profile
            request_id: Optional request ID

        Returns:
            VocabularyRecommendation instance
        """
        logger.debug(
            f"Generating vocabulary recommendations",
            extra={
                "student_id": profile.student_id,
                "gap_words": len(gap_words),
                "request_id": request_id,
            },
        )

        recommendation = await self.recommender.generate(
            gap_words=gap_words,
            student_id=profile.student_id,
            grade_level=profile.grade_level,
            request_id=request_id,
        )

        logger.debug(
            f"Generated {len(recommendation.words)} recommendations",
            extra={
                "student_id": profile.student_id,
                "recommendations": len(recommendation.words),
                "request_id": request_id,
            },
        )

        return recommendation

    async def _persist_recommendations(
        self,
        recommendation: VocabularyRecommendation,
        request_id: Optional[str] = None,
    ) -> VocabularyRecommendation:
        """Persist recommendations to database.

        Args:
            recommendation: Recommendation to persist
            request_id: Optional request ID

        Returns:
            Persisted VocabularyRecommendation instance
        """
        logger.debug(
            f"Persisting recommendations",
            extra={
                "student_id": recommendation.student_id,
                "recommendations": len(recommendation.words),
                "request_id": request_id,
            },
        )

        persisted = self.recommendation_repository.create(recommendation)

        logger.info(
            f"Persisted recommendations",
            extra={
                "student_id": recommendation.student_id,
                "recommendation_date": recommendation.recommendation_date,
                "request_id": request_id,
            },
        )

        return persisted

