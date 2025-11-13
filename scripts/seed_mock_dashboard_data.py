#!/usr/bin/env python3
"""Seed mock student data for dashboard demo.

This script populates DynamoDB with 15-20 mock students across 3 classes
(7A-ELA, 7B-ELA, 8A-ELA) for dashboard demonstration purposes.
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.student_repository import StudentRepository
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.vocabulary.common_core_loader import CommonCoreLoader

logger = get_logger("scripts.seed_mock_dashboard_data")

# Academic vocabulary words for middle school (grades 6-8)
ACADEMIC_VOCABULARY = [
    "analyze", "evaluate", "synthesize", "comprehend", "interpret",
    "persuade", "demonstrate", "illustrate", "elaborate", "articulate",
    "contradict", "substantiate", "hypothesize", "investigate", "examine",
    "conclude", "summarize", "paraphrase", "infer", "deduce",
    "metaphor", "simile", "alliteration", "personification", "hyperbole",
    "protagonist", "antagonist", "narrative", "dialogue", "characterization",
    "theme", "symbolism", "foreshadowing", "irony", "conflict",
    "renewable", "sustainable", "ecosystem",     "photosynthesis", "chlorophyll",
    "chloroplast", "glucose", "carbon dioxide", "oxygen",
    "climate", "atmosphere", "greenhouse", "emissions", "conservation",
    "prejudice", "justice", "morality", "integrity", "courage",
    "complexity", "perspective", "context", "significance", "relevance"
]


def generate_vocabulary_entries(size: int, grade_level: int) -> List[VocabularyEntry]:
    """Generate mock vocabulary entries for a student.
    
    Args:
        size: Number of vocabulary words to generate
        grade_level: Student's grade level (6, 7, or 8)
        
    Returns:
        List of VocabularyEntry objects
    """
    # Select words appropriate for grade level
    # Mix of academic vocabulary and common words
    selected_words = random.sample(ACADEMIC_VOCABULARY, min(size, len(ACADEMIC_VOCABULARY)))
    
    # If we need more words, repeat some with different contexts
    while len(selected_words) < size:
        selected_words.append(random.choice(ACADEMIC_VOCABULARY))
    
    subject_areas = ["science", "literature", "social studies", "math", "ela"]
    
    entries = []
    for word in selected_words[:size]:
        # Generate usage count (higher for higher grade students)
        base_usage = 1 + (grade_level - 6) * 2
        usage_count = random.randint(base_usage, base_usage + 5)
        
        # Generate contexts (subject areas where word was used)
        num_contexts = random.randint(1, 3)
        contexts = random.sample(subject_areas, min(num_contexts, len(subject_areas)))
        
        # Generate first_seen timestamp (within last 6 months)
        days_ago = random.randint(0, 180)
        first_seen = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        entry = VocabularyEntry(
            word=word,
            first_seen=first_seen,
            usage_count=usage_count,
            contexts=contexts
        )
        entries.append(entry)
    
    return entries


# Mock student data - 18 students across 3 classes
MOCK_STUDENTS = [
    # 7A-ELA (6 students)
    {"student_id": "STU-001", "grade_level": 7, "class": "7A-ELA", "vocab_size": 120, "proficiency_range": (70, 85)},
    {"student_id": "STU-002", "grade_level": 7, "class": "7A-ELA", "vocab_size": 95, "proficiency_range": (60, 75)},
    {"student_id": "STU-003", "grade_level": 7, "class": "7A-ELA", "vocab_size": 110, "proficiency_range": (65, 80)},
    {"student_id": "STU-004", "grade_level": 7, "class": "7A-ELA", "vocab_size": 85, "proficiency_range": (50, 65)},
    {"student_id": "STU-005", "grade_level": 7, "class": "7A-ELA", "vocab_size": 130, "proficiency_range": (75, 90)},
    {"student_id": "STU-006", "grade_level": 7, "class": "7A-ELA", "vocab_size": 100, "proficiency_range": (55, 70)},
    
    # 7B-ELA (6 students)
    {"student_id": "STU-007", "grade_level": 7, "class": "7B-ELA", "vocab_size": 105, "proficiency_range": (65, 80)},
    {"student_id": "STU-008", "grade_level": 7, "class": "7B-ELA", "vocab_size": 90, "proficiency_range": (55, 70)},
    {"student_id": "STU-009", "grade_level": 7, "class": "7B-ELA", "vocab_size": 115, "proficiency_range": (70, 85)},
    {"student_id": "STU-010", "grade_level": 7, "class": "7B-ELA", "vocab_size": 80, "proficiency_range": (45, 60)},
    {"student_id": "STU-011", "grade_level": 7, "class": "7B-ELA", "vocab_size": 125, "proficiency_range": (75, 90)},
    {"student_id": "STU-012", "grade_level": 7, "class": "7B-ELA", "vocab_size": 95, "proficiency_range": (60, 75)},
    
    # 8A-ELA (6 students)
    {"student_id": "STU-013", "grade_level": 8, "class": "8A-ELA", "vocab_size": 140, "proficiency_range": (80, 95)},
    {"student_id": "STU-014", "grade_level": 8, "class": "8A-ELA", "vocab_size": 120, "proficiency_range": (70, 85)},
    {"student_id": "STU-015", "grade_level": 8, "class": "8A-ELA", "vocab_size": 110, "proficiency_range": (65, 80)},
    {"student_id": "STU-016", "grade_level": 8, "class": "8A-ELA", "vocab_size": 100, "proficiency_range": (60, 75)},
    {"student_id": "STU-017", "grade_level": 8, "class": "8A-ELA", "vocab_size": 135, "proficiency_range": (75, 90)},
    {"student_id": "STU-018", "grade_level": 8, "class": "8A-ELA", "vocab_size": 115, "proficiency_range": (70, 85)},
]


def seed_students() -> None:
    """Populate DynamoDB with mock students for dashboard demo."""
    config = get_config()
    repo = StudentRepository()
    
    logger.info("Starting mock student data seeding for dashboard...")
    
    created_count = 0
    updated_count = 0
    
    for student_data in MOCK_STUDENTS:
        student_id = student_data["student_id"]
        grade_level = student_data["grade_level"]
        class_name = student_data["class"]
        vocab_size = student_data["vocab_size"]
        proficiency_range = student_data["proficiency_range"]
        
        # Check if student already exists
        try:
            existing = repo.get(student_id)
            if existing:
                logger.info(f"Student {student_id} already exists, updating...")
                updated_count += 1
                # Update existing student
                existing.grade_level = grade_level
                existing.vocabulary_list = generate_vocabulary_entries(vocab_size, grade_level)
                existing.calculate_proficiency_score()
                # Adjust to target range
                target_score = random.uniform(proficiency_range[0], proficiency_range[1])
                existing.proficiency_score = (existing.proficiency_score * 0.7) + (target_score * 0.3)
                existing.proficiency_score = max(0.0, min(100.0, existing.proficiency_score))
                existing.last_updated = datetime.now(timezone.utc)
                # Update metadata with class information
                if not hasattr(existing, 'metadata') or existing.metadata is None:
                    existing.metadata = {}
                existing.metadata["class"] = class_name
                repo.update(existing)
                continue
        except Exception:
            # Student doesn't exist, create new one
            pass
        
        # Generate vocabulary entries
        vocabulary = generate_vocabulary_entries(vocab_size, grade_level)
        
        # Create student profile
        now = datetime.now(timezone.utc)
        student = StudentProfile(
            student_id=student_id,
            grade_level=grade_level,
            vocabulary_list=vocabulary,
            proficiency_score=0.0,  # Will be calculated
            created_at=now,
            last_updated=now,
            metadata={"class": class_name}  # Store class in metadata
        )
        
        # Calculate proficiency score using the model's method
        student.calculate_proficiency_score()
        
        # Adjust proficiency score to be within the specified range
        # The calculated score is a baseline, we'll adjust it
        target_score = random.uniform(proficiency_range[0], proficiency_range[1])
        # Blend calculated score with target (70% calculated, 30% target for realism)
        student.proficiency_score = (student.proficiency_score * 0.7) + (target_score * 0.3)
        student.proficiency_score = max(0.0, min(100.0, student.proficiency_score))
        
        # Save to database
        repo.create(student)
        created_count += 1
        logger.info(f"Created student {student_id} (Grade {grade_level}, {class_name}, {vocab_size} words, {student.proficiency_score:.1f} proficiency)")
    
    logger.info(f"Seeding complete: {created_count} created, {updated_count} updated, {len(MOCK_STUDENTS)} total students")
    logger.info(f"Students distributed: 7A-ELA: 6, 7B-ELA: 6, 8A-ELA: 6")


if __name__ == "__main__":
    try:
        seed_students()
        print("✅ Mock student data seeding completed successfully")
    except Exception as e:
        logger.error(f"Failed to seed mock student data: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        sys.exit(1)

