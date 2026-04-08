"""
Shared grading utilities — fuzzy matching, penalties, clamping.

All functions are deterministic: same input → same output, no randomness.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set


# ---------------------------------------------------------------------------
# Text similarity / fuzzy matching (deterministic, no ML)
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def token_set(text: str) -> Set[str]:
    """Return set of alphanumeric tokens."""
    return set(re.findall(r"[a-z0-9]+", normalize_text(text)))


def fuzzy_keyword_match(candidate: str, references: List[str]) -> float:
    """
    Token-overlap similarity between candidate and the best-matching reference.
    Returns 0.0 – 1.0.  Deterministic.
    """
    if not references:
        return 0.0
    cand_tokens = token_set(candidate)
    if not cand_tokens:
        return 0.0
    best = 0.0
    for ref in references:
        ref_tokens = token_set(ref)
        if not ref_tokens:
            continue
        overlap = len(cand_tokens & ref_tokens)
        union = len(cand_tokens | ref_tokens)
        score = overlap / union if union else 0.0
        best = max(best, score)
    return best


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Lightweight semantic similarity using Jaccard index on token bigrams.
    Deterministic, no external dependencies.
    """
    def bigrams(text: str) -> Set[str]:
        tokens = list(token_set(text))
        tokens.sort()
        if len(tokens) < 2:
            return set(tokens)
        return {f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)}

    a_bg = bigrams(text_a) | token_set(text_a)
    b_bg = bigrams(text_b) | token_set(text_b)
    if not a_bg or not b_bg:
        return 0.0
    return len(a_bg & b_bg) / len(a_bg | b_bg)


def keyword_group_match(text: str, keyword_groups: Dict[str, List[str]]) -> str:
    """
    Match text against named keyword groups.  Returns the group name with
    the highest token overlap, or empty string if none match.
    """
    text_tokens = token_set(text)
    best_group = ""
    best_score = 0.0
    for group_name, keywords in keyword_groups.items():
        kw_tokens = set()
        for kw in keywords:
            kw_tokens |= token_set(kw)
        overlap = len(text_tokens & kw_tokens)
        if overlap > best_score:
            best_score = overlap
            best_group = group_name
    return best_group


def expand_with_synonyms(text: str) -> str:
    """
    Expand text with common technical synonyms for better matching.
    Used to make grading more forgiving of phrasing variations.
    """
    synonyms = {
        'sql injection': ['sqli', 'sql inject', 'query injection'],
        'parameterized': ['prepared statement', 'placeholder', 'bind variable'],
        'hash': ['hashing', 'hashed', 'digest'],
        'bcrypt': ['argon2', 'scrypt', 'password hash'],
        'validation': ['validate', 'check', 'verify'],
        'sanitize': ['sanitization', 'escape', 'clean'],
    }
    
    expanded = text.lower()
    for key, syns in synonyms.items():
        if key in expanded:
            expanded += ' ' + ' '.join(syns)
    
    return expanded


# ---------------------------------------------------------------------------
# Penalty / bonus helpers
# ---------------------------------------------------------------------------

def calculate_step_penalty(current_step: int, ideal_steps: int) -> float:
    """Penalise exceeding ideal_steps.  Returns >= 0."""
    if ideal_steps <= 0:
        return 0.0
    ratio = current_step / ideal_steps
    return max(0.0, 0.05 * (ratio - 1.0))


def calculate_early_bonus(done: bool, current_step: int, ideal_steps: int) -> float:
    """Bonus for finishing before ideal_steps."""
    if done and current_step < ideal_steps:
        return 0.1
    return 0.0


def calculate_repetition_penalty(
    action_key: str, history: List[str]
) -> float:
    """Return 0.1 if action_key already in history, else 0."""
    return 0.1 if action_key in history else 0.0


def evaluate_reasoning(reasoning: str) -> float:
    """
    Score reasoning quality 0.0 – 0.1 with chain-of-thought evaluation.
    Rewards length, specificity, logical structure, and multi-step reasoning.
    Deterministic.
    """
    if not reasoning or not reasoning.strip():
        return 0.0
    text = reasoning.strip()
    score = 0.0
    
    # Length reward: up to 0.04 for ≥ 50 words
    word_count = len(text.split())
    score += min(0.04, 0.04 * (word_count / 50))
    
    # Specificity: contains numbers or technical terms
    if re.search(r"\d", text):
        score += 0.02
    technical = {"because", "therefore", "since", "however", "thus", "issue",
                 "error", "fix", "missing", "invalid", "duplicate",
                 "priority", "critical", "bug", "performance"}
    words_lower = set(text.lower().split())
    if words_lower & technical:
        score += 0.02
    
    # Coherence: has sentence structure (periods / colons)
    if re.search(r"[.;:]", text):
        score += 0.01
    
    # NEW: Chain-of-thought markers (multi-step reasoning)
    cot_markers = {
        "first", "second", "third", "then", "next", "finally",
        "step 1", "step 2", "additionally", "furthermore", "moreover"
    }
    if any(marker in text.lower() for marker in cot_markers):
        score += 0.02  # Bonus for structured reasoning
    
    # NEW: Causal reasoning (because → therefore patterns)
    causal_patterns = [
        r"because.*(?:therefore|thus|so|hence)",
        r"since.*(?:therefore|thus|so)",
        r"if.*then",
        r"given.*(?:we|i).*(?:should|must|can)"
    ]
    if any(re.search(pattern, text.lower()) for pattern in causal_patterns):
        score += 0.01  # Bonus for causal reasoning
    
    return min(0.1, score)


def clamp_score(score: float) -> float:
    """Clamp to strict (0, 1) — never exactly 0.0 or 1.0.
    
    The competition validator requires scores strictly between 0 and 1.
    """
    EPS = 0.001
    clamped = max(0.0, min(1.0, score))
    # Enforce strict bounds: push away from exact 0.0 and 1.0
    if clamped <= 0.0:
        return EPS
    if clamped >= 1.0:
        return 1.0 - EPS
    return clamped


def check_contradictions(current_value: str, previous_values: List[str]) -> bool:
    """
    Detect if current value directly contradicts a previous value.
    Simple heuristic: if the agent previously chose the opposite for
    the same field, it's a contradiction.
    """
    if not previous_values:
        return False
    current_norm = normalize_text(current_value)
    for prev in previous_values:
        prev_norm = normalize_text(prev)
        if current_norm and prev_norm and current_norm != prev_norm:
            # Check if they are direct negations
            negation_pairs = [
                ("high", "low"), ("urgent", "low"),
                ("spam", "complaint"), ("spam", "query"),
                ("correct", "incorrect"), ("valid", "invalid"),
            ]
            for a, b in negation_pairs:
                if (a in current_norm and b in prev_norm) or \
                   (b in current_norm and a in prev_norm):
                    return True
    return False
