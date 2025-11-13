"""Prompt templates for vocabulary recommendation generation.

This module contains prompt templates for generating pedagogically sound
vocabulary recommendations with definitions, examples, and learning tips.
"""

from typing import Dict, List

# System prompt for recommendation generation
RECOMMENDATION_SYSTEM_PROMPT = """You are an expert middle school vocabulary instructor specializing in creating pedagogically sound vocabulary recommendations for students in grades 6-8.

Your task is to transform vocabulary gap words into comprehensive, age-appropriate learning recommendations that teachers can use to help students expand their vocabulary.

PEDAGOGICAL PRINCIPLES:
1. **Age-Appropriate Definitions**: Use clear, simple language that middle school students can understand
2. **Contextual Examples**: Provide 2-3 example sentences showing real-world usage
3. **Progressive Difficulty**: Order words from easiest to hardest for optimal learning
4. **Practical Tips**: Include usage tips that help students understand when and how to use the word
5. **Word Families**: Show related words to help students build connections

OUTPUT REQUIREMENTS:
For each recommended word, provide:
- Clear, age-appropriate definition (1-2 sentences max)
- 2-3 example sentences showing the word in context
- Difficulty score (0.0-1.0 scale, where 0.0=easy, 1.0=hard)
- Pedagogical rationale explaining why this word is important
- Usage tips for students (how to use the word correctly)
- Word family (related words, if applicable)

OUTPUT FORMAT:
Return ONLY valid JSON, no other text. Use this exact structure:
{
  "recommendations": [
    {
      "word": "analyze",
      "definition": "examine in detail to understand something better",
      "difficulty_score": 0.5,
      "rationale": "High-frequency academic word used across all subjects. Essential for critical thinking skills.",
      "example_sentences": [
        "Scientists analyze data to find patterns.",
        "Let's analyze the author's argument in this essay.",
        "We need to analyze the results before making a decision."
      ],
      "usage_tips": "Use 'analyze' when you're examining something carefully to understand it better. Common in science, math, and English classes.",
      "word_family": ["analysis", "analytical", "analyzer"]
    }
  ],
  "difficulty_progression": "gradual",
  "estimated_learning_time": "2-3 weeks"
}

IMPORTANT:
- Return ONLY the JSON object, no markdown formatting, no code blocks
- Ensure all words are lowercase and lemmatized
- Difficulty scores should reflect the gap analysis difficulty (convert from 1-10 scale to 0.0-1.0)
- Order recommendations by difficulty (easiest first)
- Definitions must be age-appropriate for middle school students
- Example sentences should be relevant to middle school contexts
- Include 10-15 recommendations (or fewer if fewer gap words provided)
"""


def build_recommendation_prompt(
    student_id: str,
    grade_level: int,
    gap_words: List[Dict],
) -> List[Dict[str, str]]:
    """Build messages for recommendation generation API call.

    Args:
        student_id: Anonymous student identifier
        grade_level: Student's grade level (6-8)
        gap_words: List of gap words identified for the student

    Returns:
        List of message dictionaries for OpenAI API
    """
    # Prepare gap words summary
    gap_words_summary = []
    for gap in gap_words:
        gap_words_summary.append(
            {
                "word": gap.get("word", ""),
                "rationale": gap.get("rationale", ""),
                "difficulty_score": gap.get("difficulty_score", 5),
                "cc_grade_level": gap.get("cc_grade_level", grade_level),
                "subject_areas": gap.get("subject_areas", []),
            }
        )

    # Build user prompt
    user_prompt = f"""Student: {student_id}
Grade Level: {grade_level}

Vocabulary Gap Analysis Results:
I've identified {len(gap_words_summary)} words that are appropriate for this student's Zone of Proximal Development (ZPD).

Gap Words:
{_format_gap_words_for_prompt(gap_words_summary)}

Task: Create comprehensive vocabulary recommendations for these {len(gap_words_summary)} words.

For each word, provide:
1. Clear, age-appropriate definition (suitable for grade {grade_level} students)
2. 2-3 example sentences showing the word used in middle school contexts
3. Difficulty score (convert from 1-10 scale to 0.0-1.0 scale)
4. Pedagogical rationale explaining why this word is important
5. Usage tips to help students understand when and how to use the word
6. Word family (related words, if applicable)

Order the recommendations by difficulty (easiest first) to support progressive learning.

Return the recommendations in JSON format as specified."""

    return [
        {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _format_gap_words_for_prompt(gap_words: List[Dict]) -> str:
    """Format gap words for inclusion in prompt.

    Args:
        gap_words: List of gap word dictionaries

    Returns:
        Formatted string representation
    """
    formatted = []
    for i, gap in enumerate(gap_words, 1):
        word = gap.get("word", "")
        rationale = gap.get("rationale", "")
        difficulty = gap.get("difficulty_score", 5)
        grade = gap.get("cc_grade_level", "")
        subjects = ", ".join(gap.get("subject_areas", []))

        formatted.append(
            f"{i}. {word} (Difficulty: {difficulty}/10, Grade: {grade}, Subjects: {subjects})\n   Rationale: {rationale}"
        )

    return "\n\n".join(formatted)

