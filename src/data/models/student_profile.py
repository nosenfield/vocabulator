"""Student profile data model.

This module defines the StudentProfile model and related data structures
for tracking student vocabulary and proficiency.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class VocabularyEntry(BaseModel):
    """A single vocabulary word entry for a student.
    
    Attributes:
        word: The vocabulary word
        first_seen: Timestamp when word was first encountered
        usage_count: Number of times word has been used
        contexts: List of subject areas where word was used
    """
    
    word: str = Field(..., description="The vocabulary word")
    first_seen: datetime = Field(..., description="When word was first encountered")
    usage_count: int = Field(default=1, ge=1, description="Number of times word used")
    contexts: List[str] = Field(default_factory=list, description="Subject areas")
    
    @field_validator("usage_count")
    @classmethod
    def validate_usage_count(cls, v: int) -> int:
        """Validate usage count is positive."""
        if v < 1:
            raise ValueError("usage_count must be at least 1")
        return v


class ProficiencyScore(BaseModel):
    """Proficiency score calculation result.
    
    Attributes:
        score: Overall proficiency score (0-100)
        vocabulary_size: Number of unique words
        average_usage: Average usage count per word
    """
    
    score: float = Field(..., ge=0.0, le=100.0, description="Proficiency score")
    vocabulary_size: int = Field(..., ge=0, description="Number of unique words")
    average_usage: float = Field(..., ge=0.0, description="Average usage per word")


class StudentProfile(BaseModel):
    """Student vocabulary profile.
    
    Tracks a student's vocabulary knowledge, usage patterns, and proficiency
    score. Used for generating personalized vocabulary recommendations.
    
    Attributes:
        student_id: Anonymous student identifier
        grade_level: Student's grade level (6-8)
        vocabulary_list: List of vocabulary words the student knows
        proficiency_score: Calculated proficiency score (0-100)
        profile_version: Version number for schema evolution
        created_at: Profile creation timestamp
        last_updated: Last update timestamp
    """
    
    student_id: str = Field(..., description="Anonymous student identifier")
    grade_level: int = Field(..., ge=6, le=8, description="Grade level (6-8)")
    vocabulary_list: List[VocabularyEntry] = Field(
        default_factory=list,
        description="List of vocabulary words",
    )
    proficiency_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Proficiency score (0-100)",
    )
    profile_version: int = Field(default=1, ge=1, description="Schema version")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )
    metadata: Dict = Field(
        default_factory=dict,
        description="Optional metadata (e.g., class information)",
    )
    
    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v: int) -> int:
        """Validate grade level is 6-8."""
        if v not in [6, 7, 8]:
            raise ValueError("grade_level must be 6, 7, or 8")
        return v
    
    def add_vocabulary(self, entry: VocabularyEntry) -> None:
        """Add a vocabulary word to the profile.
        
        If the word already exists, updates the usage count and contexts.
        Otherwise, adds a new entry.
        
        Args:
            entry: Vocabulary entry to add
        """
        # Check if word already exists
        for existing_entry in self.vocabulary_list:
            if existing_entry.word.lower() == entry.word.lower():
                # Update existing entry
                existing_entry.usage_count += entry.usage_count
                # Merge contexts (dedupe)
                for context in entry.contexts:
                    if context not in existing_entry.contexts:
                        existing_entry.contexts.append(context)
                # Update first_seen if this is earlier
                if entry.first_seen < existing_entry.first_seen:
                    existing_entry.first_seen = entry.first_seen
                self.last_updated = datetime.now(timezone.utc)
                return
        
        # Add new entry
        self.vocabulary_list.append(entry)
        self.last_updated = datetime.now(timezone.utc)
    
    def calculate_proficiency_score(self) -> float:
        """Calculate proficiency score based on vocabulary.
        
        Score calculation:
        - Base score from vocabulary size (max 50 points)
        - Usage diversity bonus (max 30 points)
        - Grade-level alignment bonus (max 20 points)
        
        Returns:
            Proficiency score (0-100)
        """
        if not self.vocabulary_list:
            self.proficiency_score = 0.0
            return 0.0
        
        vocabulary_size = len(self.vocabulary_list)
        
        # Base score from vocabulary size (0-50 points)
        # Target: 500 words for grade level = 50 points
        # Formula: min(50, (vocabulary_size / 500) * 50)
        base_score = min(50.0, (vocabulary_size / 500.0) * 50.0)
        
        # Usage diversity bonus (0-30 points)
        # Based on average usage count and context diversity
        total_usage = sum(entry.usage_count for entry in self.vocabulary_list)
        average_usage = total_usage / vocabulary_size if vocabulary_size > 0 else 0
        
        # Bonus for higher average usage (up to 20 points)
        usage_bonus = min(20.0, (average_usage / 5.0) * 20.0)
        
        # Bonus for context diversity (up to 10 points)
        all_contexts = set()
        for entry in self.vocabulary_list:
            all_contexts.update(entry.contexts)
        context_diversity = len(all_contexts)
        context_bonus = min(10.0, (context_diversity / 5.0) * 10.0)
        
        usage_diversity_score = usage_bonus + context_bonus
        
        # Grade-level alignment bonus (0-20 points)
        # This would ideally check against Common Core vocabulary
        # For now, simplified: bonus based on vocabulary size relative to grade
        grade_alignment_bonus = min(20.0, (vocabulary_size / 100.0) * 20.0)
        
        score = base_score + usage_diversity_score + grade_alignment_bonus
        score = min(100.0, max(0.0, score))  # Clamp to 0-100
        
        self.proficiency_score = score
        return score
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary for DynamoDB storage.
        
        Returns:
            Dictionary representation suitable for DynamoDB
        """
        result = {
            "student_id": self.student_id,
            "profile_version": self.profile_version,
            "grade_level": self.grade_level,
            "vocabulary_list": [
                {
                    "word": entry.word,
                    "first_seen": entry.first_seen.isoformat(),
                    "usage_count": entry.usage_count,
                    "contexts": entry.contexts,
                }
                for entry in self.vocabulary_list
            ],
            "proficiency_score": Decimal(str(self.proficiency_score)),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
        # Include metadata if it exists (for class information)
        # Always include metadata dict, even if empty, to ensure it's persisted
        result["metadata"] = self.metadata if self.metadata else {}
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StudentProfile":
        """Create profile from dictionary (e.g., from DynamoDB).
        
        Args:
            data: Dictionary containing profile data
            
        Returns:
            StudentProfile instance
        """
        # Convert vocabulary list entries
        vocabulary_list = []
        for entry_data in data.get("vocabulary_list", []):
            entry = VocabularyEntry(
                word=entry_data["word"],
                first_seen=datetime.fromisoformat(entry_data["first_seen"]),
                usage_count=entry_data.get("usage_count", 1),
                contexts=entry_data.get("contexts", []),
            )
            vocabulary_list.append(entry)
        
        # Convert Decimal to float for proficiency_score if needed
        proficiency_score = data.get("proficiency_score", 0.0)
        if isinstance(proficiency_score, Decimal):
            proficiency_score = float(proficiency_score)

        profile = cls(
            student_id=data["student_id"],
            grade_level=data["grade_level"],
            vocabulary_list=vocabulary_list,
            proficiency_score=proficiency_score,
            profile_version=data.get("profile_version", 1),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now(timezone.utc).isoformat())),
        )
        # Set metadata if it exists in the data, otherwise use empty dict
        # This ensures metadata is always set, even if not in DynamoDB item
        profile.metadata = data.get("metadata", {})
        return profile

