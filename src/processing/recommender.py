"""Vocabulary recommendation generation using OpenAI.

This module generates pedagogically sound vocabulary recommendations
from gap analysis results, including definitions, examples, and learning tips.
"""

import json
import re
from datetime import datetime, timezone
from typing import List, Optional

from src.ai.cost_tracker import OperationType
from src.ai.openai_client import OpenAIClient, OpenAIError
from src.ai.prompts.recommendation import build_recommendation_prompt
from src.data.models.recommendation import RecommendedWord, VocabularyRecommendation
from src.processing.gap_identifier import GapWord
from src.utils.logger import get_logger

logger = get_logger("processing.recommender")


class Recommender:
    """Generate vocabulary recommendations from gap analysis.

    Transforms gap words into comprehensive recommendations with definitions,
    example sentences, usage tips, and difficulty progression.
    """

    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
    ):
        """Initialize recommender.

        Args:
            openai_client: OpenAI client instance (creates new if None)
            model: Model to use for recommendation generation (default: gpt-4o)
            temperature: Sampling temperature (default: 0.7)
        """
        self.client = openai_client or OpenAIClient()
        self.model = model
        self.temperature = temperature

    async def generate(
        self,
        gap_words: List[GapWord],
        student_id: str,
        grade_level: int,
        request_id: Optional[str] = None,
    ) -> VocabularyRecommendation:
        """Generate vocabulary recommendations from gap words.

        Args:
            gap_words: List of gap words identified for the student
            student_id: Anonymous student identifier
            grade_level: Student's grade level (6-8)
            request_id: Optional request ID for correlation

        Returns:
            VocabularyRecommendation instance with recommended words

        Raises:
            OpenAIError: If recommendation generation fails
            ValueError: If response cannot be parsed
        """
        logger.info(
            f"Generating vocabulary recommendations",
            extra={
                "student_id": student_id,
                "grade_level": grade_level,
                "gap_words_count": len(gap_words),
                "request_id": request_id,
            },
        )

        # Handle empty gap words
        if not gap_words:
            logger.warning(
                f"No gap words provided, returning empty recommendation",
                extra={"student_id": student_id, "request_id": request_id},
            )
            return self._create_empty_recommendation(student_id, grade_level)

        # Prepare gap words data for prompt
        gap_words_dict = [gap.to_dict() for gap in gap_words]

        # Build prompt
        messages = build_recommendation_prompt(
            student_id=student_id,
            grade_level=grade_level,
            gap_words=gap_words_dict,
        )

        # Call OpenAI API
        try:
            response = await self.client.complete(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=3000,
                operation_type=OperationType.RECOMMENDATION,
                request_id=request_id,
            )
        except OpenAIError as e:
            logger.error(
                f"Failed to generate recommendations",
                extra={
                    "student_id": student_id,
                    "error": str(e),
                    "request_id": request_id,
                },
            )
            raise

        # Parse response
        recommended_words = self._parse_response(response, grade_level)

        # Order by difficulty (easiest first)
        recommended_words.sort(key=lambda w: w.difficulty_score)

        # Create recommendation
        recommendation = VocabularyRecommendation(
            student_id=student_id,
            recommendation_date=datetime.now(timezone.utc).date().isoformat(),
            words=recommended_words,
        )

        logger.info(
            f"Generated {len(recommended_words)} recommendations",
            extra={
                "student_id": student_id,
                "recommendations_count": len(recommended_words),
                "request_id": request_id,
            },
        )

        return recommendation

    def _parse_response(
        self, response: str, grade_level: int
    ) -> List[RecommendedWord]:
        """Parse OpenAI API response into RecommendedWord objects.

        Args:
            response: JSON response string from OpenAI
            grade_level: Student's grade level for default grade_level

        Returns:
            List of RecommendedWord instances

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
                f"Failed to parse recommendation response as JSON",
                extra={"response_preview": response[:200], "error": str(e)},
            )
            raise ValueError(f"Invalid JSON response from OpenAI: {e}") from e

        # Extract recommendations
        if not isinstance(data, dict) or "recommendations" not in data:
            logger.warning("Response missing 'recommendations' key")
            return []

        recommendations_list = data.get("recommendations", [])
        if not isinstance(recommendations_list, list):
            logger.warning("'recommendations' is not a list")
            return []

        recommended_words = []

        for rec_data in recommendations_list:
            if not isinstance(rec_data, dict):
                continue

            word = rec_data.get("word", "").strip().lower()
            if not word:
                continue

            definition = rec_data.get("definition", "").strip()
            if not definition:
                definition = f"A vocabulary word for grade {grade_level} students"

            # Convert difficulty score from 1-10 scale to 0.0-1.0 scale
            # If already in 0.0-1.0 scale, use as-is
            difficulty_score = rec_data.get("difficulty_score", 0.5)
            if isinstance(difficulty_score, (int, float)):
                # If score is > 1.0, assume it's 1-10 scale and convert
                if difficulty_score > 1.0:
                    difficulty_score = difficulty_score / 10.0
                # Clamp to 0.0-1.0 range
                difficulty_score = max(0.0, min(1.0, float(difficulty_score)))
            else:
                difficulty_score = 0.5

            rationale = rec_data.get("rationale", "").strip()
            if not rationale:
                rationale = f"Appropriate vocabulary word for grade {grade_level} students"

            example_sentences = rec_data.get("example_sentences", [])
            if not isinstance(example_sentences, list):
                example_sentences = []
            # Ensure we have at least one example
            if not example_sentences:
                example_sentences = [f"Example: Use '{word}' in a sentence."]

            # Use cc_grade_level from gap word if available, otherwise use student grade
            rec_grade_level = rec_data.get("cc_grade_level", grade_level)
            if not isinstance(rec_grade_level, int) or rec_grade_level not in [6, 7, 8]:
                rec_grade_level = grade_level

            recommended_words.append(
                RecommendedWord(
                    word=word,
                    definition=definition,
                    grade_level=rec_grade_level,
                    difficulty_score=difficulty_score,
                    rationale=rationale,
                    example_sentences=example_sentences,
                )
            )

        return recommended_words

    def _create_empty_recommendation(
        self, student_id: str, grade_level: int
    ) -> VocabularyRecommendation:
        """Create an empty recommendation when no gap words provided.

        Args:
            student_id: Anonymous student identifier
            grade_level: Student's grade level

        Returns:
            VocabularyRecommendation with empty words list
        """
        return VocabularyRecommendation(
            student_id=student_id,
            recommendation_date=datetime.now(timezone.utc).date().isoformat(),
            words=[],
        )

