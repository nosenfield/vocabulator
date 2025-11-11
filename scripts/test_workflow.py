#!/usr/bin/env python3
"""
End-to-End Workflow Test for Vocabulator Data Layer

This script tests the complete data layer workflow:
1. Initialize configuration and logging
2. Connect to DynamoDB (LocalStack)
3. Create student profile
4. Add vocabulary entries
5. Create recommendations
6. Query and verify data
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logger import get_logger, set_correlation_id
from src.data.repositories.student_repository import StudentRepository
from src.data.repositories.recommendation_repository import RecommendationRepository
from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.models.recommendation import (
    VocabularyRecommendation,
    RecommendedWord,
    RecommendationStatus,
)

# Initialize logger
logger = get_logger(__name__)


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print(f"{'=' * 80}\n")


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def main():
    """Run the end-to-end workflow test"""
    try:
        # Set correlation ID for this test run
        correlation_id = f"test-workflow-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        set_correlation_id(correlation_id)

        print_header("Vocabulator Data Layer Workflow Test")
        print_info(f"Correlation ID: {correlation_id}")

        # Step 1: Initialize configuration
        print_header("Step 1: Initialize Configuration")
        config = load_config()
        print_info(f"Environment: {config.environment}")
        print_info(f"AWS Region: {config.aws_region}")
        print_info(f"DynamoDB Endpoint: {config.localstack_endpoint_url or 'AWS'}")
        print_info(f"S3 Bucket: {config.s3_bucket_name}")
        print_success("Configuration loaded successfully")

        # Step 2: Initialize repositories (they will create their own DB clients)
        print_header("Step 2: Initialize Repositories")
        student_repo = StudentRepository()
        recommendation_repo = RecommendationRepository()
        print_success("Student and Recommendation repositories initialized")

        # Step 3: Create a test student profile
        print_header("Step 3: Create Test Student Profile")
        student_id = "STU-2024-TEST-001"

        # Check if student already exists
        existing_student = student_repo.get(student_id)
        if existing_student:
            print_info(f"Student {student_id} already exists, deleting...")
            student_repo.delete(student_id, existing_student.profile_version)

        student_profile = StudentProfile(
            student_id=student_id,
            grade_level=7,
            vocabulary_list=[],
            proficiency_score=0.0,
        )

        saved_student = student_repo.create(student_profile)
        print_success(f"Created student profile: {saved_student.student_id}")
        print_info(f"  Grade Level: {saved_student.grade_level}")
        print_info(f"  Profile Version: {saved_student.profile_version}")
        print_info(f"  Vocabulary Size: {len(saved_student.vocabulary_list)}")

        # Step 4: Add vocabulary entries
        print_header("Step 4: Add Vocabulary Entries")

        sample_words = [
            {
                "word": "analyze",
                "context": "Students were asked to analyze the historical document for bias.",
            },
            {
                "word": "hypothesis",
                "context": "The scientist formed a hypothesis about the experiment.",
            },
            {
                "word": "synthesis",
                "context": "The essay required a synthesis of multiple sources.",
            },
            {
                "word": "perspective",
                "context": "Consider the author's perspective when reading.",
            },
            {
                "word": "inference",
                "context": "Make an inference based on the evidence provided.",
            },
        ]

        for word_data in sample_words:
            entry = VocabularyEntry(
                word=word_data["word"],
                first_seen=datetime.now(timezone.utc),
                contexts=[word_data["context"]],
            )
            student_profile = student_repo.add_vocabulary(
                student_id=student_id,
                entry=entry,
            )
            print_success(f"  Added word: '{word_data['word']}'")

        # Get updated student profile
        updated_student = student_repo.get(student_id)
        print_info(f"\nUpdated vocabulary size: {len(updated_student.vocabulary_list)}")
        print_info(f"Proficiency score: {updated_student.proficiency_score:.2f}")

        # Step 6: Display vocabulary entries
        print_header("Step 6: Display Vocabulary Entries")
        for entry in updated_student.vocabulary_list:
            print(f"  📖 {entry.word}")
            print(f"     Usage count: {entry.usage_count}")
            print(f"     First seen: {entry.first_seen}")
            print(f"     Contexts: {len(entry.contexts)}")
            print()

        # Step 7: Create vocabulary recommendations
        print_header("Step 7: Create Vocabulary Recommendations")

        recommended_words = [
            RecommendedWord(
                word="empirical",
                definition="Based on observation or experience rather than theory",
                grade_level=8,
                difficulty_score=0.75,  # 0-1 scale (0.75 = moderately challenging)
                rationale="Builds on 'analyze' and 'hypothesis' - important for scientific literacy",
                example_sentences=[
                    "The study provided empirical evidence for the theory.",
                    "Scientists rely on empirical data rather than assumptions.",
                ],
            ),
            RecommendedWord(
                word="juxtapose",
                definition="To place side by side for comparison",
                grade_level=8,
                difficulty_score=0.70,  # 0-1 scale
                rationale="Enhances analytical writing skills, complements 'perspective'",
                example_sentences=[
                    "The essay juxtaposes two contrasting viewpoints.",
                    "Juxtapose the authors' arguments to find similarities.",
                ],
            ),
            RecommendedWord(
                word="methodology",
                definition="A system of methods used in a particular area of study",
                grade_level=8,
                difficulty_score=0.78,  # 0-1 scale
                rationale="Critical academic vocabulary for describing research approaches",
                example_sentences=[
                    "The researchers explained their methodology in detail.",
                    "Understanding the methodology helps evaluate the findings.",
                ],
            ),
        ]

        recommendation = VocabularyRecommendation(
            student_id=student_id,
            recommendation_date=datetime.now(timezone.utc).isoformat(),
            words=recommended_words,
            status=RecommendationStatus.PENDING,
            generated_by="workflow-test-script",
        )

        saved_recommendation = recommendation_repo.create(recommendation)
        print_success(f"Created recommendation for {student_id}")
        print_info(f"  Date: {saved_recommendation.recommendation_date}")
        print_info(f"  Status: {saved_recommendation.status}")
        print_info(f"  Word count: {len(saved_recommendation.words)}")

        # Step 8: Display recommendations
        print_header("Step 8: Display Recommended Words")
        for word in saved_recommendation.words:
            print(f"  💡 {word.word.upper()} (Grade {word.grade_level}, Difficulty: {word.difficulty_score:.2f}/1.0)")
            print(f"     Definition: {word.definition}")
            print(f"     Rationale: {word.rationale}")
            print(f"     Examples:")
            for example in word.example_sentences:
                print(f"       • {example}")
            print()

        # Step 9: Query recommendations by status
        print_header("Step 9: Query Recommendations by Status")
        pending_recs = recommendation_repo.get_by_status(RecommendationStatus.PENDING)
        print_success(f"Found {len(pending_recs)} pending recommendations")
        for rec in pending_recs:
            print_info(f"  Student: {rec.student_id}, Date: {rec.recommendation_date}")

        # Step 10: Update recommendation status
        print_header("Step 10: Update Recommendation Status")
        updated_rec = recommendation_repo.update_status(
            student_id=student_id,
            recommendation_date=saved_recommendation.recommendation_date,
            status=RecommendationStatus.ASSIGNED,
        )
        print_success(f"Updated recommendation status to: {updated_rec.status}")

        # Step 11: Query by grade level
        print_header("Step 11: Query Students by Grade Level")
        grade_7_students = student_repo.list_by_grade_level(7)
        print_success(f"Found {len(grade_7_students)} grade 7 students")
        for student in grade_7_students:
            print_info(f"  {student.student_id} - Proficiency: {student.proficiency_score:.2f}")

        # Final summary
        print_header("✅ Workflow Test Complete")
        print_success("All data layer components working correctly!")
        print_info("\nTest Summary:")
        print_info(f"  ✓ Configuration loaded")
        print_info(f"  ✓ DynamoDB client initialized")
        print_info(f"  ✓ Student profile created and updated")
        print_info(f"  ✓ {len(sample_words)} vocabulary words added")
        print_info(f"  ✓ {len(recommended_words)} word recommendations created")
        print_info(f"  ✓ Status updates working")
        print_info(f"  ✓ Grade level queries working")

        print("\n" + "=" * 80)
        print("  🎉 Data Layer is ready for Phase 2 (AI/ML Layer)!")
        print("=" * 80 + "\n")

        return 0

    except Exception as e:
        print_error(f"Workflow test failed: {str(e)}")
        logger.exception("Workflow test failed", exc_info=e)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
