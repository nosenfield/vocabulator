"""HTML report template rendering.

This module provides functions to render HTML reports from Jinja2 templates
for student vocabulary profiles and recommendations.
"""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.data.models.student_profile import StudentProfile
from src.data.models.recommendation import VocabularyRecommendation


# Get the templates directory path
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_profile_report(profile: StudentProfile) -> str:
    """Render student profile report HTML.
    
    Args:
        profile: StudentProfile instance to render
        
    Returns:
        Rendered HTML string
        
    Raises:
        TemplateNotFound: If template file is missing
    """
    template = env.get_template("profile_report.html")
    
    # Prepare template context
    # Convert vocabulary entries to dict format for template
    vocabulary_list = [
        {
            "word": entry.word,
            "first_seen": entry.first_seen.strftime("%Y-%m-%d"),
            "usage_count": entry.usage_count,
            "contexts": ", ".join(entry.contexts) if entry.contexts else "N/A",
        }
        for entry in profile.vocabulary_list
    ]
    
    # Recent words (keep as VocabularyEntry objects for template access)
    recent_words = sorted(
        profile.vocabulary_list,
        key=lambda x: x.first_seen,
        reverse=True,
    )[:10]  # Last 10 words
    
    context = {
        "student_id": profile.student_id,
        "grade_level": profile.grade_level,
        "proficiency_score": round(profile.proficiency_score, 1),
        "vocabulary_size": len(profile.vocabulary_list),
        "vocabulary_list": vocabulary_list,
        "recent_words": recent_words,
        "created_at": profile.created_at.strftime("%Y-%m-%d"),
        "last_updated": profile.last_updated.strftime("%Y-%m-%d"),
    }
    
    return template.render(**context)


def render_recommendations_report(recommendation: VocabularyRecommendation) -> str:
    """Render vocabulary recommendations report HTML.
    
    Args:
        recommendation: VocabularyRecommendation instance to render
        
    Returns:
        Rendered HTML string
        
    Raises:
        TemplateNotFound: If template file is missing
    """
    template = env.get_template("recommendations_report.html")
    
    # Sort words by difficulty (easiest first)
    sorted_words = sorted(
        recommendation.words,
        key=lambda x: x.difficulty_score,
    )
    
    # Prepare template context
    context = {
        "student_id": recommendation.student_id,
        "recommendation_date": recommendation.recommendation_date,
        "status": recommendation.status.value,
        "word_count": len(recommendation.words),
        "words": [
            {
                "word": word.word,
                "definition": word.definition,
                "grade_level": word.grade_level,
                "difficulty_score": round(word.difficulty_score, 2),
                "difficulty_percent": int(word.difficulty_score * 100),
                "rationale": word.rationale,
                "example_sentences": word.example_sentences,
            }
            for word in sorted_words
        ],
        "generated_by": recommendation.generated_by or "N/A",
    }
    
    return template.render(**context)

