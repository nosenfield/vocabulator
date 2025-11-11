#!/usr/bin/env python3
"""Generate Common Core vocabulary corpus files.

This script generates representative vocabulary corpus files for grades 6-8
with common academic vocabulary words. The corpus can be expanded with
additional words from Common Core standards, AWL, and COCA sources.
"""

import json
from pathlib import Path
from typing import List, Dict


def generate_grade_6_corpus() -> List[Dict]:
    """Generate grade 6 vocabulary corpus."""
    words = [
        # Analysis & Evaluation
        {"word": "analyze", "grade_level": 6, "definition": "examine in detail to understand", "subject_areas": ["math", "science", "ela"], "complexity_tier": 2, "word_family": ["analysis", "analytical", "analyzer"]},
        {"word": "evaluate", "grade_level": 6, "definition": "assess the value or quality of something", "subject_areas": ["math", "ela"], "complexity_tier": 2, "word_family": ["evaluation", "evaluative"]},
        {"word": "compare", "grade_level": 6, "definition": "examine similarities and differences", "subject_areas": ["math", "science", "ela"], "complexity_tier": 1, "word_family": ["comparison", "comparable"]},
        {"word": "contrast", "grade_level": 6, "definition": "show differences between things", "subject_areas": ["ela"], "complexity_tier": 1, "word_family": ["contrasting"]},
        {"word": "examine", "grade_level": 6, "definition": "inspect closely", "subject_areas": ["science", "ela"], "complexity_tier": 1, "word_family": ["examination", "examiner"]},
        
        # Communication & Explanation
        {"word": "summarize", "grade_level": 6, "definition": "give a brief statement of main points", "subject_areas": ["ela"], "complexity_tier": 1, "word_family": ["summary", "summarization"]},
        {"word": "explain", "grade_level": 6, "definition": "make clear or understandable", "subject_areas": ["math", "science", "ela"], "complexity_tier": 1, "word_family": ["explanation", "explanatory"]},
        {"word": "describe", "grade_level": 6, "definition": "give a detailed account", "subject_areas": ["ela", "science"], "complexity_tier": 1, "word_family": ["description", "descriptive"]},
        {"word": "demonstrate", "grade_level": 6, "definition": "show or prove by reasoning or evidence", "subject_areas": ["math", "science"], "complexity_tier": 2, "word_family": ["demonstration", "demonstrative"]},
        {"word": "illustrate", "grade_level": 6, "definition": "explain or make clear with examples", "subject_areas": ["ela", "math"], "complexity_tier": 2, "word_family": ["illustration", "illustrative"]},
        
        # Reasoning & Logic
        {"word": "infer", "grade_level": 6, "definition": "deduce or conclude from evidence", "subject_areas": ["ela", "science"], "complexity_tier": 2, "word_family": ["inference", "inferential"]},
        {"word": "conclude", "grade_level": 6, "definition": "arrive at a judgment or decision", "subject_areas": ["ela", "math"], "complexity_tier": 1, "word_family": ["conclusion", "conclusive"]},
        {"word": "reason", "grade_level": 6, "definition": "think logically about something", "subject_areas": ["math", "ela"], "complexity_tier": 1, "word_family": ["reasoning", "reasonable"]},
        {"word": "justify", "grade_level": 6, "definition": "show or prove to be right or reasonable", "subject_areas": ["math", "ela"], "complexity_tier": 2, "word_family": ["justification", "justifiable"]},
        {"word": "support", "grade_level": 6, "definition": "provide evidence or backing for", "subject_areas": ["ela", "science"], "complexity_tier": 1, "word_family": ["supportive", "supporter"]},
        
        # Evidence & Facts
        {"word": "evidence", "grade_level": 6, "definition": "facts or information indicating whether something is true", "subject_areas": ["science", "ela"], "complexity_tier": 1, "word_family": ["evident", "evidently"]},
        {"word": "fact", "grade_level": 6, "definition": "a thing that is known to be true", "subject_areas": ["science", "ela"], "complexity_tier": 1, "word_family": ["factual", "factually"]},
        {"word": "opinion", "grade_level": 6, "definition": "a view or judgment formed about something", "subject_areas": ["ela"], "complexity_tier": 1, "word_family": ["opinionated"]},
        {"word": "claim", "grade_level": 6, "definition": "state or assert that something is the case", "subject_areas": ["ela", "science"], "complexity_tier": 1, "word_family": ["claimant"]},
        {"word": "argument", "grade_level": 6, "definition": "a reason or set of reasons given in support of an idea", "subject_areas": ["ela", "math"], "complexity_tier": 2, "word_family": ["argue", "argumentative"]},
    ]
    
    # Add more words to reach ~500 (for MVP, we'll create a representative sample)
    # In production, this would be expanded with full Common Core vocabulary lists
    additional_words = [
        {"word": "calculate", "grade_level": 6, "definition": "determine mathematically", "subject_areas": ["math"], "complexity_tier": 1, "word_family": ["calculation", "calculator"]},
        {"word": "measure", "grade_level": 6, "definition": "determine the size or amount of something", "subject_areas": ["math", "science"], "complexity_tier": 1, "word_family": ["measurement", "measurable"]},
        {"word": "observe", "grade_level": 6, "definition": "notice or perceive something", "subject_areas": ["science"], "complexity_tier": 1, "word_family": ["observation", "observable"]},
        {"word": "predict", "grade_level": 6, "definition": "say or estimate that something will happen", "subject_areas": ["science", "math"], "complexity_tier": 1, "word_family": ["prediction", "predictable"]},
        {"word": "classify", "grade_level": 6, "definition": "arrange in categories", "subject_areas": ["science", "math"], "complexity_tier": 2, "word_family": ["classification", "classifiable"]},
        {"word": "organize", "grade_level": 6, "definition": "arrange systematically", "subject_areas": ["ela", "science"], "complexity_tier": 1, "word_family": ["organization", "organizational"]},
        {"word": "interpret", "grade_level": 6, "definition": "explain the meaning of", "subject_areas": ["ela", "math"], "complexity_tier": 2, "word_family": ["interpretation", "interpreter"]},
        {"word": "represent", "grade_level": 6, "definition": "stand for or symbolize", "subject_areas": ["math", "ela"], "complexity_tier": 2, "word_family": ["representation", "representative"]},
        {"word": "identify", "grade_level": 6, "definition": "recognize or establish as being a particular person or thing", "subject_areas": ["science", "ela"], "complexity_tier": 1, "word_family": ["identification", "identifiable"]},
        {"word": "define", "grade_level": 6, "definition": "state or describe the nature or scope of", "subject_areas": ["ela", "math"], "complexity_tier": 1, "word_family": ["definition", "definable"]},
    ]
    
    words.extend(additional_words)
    
    # Note: For MVP, this is a representative sample. Production would include
    # 500+ words per grade from Common Core standards, AWL, and COCA sources.
    return words


def generate_grade_7_corpus() -> List[Dict]:
    """Generate grade 7 vocabulary corpus."""
    words = [
        # Advanced Analysis
        {"word": "synthesize", "grade_level": 7, "definition": "combine elements into a coherent whole", "subject_areas": ["science", "ela"], "complexity_tier": 3, "word_family": ["synthesis", "synthetic"]},
        {"word": "critique", "grade_level": 7, "definition": "evaluate in a detailed and analytical way", "subject_areas": ["ela"], "complexity_tier": 3, "word_family": ["criticism", "critical"]},
        {"word": "elaborate", "grade_level": 7, "definition": "develop or present in detail", "subject_areas": ["ela"], "complexity_tier": 2, "word_family": ["elaboration", "elaborative"]},
        {"word": "distinguish", "grade_level": 7, "definition": "recognize or treat as different", "subject_areas": ["ela", "science"], "complexity_tier": 2, "word_family": ["distinction", "distinctive"]},
        {"word": "differentiate", "grade_level": 7, "definition": "recognize or identify as different", "subject_areas": ["math", "science"], "complexity_tier": 2, "word_family": ["differentiation", "differential"]},
        
        # Advanced Reasoning
        {"word": "hypothesize", "grade_level": 7, "definition": "put forward as a hypothesis", "subject_areas": ["science"], "complexity_tier": 3, "word_family": ["hypothesis", "hypothetical"]},
        {"word": "theorize", "grade_level": 7, "definition": "form a theory about", "subject_areas": ["science"], "complexity_tier": 3, "word_family": ["theory", "theoretical"]},
        {"word": "validate", "grade_level": 7, "definition": "check or prove the validity of", "subject_areas": ["science", "math"], "complexity_tier": 2, "word_family": ["validation", "valid"]},
        {"word": "verify", "grade_level": 7, "definition": "make sure or demonstrate that something is true", "subject_areas": ["math", "science"], "complexity_tier": 2, "word_family": ["verification", "verifiable"]},
        {"word": "refute", "grade_level": 7, "definition": "prove to be wrong or false", "subject_areas": ["ela", "science"], "complexity_tier": 3, "word_family": ["refutation"]},
        
        # Advanced Communication
        {"word": "articulate", "grade_level": 7, "definition": "express clearly", "subject_areas": ["ela"], "complexity_tier": 2, "word_family": ["articulation", "articulate"]},
        {"word": "clarify", "grade_level": 7, "definition": "make clear or easier to understand", "subject_areas": ["ela", "math"], "complexity_tier": 1, "word_family": ["clarification", "clear"]},
        {"word": "emphasize", "grade_level": 7, "definition": "give special importance to", "subject_areas": ["ela"], "complexity_tier": 1, "word_family": ["emphasis", "emphatic"]},
        {"word": "paraphrase", "grade_level": 7, "definition": "express the meaning using different words", "subject_areas": ["ela"], "complexity_tier": 2, "word_family": ["paraphrasing"]},
        {"word": "cite", "grade_level": 7, "definition": "quote or refer to as evidence", "subject_areas": ["ela", "science"], "complexity_tier": 2, "word_family": ["citation", "citable"]},
    ]
    
    # Add more representative words
    additional_words = [
        {"word": "investigate", "grade_level": 7, "definition": "carry out research or study", "subject_areas": ["science"], "complexity_tier": 2, "word_family": ["investigation", "investigative"]},
        {"word": "experiment", "grade_level": 7, "definition": "a scientific procedure to test a hypothesis", "subject_areas": ["science"], "complexity_tier": 2, "word_family": ["experimental", "experimentation"]},
        {"word": "formulate", "grade_level": 7, "definition": "create or devise methodically", "subject_areas": ["math", "science"], "complexity_tier": 2, "word_family": ["formulation", "formula"]},
        {"word": "construct", "grade_level": 7, "definition": "build or form by putting together parts", "subject_areas": ["math", "science"], "complexity_tier": 2, "word_family": ["construction", "constructive"]},
        {"word": "deconstruct", "grade_level": 7, "definition": "analyze by breaking down into components", "subject_areas": ["ela"], "complexity_tier": 3, "word_family": ["deconstruction"]},
    ]
    
    words.extend(additional_words)
    return words


def generate_grade_8_corpus() -> List[Dict]:
    """Generate grade 8 vocabulary corpus."""
    words = [
        # Advanced Analysis & Synthesis
        {"word": "scrutinize", "grade_level": 8, "definition": "examine or inspect closely", "subject_areas": ["ela", "science"], "complexity_tier": 3, "word_family": ["scrutiny", "scrutinizing"]},
        {"word": "delineate", "grade_level": 8, "definition": "describe or portray precisely", "subject_areas": ["ela"], "complexity_tier": 3, "word_family": ["delineation"]},
        {"word": "corroborate", "grade_level": 8, "definition": "confirm or give support to", "subject_areas": ["science", "ela"], "complexity_tier": 3, "word_family": ["corroboration", "corroborative"]},
        {"word": "substantiate", "grade_level": 8, "definition": "provide evidence to support or prove", "subject_areas": ["ela", "science"], "complexity_tier": 3, "word_family": ["substantiation", "substantive"]},
        {"word": "quantify", "grade_level": 8, "definition": "express or measure the quantity of", "subject_areas": ["math", "science"], "complexity_tier": 3, "word_family": ["quantification", "quantitative"]},
        
        # Advanced Reasoning & Logic
        {"word": "deduce", "grade_level": 8, "definition": "arrive at a conclusion by reasoning", "subject_areas": ["math", "science"], "complexity_tier": 3, "word_family": ["deduction", "deductive"]},
        {"word": "induce", "grade_level": 8, "definition": "bring about or give rise to", "subject_areas": ["science"], "complexity_tier": 3, "word_family": ["induction", "inductive"]},
        {"word": "extrapolate", "grade_level": 8, "definition": "extend application beyond the original range", "subject_areas": ["math", "science"], "complexity_tier": 3, "word_family": ["extrapolation"]},
        {"word": "generalize", "grade_level": 8, "definition": "make a general or broad statement", "subject_areas": ["math", "science"], "complexity_tier": 2, "word_family": ["generalization", "general"]},
        {"word": "speculate", "grade_level": 8, "definition": "form a theory without firm evidence", "subject_areas": ["science", "ela"], "complexity_tier": 2, "word_family": ["speculation", "speculative"]},
        
        # Advanced Communication
        {"word": "convey", "grade_level": 8, "definition": "transport or communicate", "subject_areas": ["ela"], "complexity_tier": 2, "word_family": ["conveyance"]},
        {"word": "elucidate", "grade_level": 8, "definition": "make clear; explain", "subject_areas": ["ela"], "complexity_tier": 3, "word_family": ["elucidation"]},
        {"word": "exemplify", "grade_level": 8, "definition": "be a typical example of", "subject_areas": ["ela"], "complexity_tier": 2, "word_family": ["exemplification", "example"]},
        {"word": "characterize", "grade_level": 8, "definition": "describe the distinctive nature or features of", "subject_areas": ["ela", "science"], "complexity_tier": 2, "word_family": ["characterization", "characteristic"]},
        {"word": "contextualize", "grade_level": 8, "definition": "place or study in context", "subject_areas": ["ela"], "complexity_tier": 3, "word_family": ["contextualization", "context"]},
    ]
    
    # Add more representative words
    additional_words = [
        {"word": "hypothesize", "grade_level": 8, "definition": "put forward as a hypothesis", "subject_areas": ["science"], "complexity_tier": 3, "word_family": ["hypothesis", "hypothetical"]},
        {"word": "methodology", "grade_level": 8, "definition": "a system of methods used in a particular area", "subject_areas": ["science"], "complexity_tier": 3, "word_family": ["method", "methodological"]},
        {"word": "paradigm", "grade_level": 8, "definition": "a typical example or pattern", "subject_areas": ["science", "ela"], "complexity_tier": 3, "word_family": ["paradigmatic"]},
        {"word": "phenomenon", "grade_level": 8, "definition": "a fact or situation that is observed", "subject_areas": ["science"], "complexity_tier": 3, "word_family": ["phenomenal"]},
        {"word": "theoretical", "grade_level": 8, "definition": "concerned with or involving theory", "subject_areas": ["science", "math"], "complexity_tier": 3, "word_family": ["theory", "theorize"]},
    ]
    
    words.extend(additional_words)
    return words


def main():
    """Generate corpus files for all grade levels."""
    corpus_dir = Path("src/vocabulary/corpus")
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and save corpus files
    grade_6_words = generate_grade_6_corpus()
    grade_7_words = generate_grade_7_corpus()
    grade_8_words = generate_grade_8_corpus()
    
    with open(corpus_dir / "common_core_grade_6.json", "w") as f:
        json.dump(grade_6_words, f, indent=2)
    
    with open(corpus_dir / "common_core_grade_7.json", "w") as f:
        json.dump(grade_7_words, f, indent=2)
    
    with open(corpus_dir / "common_core_grade_8.json", "w") as f:
        json.dump(grade_8_words, f, indent=2)
    
    print(f"Generated corpus files:")
    print(f"  Grade 6: {len(grade_6_words)} words")
    print(f"  Grade 7: {len(grade_7_words)} words")
    print(f"  Grade 8: {len(grade_8_words)} words")
    print(f"  Total: {len(grade_6_words) + len(grade_7_words) + len(grade_8_words)} words")
    print("\nNote: This is a representative sample for MVP.")
    print("Production corpus should include 500+ words per grade from:")
    print("  - Common Core State Standards")
    print("  - Academic Word List (AWL)")
    print("  - COCA (Corpus of Contemporary American English)")


if __name__ == "__main__":
    main()

