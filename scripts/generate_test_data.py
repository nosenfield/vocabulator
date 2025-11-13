#!/usr/bin/env python3
"""Generate test data for Vocabulator MVP.

This script generates:
- 50+ mock student transcripts (varying quality)
- 20+ mock writing samples
- Mock student profiles across grades 6-8

Generated files are saved to tests/fixtures/ for use in testing and development.
"""

import json
import random
import sys
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.utils.logger import get_logger

logger = get_logger("scripts.generate_test_data")

# Grade-appropriate vocabulary and topics
GRADE_6_TOPICS = [
    "science experiments", "ancient civilizations", "ecosystems", 
    "fractions", "geometry", "reading comprehension", "creative writing"
]

GRADE_7_TOPICS = [
    "cell biology", "world history", "algebra", "literary analysis",
    "research projects", "debate", "scientific method"
]

GRADE_8_TOPICS = [
    "chemistry", "American history", "pre-algebra", "essay writing",
    "critical thinking", "lab reports", "presentations"
]

# Sample vocabulary words by grade level
GRADE_6_WORDS = [
    "photosynthesis", "ecosystem", "civilization", "fraction", "geometry",
    "comprehension", "creative", "experiment", "observe", "analyze",
    "hypothesis", "evidence", "conclusion", "ancient", "pyramid"
]

GRADE_7_WORDS = [
    "cell", "membrane", "mitochondria", "democracy", "republic",
    "equation", "variable", "literary", "metaphor", "simile",
    "research", "citation", "debate", "argument", "evidence"
]

GRADE_8_WORDS = [
    "molecule", "compound", "reaction", "constitution", "amendment",
    "algebraic", "polynomial", "thesis", "synthesis", "analysis",
    "critical", "evaluate", "hypothesis", "methodology", "conclusion"
]

# Transcript templates with varying quality
TRANSCRIPT_TEMPLATES = {
    "high_quality": [
        "Today in {subject} class, we learned about {topic}. {topic} is important because {reason}. The teacher explained that {concept} helps us understand {connection}.",
        "During the {activity}, we observed how {phenomenon} affects {outcome}. I noticed that {observation}. The data we collected showed {finding}.",
        "In {subject} class, we analyzed {data}. We calculated {calculation} and compared {comparison}. The results were {result}, which means {interpretation}.",
        "I think {subject} is {opinion} because {reason}. The {method} allows us to {action} and {outcome}."
    ],
    "medium_quality": [
        "We learned about {topic} today. It was {adjective}. The teacher said {statement}.",
        "We did an experiment with {materials}. It was {result}.",
        "I think {topic} is {opinion}."
    ],
    "low_quality": [
        "Today we learned stuff. It was okay.",
        "We did something in class.",
        "I don't remember what we did."
    ]
}

# Writing sample templates
WRITING_TEMPLATES = {
    "essay": [
        "In my opinion, {topic} is {opinion} because {reason1}, {reason2}, and {reason3}. "
        "For example, {example}. This shows that {conclusion}. "
        "Therefore, I believe that {thesis}."
    ],
    "response": [
        "The {text_type} {title} is about {topic}. The main character {action}. "
        "I think this is {opinion} because {reason}. The author uses {technique} to {purpose}."
    ],
    "report": [
        "For this project, I researched {topic}. I found that {finding1} and {finding2}. "
        "The most interesting thing I learned was {insight}. This matters because {significance}."
    ]
}


def generate_transcript(grade_level: int, quality: str = "high_quality") -> str:
    """Generate a mock student transcript.
    
    Args:
        grade_level: Grade level (6-8)
        quality: Quality level ("high_quality", "medium_quality", "low_quality")
        
    Returns:
        Generated transcript text
    """
    templates = TRANSCRIPT_TEMPLATES.get(quality, TRANSCRIPT_TEMPLATES["medium_quality"])
    
    if grade_level == 6:
        topics = GRADE_6_TOPICS
        words = GRADE_6_WORDS
    elif grade_level == 7:
        topics = GRADE_7_TOPICS
        words = GRADE_7_WORDS
    else:  # grade 8
        topics = GRADE_8_TOPICS
        words = GRADE_8_WORDS
    
    # Select random topic and words
    topic = random.choice(topics)
    subject = topic.split()[0] if topic else "science"
    concept = random.choice(words)
    
    # Generate sentences
    sentences = []
    for template in templates:
        sentence = template.format(
            subject=subject,
            topic=topic,
            reason=f"it helps us understand {concept}",
            concept=concept,
            connection="how things work",
            activity="experiment",
            phenomenon=concept,
            outcome="successful results",
            observation=f"{concept} changed over time",
            finding="a clear pattern",
            data="the results",
            calculation="the average",
            comparison="different conditions",
            result="significant",
            interpretation="our hypothesis was correct",
            opinion="interesting",
            method="scientific method",
            action="investigate questions",
            adjective="interesting",
            statement=f"{concept} is important",
            materials="various materials"
        )
        sentences.append(sentence)
    
    return " ".join(sentences)


def generate_writing_sample(grade_level: int, sample_type: str = "essay") -> str:
    """Generate a mock writing sample.
    
    Args:
        grade_level: Grade level (6-8)
        sample_type: Type of writing ("essay", "response", "report")
        
    Returns:
        Generated writing sample text
    """
    if grade_level == 6:
        topics = ["friendship", "adventure", "nature", "school", "family"]
        words = GRADE_6_WORDS
    elif grade_level == 7:
        topics = ["leadership", "challenges", "discovery", "history", "science"]
        words = GRADE_7_WORDS
    else:  # grade 8
        topics = ["change", "responsibility", "innovation", "society", "future"]
        words = GRADE_8_WORDS
    
    topic = random.choice(topics)
    template = WRITING_TEMPLATES.get(sample_type, WRITING_TEMPLATES["essay"])[0]
    
    # Format parameters based on template type
    if sample_type == "essay":
        format_params = {
            "topic": topic,
            "opinion": "important",
            "reason1": f"it affects {random.choice(words)}",
            "reason2": "it helps us grow",
            "reason3": "it teaches us lessons",
            "example": f"when I learned about {topic}, I realized {random.choice(words)}",
            "conclusion": "this is valuable",
            "thesis": f"{topic} matters"
        }
    elif sample_type == "response":
        format_params = {
            "text_type": "story",
            "title": f"The {topic.title()}",
            "topic": topic,
            "action": f"discovers {random.choice(words)}",
            "opinion": "interesting",
            "reason": f"it shows how {random.choice(words)} affects people",
            "technique": "descriptive language",
            "purpose": "create vivid images"
        }
    else:  # report
        format_params = {
            "topic": topic,
            "finding1": f"{topic} involves {random.choice(words)}",
            "finding2": f"it relates to {random.choice(words)}",
            "insight": f"{topic} connects to {random.choice(words)}",
            "significance": "it helps us understand the world"
        }
    
    writing = template.format(**format_params)
    
    return writing


# Common first names for middle school students
FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn",
    "Sage", "River", "Phoenix", "Blake", "Cameron", "Dakota", "Emery", "Finley",
    "Hayden", "Jamie", "Sam", "Chris", "Drew", "Lee", "Pat", "Terry"
]

# Last name initials (A-Z)
LAST_INITIALS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def generate_student_profile(
    student_id: str,
    grade_level: int,
    vocabulary_size: int = None
) -> StudentProfile:
    """Generate a mock student profile.
    
    Args:
        student_id: Student identifier
        grade_level: Grade level (6-8)
        vocabulary_size: Number of vocabulary words (default: random 50-200)
        
    Returns:
        Generated StudentProfile
    """
    if vocabulary_size is None:
        vocabulary_size = random.randint(50, 200)
    
    # Generate random name
    first_name = random.choice(FIRST_NAMES)
    last_initial = random.choice(LAST_INITIALS)
    
    # Select appropriate words for grade level
    if grade_level == 6:
        word_pool = GRADE_6_WORDS
    elif grade_level == 7:
        word_pool = GRADE_7_WORDS
    else:  # grade 8
        word_pool = GRADE_8_WORDS
    
    # Generate vocabulary entries
    vocabulary_list = []
    base_time = datetime.now(timezone.utc) - timedelta(days=90)
    
    # If vocabulary_size exceeds word pool, allow duplicates with different contexts
    max_unique_words = min(vocabulary_size, len(word_pool))
    unique_words = random.sample(word_pool, max_unique_words)
    
    for i in range(vocabulary_size):
        if i < len(unique_words):
            word = unique_words[i]
        else:
            # Allow duplicates after exhausting unique words
            word = random.choice(word_pool)
        
        first_seen = base_time + timedelta(days=random.randint(0, 90))
        usage_count = random.randint(1, 10)
        contexts = random.sample(
            ["science", "math", "english", "history", "social studies"],
            k=random.randint(1, 3)
        )
        
        entry = VocabularyEntry(
            word=word,
            first_seen=first_seen,
            usage_count=usage_count,
            contexts=contexts
        )
        vocabulary_list.append(entry)
    
    profile = StudentProfile(
        student_id=student_id,
        first_name=first_name,
        last_initial=last_initial,
        grade_level=grade_level,
        vocabulary_list=vocabulary_list
    )
    
    # Calculate proficiency score
    profile.calculate_proficiency_score()
    
    return profile


def generate_all_test_data(output_dir: Path) -> None:
    """Generate all test data files.
    
    Args:
        output_dir: Directory to save test data files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    transcripts_dir = output_dir / "sample_transcripts"
    writing_dir = output_dir / "sample_writing"
    profiles_dir = output_dir / "student_profiles"
    
    transcripts_dir.mkdir(exist_ok=True)
    writing_dir.mkdir(exist_ok=True)
    profiles_dir.mkdir(exist_ok=True)
    
    # Generate 50+ transcripts (varying quality and grade levels)
    logger.info("Generating student transcripts...")
    transcript_count = 0
    for grade in [6, 7, 8]:
        for quality_idx, quality in enumerate(["high_quality", "medium_quality", "low_quality"]):
            for i in range(6):  # 6 per quality level per grade = 54 total
                transcript_count += 1
                # Make student ID unique by including quality index
                student_id = f"STU-{grade:03d}-{quality_idx+1}-{i+1:03d}"
                transcript = generate_transcript(grade, quality)
                
                transcript_file = transcripts_dir / f"{student_id}.txt"
                transcript_file.write_text(transcript)
    
    logger.info(f"Generated {transcript_count} transcripts")
    
    # Generate 20+ writing samples
    logger.info("Generating writing samples...")
    writing_count = 0
    for grade in [6, 7, 8]:
        for type_idx, sample_type in enumerate(["essay", "response", "report"]):
            for i in range(3):  # 3 per type per grade = 27 total
                writing_count += 1
                # Make student ID unique by including type index
                student_id = f"STU-{grade:03d}-WR-{type_idx+1}-{i+1:03d}"
                writing = generate_writing_sample(grade, sample_type)
                
                writing_file = writing_dir / f"{student_id}.txt"
                writing_file.write_text(writing)
    
    logger.info(f"Generated {writing_count} writing samples")
    
    # Generate student profiles
    logger.info("Generating student profiles...")
    profiles = []
    for grade in [6, 7, 8]:
        for i in range(10):  # 10 profiles per grade = 30 total
            student_id = f"STU-{grade:03d}-{i+1:03d}"
            profile = generate_student_profile(student_id, grade)
            profiles.append(profile)
            
            # Save individual profile as JSON
            profile_file = profiles_dir / f"{student_id}.json"
            profile_dict = profile.to_dict()
            # Convert datetime objects to ISO strings for JSON serialization
            profile_dict["created_at"] = profile.created_at.isoformat()
            profile_dict["last_updated"] = profile.last_updated.isoformat()
            # Convert Decimal to float for proficiency_score
            if isinstance(profile_dict["proficiency_score"], Decimal):
                profile_dict["proficiency_score"] = float(profile_dict["proficiency_score"])
            # Convert datetime strings in vocabulary_list (already done by to_dict())
            for entry in profile_dict["vocabulary_list"]:
                if isinstance(entry["first_seen"], datetime):
                    entry["first_seen"] = entry["first_seen"].isoformat()
            
            profile_file.write_text(json.dumps(profile_dict, indent=2, default=str))
    
    logger.info(f"Generated {len(profiles)} student profiles")
    
    # Save all profiles as a single JSON file for seeding
    all_profiles_file = output_dir / "all_student_profiles.json"
    all_profiles_data = []
    for profile in profiles:
        profile_dict = profile.to_dict()
        # Convert datetime objects to ISO strings
        profile_dict["created_at"] = profile.created_at.isoformat()
        profile_dict["last_updated"] = profile.last_updated.isoformat()
        # Convert Decimal to float for proficiency_score
        if isinstance(profile_dict["proficiency_score"], Decimal):
            profile_dict["proficiency_score"] = float(profile_dict["proficiency_score"])
        # Convert datetime strings in vocabulary_list (already done by to_dict())
        for entry in profile_dict["vocabulary_list"]:
            if isinstance(entry["first_seen"], datetime):
                entry["first_seen"] = entry["first_seen"].isoformat()
        all_profiles_data.append(profile_dict)
    
    all_profiles_file.write_text(json.dumps(all_profiles_data, indent=2, default=str))
    
    logger.info(f"Test data generation complete!")
    logger.info(f"  - Transcripts: {transcript_count} files in {transcripts_dir}")
    logger.info(f"  - Writing samples: {writing_count} files in {writing_dir}")
    logger.info(f"  - Student profiles: {len(profiles)} files in {profiles_dir}")
    logger.info(f"  - Combined profiles: {all_profiles_file}")


def main():
    """Main entry point for test data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for Vocabulator MVP")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/fixtures"),
        help="Output directory for test data (default: tests/fixtures)",
    )
    
    args = parser.parse_args()
    
    try:
        generate_all_test_data(args.output_dir)
        logger.info("Test data generation completed successfully")
    except Exception as e:
        logger.error(f"Failed to generate test data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

