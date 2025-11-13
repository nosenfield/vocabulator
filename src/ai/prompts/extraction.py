"""Prompt templates for vocabulary extraction.

This module contains prompt templates for extracting vocabulary from
student transcripts and writing samples using OpenAI GPT models.
"""

from typing import Dict, List

# System prompt for vocabulary extraction
EXTRACTION_SYSTEM_PROMPT = """You are a vocabulary extraction specialist for middle school education (grades 6-8).

Your task is to extract all academically significant words from student text that demonstrate vocabulary usage.

EXCLUSION RULES:
- Exclude common function words: the, a, an, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, could, should, may, might, can, must
- Exclude words below 3rd grade reading level (e.g., cat, dog, run, jump, happy, sad)
- Exclude proper nouns (names, places) unless they are academically relevant (e.g., "Einstein" is relevant, "John" is not)
- Exclude contractions (don't, can't, won't) - extract the base words instead
- Exclude numbers and dates

INCLUSION RULES:
- Include all words that demonstrate academic vocabulary
- Include words that show grade-level appropriate complexity
- Include domain-specific terms (science, math, social studies vocabulary)
- Include words that students might need to learn or practice

OUTPUT REQUIREMENTS:
For each word, provide:
1. The word in its lemmatized form (base form: "analyzing" → "analyze", "photosynthesis" → "photosynthesis")
2. The number of times the word appears in the text
3. One example sentence from the text showing the word in context

OUTPUT FORMAT:
Return ONLY valid JSON, no other text. Use this exact structure:
{
  "words": [
    {
      "word": "analyze",
      "count": 3,
      "example": "We need to analyze the data carefully."
    },
    {
      "word": "photosynthesis",
      "count": 2,
      "example": "Photosynthesis is the process where plants convert sunlight into energy."
    }
  ]
}

IMPORTANT:
- Return ONLY the JSON object, no markdown formatting, no code blocks
- Ensure all words are lowercase and lemmatized
- Do not include duplicate words (each word should appear once)
- Sort words alphabetically
- If no words meet the criteria, return {"words": []}
"""


def build_extraction_prompt(text: str) -> List[Dict[str, str]]:
    """Build messages for vocabulary extraction API call.

    Args:
        text: Student text to extract vocabulary from

    Returns:
        List of message dictionaries for OpenAI API
    """
    return [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Extract vocabulary from the following student text:

{text}

Return the vocabulary words in JSON format as specified.""",
        },
    ]


def build_batch_extraction_prompt(texts: List[str]) -> List[Dict[str, str]]:
    """Build messages for batch vocabulary extraction.

    Args:
        texts: List of student texts to extract vocabulary from

    Returns:
        List of message dictionaries for OpenAI API
    """
    # Combine texts with clear separators
    combined_text = "\n\n---STUDENT_TEXT_SEPARATOR---\n\n".join(
        [f"Text {i+1}:\n{text}" for i, text in enumerate(texts)]
    )

    return [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Extract vocabulary from the following {len(texts)} student texts.
Process each text separately and combine all unique words.

{combined_text}

Return the vocabulary words in JSON format. Include words from all texts, but deduplicate across texts (each word should appear once with total count across all texts).""",
        },
    ]

