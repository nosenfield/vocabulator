"""Vocabulary recommendation data model.

This module defines the VocabularyRecommendation model and related data structures
for tracking vocabulary word recommendations for students.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RecommendationStatus(str, Enum):
    """Status of a vocabulary recommendation."""
    
    PENDING = "pending"
    ASSIGNED = "assigned"
    LEARNED = "learned"


class RecommendedWord(BaseModel):
    """A single recommended vocabulary word.
    
    Attributes:
        word: The vocabulary word
        definition: Definition of the word
        grade_level: Grade level for this word (6-8)
        difficulty_score: Difficulty score (0.0-1.0)
        rationale: Explanation of why this word was recommended
        example_sentences: Example sentences using the word
    """
    
    word: str = Field(..., description="The vocabulary word")
    definition: str = Field(..., description="Definition of the word")
    grade_level: int = Field(..., ge=6, le=8, description="Grade level (6-8)")
    difficulty_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Difficulty score (0.0=easy, 1.0=hard)",
    )
    rationale: str = Field(
        default="",
        description="Explanation of why this word was recommended",
    )
    example_sentences: List[str] = Field(
        default_factory=list,
        description="Example sentences using the word",
    )
    
    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v: int) -> int:
        """Validate grade level is 6-8."""
        if v not in [6, 7, 8]:
            raise ValueError("grade_level must be 6, 7, or 8")
        return v
    
    @field_validator("difficulty_score")
    @classmethod
    def validate_difficulty_score(cls, v: float) -> float:
        """Validate difficulty score is 0-1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("difficulty_score must be between 0.0 and 1.0")
        return v


class VocabularyRecommendation(BaseModel):
    """Vocabulary recommendation for a student.
    
    Contains a list of recommended words with definitions, difficulty scores,
    and example sentences. Recommendations expire after 30 days (TTL).
    
    Attributes:
        student_id: Anonymous student identifier
        recommendation_date: Date when recommendation was generated (ISO 8601 date string)
        words: List of recommended words
        status: Current status of the recommendation
        generated_by: ID of the batch job that generated this recommendation
        expires_at: Unix timestamp for TTL expiration (30 days from creation)
    """
    
    student_id: str = Field(..., description="Anonymous student identifier")
    recommendation_date: str = Field(
        ...,
        description="Date when recommendation was generated (ISO 8601 date string)",
    )
    words: List[RecommendedWord] = Field(
        default_factory=list,
        description="List of recommended words",
    )
    status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING,
        description="Current status of the recommendation",
    )
    generated_by: Optional[str] = Field(
        default=None,
        description="ID of the batch job that generated this recommendation",
    )
    expires_at: int = Field(
        ...,
        description="Unix timestamp for TTL expiration",
    )
    
    def __init__(self, **data):
        """Initialize recommendation with automatic TTL calculation."""
        # If expires_at not provided, calculate it (30 days from now)
        if "expires_at" not in data:
            expires_at = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
            data["expires_at"] = expires_at
        
        # Convert recommendation_date to string if it's a date object
        if "recommendation_date" in data:
            rec_date = data["recommendation_date"]
            if isinstance(rec_date, datetime):
                data["recommendation_date"] = rec_date.date().isoformat()
            elif hasattr(rec_date, "isoformat"):
                data["recommendation_date"] = rec_date.isoformat()
        
        super().__init__(**data)
    
    def to_dict(self) -> Dict:
        """Convert recommendation to dictionary for DynamoDB storage.
        
        Returns:
            Dictionary representation suitable for DynamoDB
        """
        return {
            "student_id": self.student_id,
            "recommendation_date": self.recommendation_date,
            "words": [
                {
                    "word": word.word,
                    "definition": word.definition,
                    "grade_level": word.grade_level,
                    "difficulty_score": Decimal(str(word.difficulty_score)),
                    "rationale": word.rationale,
                    "example_sentences": word.example_sentences,
                }
                for word in self.words
            ],
            "status": self.status.value,
            "generated_by": self.generated_by,
            "expires_at": self.expires_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "VocabularyRecommendation":
        """Create recommendation from dictionary (e.g., from DynamoDB).
        
        Args:
            data: Dictionary containing recommendation data
            
        Returns:
            VocabularyRecommendation instance
        """
        # Convert words list
        words = []
        for word_data in data.get("words", []):
            # Convert Decimal to float for difficulty_score if needed
            difficulty_score = word_data.get("difficulty_score", 0.5)
            if isinstance(difficulty_score, Decimal):
                difficulty_score = float(difficulty_score)

            word = RecommendedWord(
                word=word_data["word"],
                definition=word_data["definition"],
                grade_level=word_data["grade_level"],
                difficulty_score=difficulty_score,
                rationale=word_data.get("rationale", ""),
                example_sentences=word_data.get("example_sentences", []),
            )
            words.append(word)
        
        # Convert status string to enum
        status_str = data.get("status", "pending")
        status = RecommendationStatus(status_str)
        
        return cls(
            student_id=data["student_id"],
            recommendation_date=data["recommendation_date"],
            words=words,
            status=status,
            generated_by=data.get("generated_by"),
            expires_at=data.get("expires_at", int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())),
        )

