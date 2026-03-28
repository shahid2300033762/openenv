"""
Email Triage grader — semantic evaluation with partial credit.

Weights:
  - Classification accuracy: 40%
  - Priority correctness: 30%
  - Response quality: 30%

Deterministic. Tolerates phrasing variation via fuzzy matching.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from grading.utils import (
    fuzzy_keyword_match,
    keyword_group_match,
    normalize_text,
    semantic_similarity,
)
from tasks.email_triage.data import CLASSIFICATION_KEYWORDS, PRIORITY_BY_CLASSIFICATION


def grade_classification(predicted: str, ground_truth: str) -> float:
    """
    Score classification accuracy.
    Exact match = 1.0, same-family partial credit, else fuzzy match.
    """
    pred = normalize_text(predicted)
    gt = normalize_text(ground_truth)

    if pred == gt:
        return 1.0

    # Partial credit: complaint ↔ refund are related (0.4)
    related_pairs = {
        frozenset({"complaint", "refund"}): 0.4,
        frozenset({"failure", "complaint"}): 0.3,
        frozenset({"query", "complaint"}): 0.2,
    }
    pair = frozenset({pred, gt})
    if pair in related_pairs:
        return related_pairs[pair]

    return 0.0


def grade_priority(predicted: str, ground_truth: str) -> float:
    """
    Score priority correctness.
    Exact = 1.0, one level off = 0.5, two+ levels off = 0.0.
    """
    levels = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    pred = normalize_text(predicted)
    gt = normalize_text(ground_truth)

    if pred == gt:
        return 1.0

    pred_level = levels.get(pred, 0)
    gt_level = levels.get(gt, 0)

    diff = abs(pred_level - gt_level)
    if diff == 1:
        return 0.5
    return 0.0


def grade_response_quality(
    response: str,
    expected_keywords: List[str],
    classification: str,
) -> float:
    """
    Score response quality based on:
      - Acknowledgment (does it address the issue?)
      - Professionalism (polite language)
      - Actionable content (concrete next steps)

    Uses fuzzy keyword matching, not exact string comparison.
    """
    if not response or not response.strip():
        return 0.0

    resp_lower = normalize_text(response)
    score = 0.0

    # 1) Acknowledgment — does it reference the customer's issue? (0.35)
    if expected_keywords:
        kw_score = fuzzy_keyword_match(resp_lower, expected_keywords)
        score += 0.35 * min(1.0, kw_score * 2.0)  # scale up small overlaps

    # 2) Professionalism — polite / empathetic language (0.30)
    professional_markers = [
        "thank", "appreciate", "understand", "sorry", "apologize",
        "apologies", "happy to help", "we value", "please",
    ]
    prof_hits = sum(1 for m in professional_markers if m in resp_lower)
    score += 0.30 * min(1.0, prof_hits / 3.0)

    # 3) Actionable content — concrete next steps (0.35)
    action_markers = [
        "will", "we'll", "going to", "next step", "please",
        "reach out", "follow up", "resolve", "process", "investigate",
        "team", "update", "within", "hours", "shortly",
    ]
    action_hits = sum(1 for m in action_markers if m in resp_lower)
    score += 0.35 * min(1.0, action_hits / 3.0)

    # Promotions shouldn't get a response — if classification is promotion
    # and agent correctly didn't write much, give full marks
    if classification == "promotion" and len(resp_lower.split()) < 10:
        return 1.0

    return min(1.0, score)


def grade_email_triage(
    classification: Optional[str],
    priority: Optional[str],
    response: Optional[str],
    ground_truth: Dict,
) -> Dict[str, float]:
    """
    Full email triage grading. Returns breakdown dict:
      classification_score, priority_score, response_score, total
    """
    gt_class = ground_truth["classification"]
    gt_priority = ground_truth["priority"]
    gt_keywords = ground_truth.get("response_keywords", [])

    class_score = grade_classification(classification or "", gt_class)
    prio_score = grade_priority(priority or "", gt_priority)
    resp_score = grade_response_quality(response or "", gt_keywords, gt_class)

    total = (
        0.40 * class_score
        + 0.30 * prio_score
        + 0.30 * resp_score
    )

    return {
        "classification_score": round(class_score, 4),
        "priority_score": round(prio_score, 4),
        "response_score": round(resp_score, 4),
        "total": round(total, 4),
    }
