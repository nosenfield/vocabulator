"""Prompt templates for vocabulary gap analysis.

This module contains prompt templates for identifying vocabulary gaps
using Zone of Proximal Development (ZPD) principles.
"""

from typing import Dict, List

# System prompt for gap analysis
GAP_ANALYSIS_SYSTEM_PROMPT = """You are a vocabulary assessment expert specializing in Zone of Proximal Development (ZPD) for middle school education (grades 6-8).

Your task is to identify vocabulary gaps - words that students should learn next based on their current level and Common Core standards.

ZPD PRINCIPLE:
The Zone of Proximal Development is the range of difficulty where learning is optimal:
- Too easy: Student already knows the word (no learning)
- Too hard: Word is far beyond current level (frustration, no learning)
- Just right: Word is slightly above current level (optimal challenge, maximum learning)

TASK:
Identify 10-15 words that are:
1. Missing from student's current vocabulary
2. Present in Common Core standards for their grade level
3. Slightly above current level (ZPD - optimal challenge)
4. High-utility across multiple subject areas
5. Appropriate for their grade level (6, 7, or 8)

OUTPUT REQUIREMENTS:
For each gap word, provide:
- The word (lemmatized form)
- Rationale explaining why this word is appropriate for ZPD
- Difficulty score (1-10 scale, where 5 = grade-appropriate, 7-8 = slightly challenging)
- Common Core grade level where word appears
- Subject areas where word is commonly used

OUTPUT FORMAT:
Return ONLY valid JSON, no other text. Use this exact structure:
{
  "gaps": [
    {
      "word": "synthesize",
      "rationale": "High-frequency academic word across subjects. Student knows 'analyze' and 'evaluate', so 'synthesize' is the next logical step in critical thinking vocabulary.",
      "difficulty_score": 7,
      "cc_grade_level": 7,
      "subject_areas": ["science", "ela"]
    }
  ]
}

IMPORTANT:
- Return ONLY the JSON object, no markdown formatting, no code blocks
- Ensure all words are lowercase and lemmatized
- Difficulty scores should reflect ZPD (slightly above current level)
- Do not include words the student already knows
- Prioritize high-utility words used across multiple subjects
- If fewer than 10 appropriate words exist, return what is available (minimum 5)
"""


def build_gap_analysis_prompt(
    student_profile: Dict,
    extracted_words: List[Dict],
    common_core_words: List[Dict],
) -> List[Dict[str, str]]:
    """Build messages for gap analysis API call.

    Args:
        student_profile: Student profile dictionary with grade_level, vocabulary_list, etc.
        extracted_words: List of extracted vocabulary words from student text
        common_core_words: List of Common Core vocabulary words for comparison

    Returns:
        List of message dictionaries for OpenAI API
    """
    # Prepare student vocabulary summary with validation
    vocab_list = student_profile.get("vocabulary_list", [])
    if not isinstance(vocab_list, list):
        vocab_list = []
    
    student_vocab_words = [
        entry.get("word", "")
        for entry in vocab_list
        if isinstance(entry, dict) and "word" in entry
    ]
    
    extracted_word_list = [
        word.get("word", "")
        for word in extracted_words
        if isinstance(word, dict) and "word" in word
    ]

    # Combine and deduplicate
    all_student_words = list(set(student_vocab_words + extracted_word_list))

    # Prepare Common Core words summary with validation
    cc_words_by_grade = {}
    if isinstance(common_core_words, list):
        for word in common_core_words:
            if not isinstance(word, dict):
                continue
            grade = word.get("grade_level", 0)
            if isinstance(grade, int) and grade in [6, 7, 8]:
                if grade not in cc_words_by_grade:
                    cc_words_by_grade[grade] = []
                word_text = word.get("word", "")
                if word_text:
                    cc_words_by_grade[grade].append(word_text)

    grade_level = student_profile.get("grade_level", 7)
    vocab_size = len(all_student_words)

    # Build user prompt
    user_prompt = f"""Student Profile:
- Grade Level: {grade_level}
- Current Vocabulary Size: {vocab_size} unique words
- Recently Used Words: {', '.join(extracted_word_list[:20]) if extracted_word_list else 'None'}
- Known Words (sample): {', '.join(all_student_words[:30]) if all_student_words else 'None'}

Common Core Standards:
- Expected words for grade {grade_level}: {len(cc_words_by_grade.get(grade_level, []))} words
- Sample Common Core words for grade {grade_level}: {', '.join(cc_words_by_grade.get(grade_level, [])[:20]) if cc_words_by_grade.get(grade_level) else 'None'}

Task: Identify 10-15 vocabulary gaps using ZPD principles. Words should be:
1. Missing from student's current vocabulary
2. Present in Common Core standards for grade {grade_level}
3. Slightly above current level (optimal challenge)
4. High-utility across subjects

Return the gap words in JSON format as specified."""

    return [
        {"role": "system", "content": GAP_ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

