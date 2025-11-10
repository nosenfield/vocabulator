# Phase 2: AI/ML Layer

**Total Estimated Time:** 21-27 hours (4-5 days)
**Priority:** 🔴 P0 (All tasks)
**Dependencies:** Phase 0 (0.4), Phase 1 (1.5 for task 2.3)

---

## Overview

Phase 2 implements the AI/ML integration layer, including OpenAI API client, prompt engineering for vocabulary extraction, gap analysis, and personalized recommendations. This is the core intelligence of the system.

**Key Deliverables:**
- OpenAI API client with retry logic and cost tracking
- Vocabulary extraction from transcripts
- Gap analysis using Zone of Proximal Development (ZPD)
- Personalized word recommendations

**Cross-References:**
- Uses logging from [Phase 0](phase-0-project-setup.md) (task 0.4)
- Uses Common Core vocabulary from [Phase 1](phase-1-data-layer.md) (task 1.5)
- Required for [Phase 3: Processing Layer](phase-3-processing-layer.md)

---

## 2.1 OpenAI Client Wrapper

**Priority:** 🔴 P0 🧪
**Estimated Time:** 4-5 hours
**Dependencies:** Phase 0 (0.4)

### Tasks
- [ ] 🧪 Write tests for OpenAI client (mock API responses)
- [ ] Implement `src/ai/openai_client.py` wrapper
- [ ] Add retry logic with exponential backoff
- [ ] Implement rate limit handling
- [ ] Add request/response logging (sanitized)
- [ ] Create cost tracking per request
- [ ] Support both GPT-4o and GPT-4o-mini models
- [ ] Add timeout configuration

### Acceptance Criteria
- Tests use mocked OpenAI responses
- Retry logic handles transient failures
- Rate limits trigger backoff
- Cost tracking logs token usage
- Both models callable via unified interface

### Files Created
- `src/ai/openai_client.py`
- `src/ai/cost_tracker.py`
- `tests/unit/test_openai_client.py`
- `tests/mocks/mock_openai.py`

### Cost Tracking Requirements
Track per request:
- Model used (gpt-4o-mini vs gpt-4o)
- Prompt tokens
- Completion tokens
- Estimated cost ($)
- Timestamp
- Operation type (extraction, analysis, recommendation)

### Related Documentation
- See [best-practices.md](../best-practices.md) - OpenAI API Integration section
- See [architecture.md](../architecture.md) - AI/ML Layer section
- See [required-reading.md](../required-reading.md) - OpenAI API section

---

## 2.2 Vocabulary Extraction Prompts & Logic

**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 2.1

### Tasks
- [ ] 🧪 Write tests for vocabulary extraction (sample inputs/outputs)
- [ ] Design extraction prompt template
- [ ] Implement `src/ai/prompts/extraction.py`
- [ ] Create text preprocessing utilities (chunking, cleaning)
- [ ] Add word deduplication and normalization
- [ ] Implement context capture for each word
- [ ] Add filtering logic (exclude common words, grade-inappropriate)
- [ ] Optimize for GPT-4o-mini usage

### Acceptance Criteria
- Tests verify extraction from sample transcripts
- Extracted words are normalized (lowercase, lemmatized)
- Context sentences captured for each word
- Common stopwords filtered out
- Handles texts up to 10,000 words

### Files Created
- `src/ai/prompts/extraction.py`
- `src/processing/text_analyzer.py`
- `tests/unit/test_vocabulary_extraction.py`
- `tests/fixtures/sample_transcripts/student_001.txt`

### Sample Prompt Template
```python
system_prompt = """
You are a vocabulary extraction specialist for middle school education.

Task: Extract all academically significant words from the student text.

Exclude:
- Common function words (the, a, an, is, are, was, were)
- Words below 3rd grade level
- Proper nouns (names, places) unless academically relevant

For each word, provide:
- The word (lemmatized form)
- Number of times used
- One example sentence showing usage

Output format: JSON
{
  "words": [
    {
      "word": "analyze",
      "count": 3,
      "example": "We need to analyze the data carefully."
    }
  ]
}
"""
```

### Optimization Strategies
- Use GPT-4o-mini (10x cheaper than GPT-4o)
- Chunk long texts into 2000-word segments
- Cache repeated extractions (hash input text)
- Batch multiple short texts in single API call
- Temperature: 0.3 (consistent extraction)

### Related Documentation
- See [best-practices.md](../best-practices.md) - Prompt Engineering section
- See [architecture.md](../architecture.md) - OpenAI API Strategy section
- Required for [Phase 3](phase-3-processing-layer.md) (task 3.1)

---

## 2.3 Vocabulary Gap Analysis Prompts & Logic

**Priority:** 🔴 P0 🧪
**Estimated Time:** 6-8 hours
**Dependencies:** 2.2, Phase 1 (1.5)

### Tasks
- [ ] 🧪 Write tests for gap analysis
- [ ] Design gap analysis prompt template
- [ ] Implement `src/ai/prompts/gap_analysis.py`
- [ ] Create `src/processing/gap_identifier.py`
- [ ] Compare student vocabulary against Common Core standards
- [ ] Implement Zone of Proximal Development (ZPD) logic
- [ ] Score word difficulty relative to student level
- [ ] Identify 10-15 target words per student

### Acceptance Criteria
- Gap analysis correctly identifies missing Common Core words
- Recommended words are slightly above current level
- Difficulty scoring aligns with grade levels
- Tests verify ZPD logic with sample profiles

### Files Created
- `src/ai/prompts/gap_analysis.py`
- `src/processing/gap_identifier.py`
- `tests/unit/test_gap_identifier.py`

### Sample Prompt Template
```python
system_prompt = """
You are a vocabulary assessment expert specializing in Zone of Proximal Development.

Student Profile:
- Grade: {grade}
- Current vocabulary size: {vocab_size}
- Recently used words: {recent_words}

Common Core Standards:
- Expected words for grade {grade}: {cc_words}

Task: Identify 10-15 words that are:
1. Missing from student's current vocabulary
2. Present in Common Core standards
3. Slightly above current level (ZPD)
4. High-utility across subjects

Output: JSON with word, rationale, difficulty_score (1-10)
{
  "gaps": [
    {
      "word": "analyze",
      "rationale": "High-frequency academic word across subjects",
      "difficulty_score": 5,
      "cc_grade_level": 6,
      "subject_areas": ["math", "science", "ela"]
    }
  ]
}
"""
```

### Zone of Proximal Development (ZPD) Logic
```python
def calculate_zpd_difficulty(student_vocab_size: int, grade: int) -> tuple:
    """Calculate appropriate difficulty range for student."""
    # Student at 80th percentile for grade → target 90th percentile
    # Student at 50th percentile for grade → target 60th percentile
    base_difficulty = grade * 2  # Grade 7 → difficulty 14/20
    adjustment = (student_vocab_size - expected_size) / 100

    min_difficulty = base_difficulty + adjustment
    max_difficulty = base_difficulty + adjustment + 2

    return (min_difficulty, max_difficulty)
```

### Related Documentation
- See [required-reading.md](../required-reading.md) - Zone of Proximal Development section
- See [required-reading.md](../required-reading.md) - Vocabulary Development section
- Uses Common Core database from [Phase 1](phase-1-data-layer.md) (task 1.5)
- Required for [Phase 2](phase-2-ai-ml-layer.md) (task 2.4)

---

## 2.4 Word Recommendation Generation

**Priority:** 🔴 P0 🧪
**Estimated Time:** 5-6 hours
**Dependencies:** 2.3

### Tasks
- [ ] 🧪 Write tests for recommendation generation
- [ ] Design recommendation prompt template
- [ ] Implement `src/ai/prompts/recommendation.py`
- [ ] Create `src/processing/recommender.py`
- [ ] Generate pedagogically sound word recommendations
- [ ] Include definitions, example sentences, usage tips
- [ ] Add difficulty progression (easiest to hardest)
- [ ] Format output for teacher consumption

### Acceptance Criteria
- Recommendations include 10-15 words
- Each word has definition and examples
- Words ordered by difficulty
- Output format matches DynamoDB schema

### Files Created
- `src/ai/prompts/recommendation.py`
- `src/processing/recommender.py`
- `tests/unit/test_recommender.py`

### Sample Output Format
```json
{
  "student_id": "STU-001",
  "recommendation_date": "2025-11-10",
  "recommendations": [
    {
      "word": "analyze",
      "definition": "examine in detail to understand",
      "difficulty_score": 5,
      "rationale": "High-frequency academic word across subjects",
      "example_sentences": [
        "Scientists analyze data to find patterns.",
        "Let's analyze the author's argument."
      ],
      "usage_tips": "Use when examining details carefully",
      "word_family": ["analysis", "analytical", "analyzer"]
    }
  ],
  "difficulty_progression": "gradual",
  "estimated_learning_time": "2-3 weeks"
}
```

### Sample Prompt Template
```python
system_prompt = """
You are an expert middle school vocabulary instructor.

Student: {student_id}
Grade: {grade}
Gap Analysis: {gap_words}

Task: Create 10-15 vocabulary recommendations with:
1. Clear, age-appropriate definitions
2. 2-3 example sentences showing usage
3. Difficulty progression (easiest first)
4. Pedagogical rationale for each word
5. Learning tips for students

Output: JSON formatted recommendations
"""
```

### Related Documentation
- See [architecture.md](../architecture.md) - Recommendation Repository section
- Saves to [Phase 1](phase-1-data-layer.md) recommendation repository (task 1.3)
- Used by [Phase 4: API Layer](phase-4-api-layer.md) (task 4.5)
- Used by [Phase 5: Frontend](phase-5-frontend-layer.md) (task 5.1)

---

## Phase 2 Completion Checklist

Before proceeding to Phase 3, verify:

- [ ] All Phase 2 tasks completed (2.1-2.4)
- [ ] All unit tests passing for AI/ML components
- [ ] OpenAI API client functional with mocked responses
- [ ] Vocabulary extraction tested with 10+ sample transcripts
- [ ] Gap analysis produces sensible recommendations
- [ ] Recommendation generation outputs valid JSON
- [ ] Cost tracking implemented and logging token usage
- [ ] Code formatted and linted (black, ruff, mypy pass)
- [ ] Integration test: Extract → Analyze → Recommend pipeline
- [ ] Memory Bank updated with Phase 2 completion

### AI/ML Pipeline Integration Test

Create end-to-end test verifying:
```python
# Step 1: Extract vocabulary from transcript
transcript = load_sample_transcript("student_001.txt")
extracted_words = await vocabulary_extractor.extract(transcript)
assert len(extracted_words) > 10

# Step 2: Identify gaps against Common Core
student_profile = {"student_id": "STU-001", "grade_level": 7}
gaps = await gap_identifier.identify_gaps(extracted_words, student_profile)
assert len(gaps) >= 10

# Step 3: Generate recommendations
recommendations = await recommender.generate(gaps, student_profile)
assert len(recommendations) == len(gaps)
assert all(rec["definition"] for rec in recommendations)

# Verify cost tracking
assert cost_tracker.total_cost > 0
assert cost_tracker.operations == 3  # extract, analyze, recommend
```

### Cost Monitoring

Track Phase 2 API costs:
- Extraction (GPT-4o-mini): ~$0.15 per 1M tokens
- Gap Analysis (GPT-4o): ~$2.50 per 1M tokens
- Recommendations (GPT-4o): ~$2.50 per 1M tokens
- Target: < $0.10 per student per analysis

### Next Phase
**Proceed to:** [Phase 3: Processing Layer](phase-3-processing-layer.md)

---

**Last Updated:** 2025-11-10
**Related Files:**
- [Phase 0: Project Setup](phase-0-project-setup.md) (prerequisite)
- [Phase 1: Data Layer](phase-1-data-layer.md) (prerequisite)
- [Phase 3: Processing Layer](phase-3-processing-layer.md) (next phase)
- [Phase 4: API Layer](phase-4-api-layer.md) (consumer)
- [Phase 5: Frontend Layer](phase-5-frontend-layer.md) (consumer)
- [architecture.md](../architecture.md)
- [best-practices.md](../best-practices.md)
- [required-reading.md](../required-reading.md)
