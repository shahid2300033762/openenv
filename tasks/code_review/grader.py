"""
Code Review grader — fuzzy/semantic evaluation.

Weights:
  - Issue detection: 30%
  - Fix correctness: 40%
  - Optimisation & code quality: 30%

Accepts multiple valid solutions.  Deterministic.
Enhanced with synonym expansion for better matching.
"""

from __future__ import annotations

from typing import Dict, List, Set

from grading.utils import fuzzy_keyword_match, normalize_text, semantic_similarity, expand_with_synonyms


def grade_issue_detection(
    identified_issues: List[str],
    expected_issues: List[Dict],
) -> Dict[str, float]:
    """
    Grade how many expected issues the agent identified.
    Uses fuzzy matching so exact wording isn't required.
    """
    if not expected_issues:
        return {"detection_score": 1.0, "matched_issues": [], "missed_issues": []}

    matched: List[str] = []
    matched_ids: Set[str] = set()

    for identified in identified_issues:
        best_score = 0.0
        best_issue_id = ""
        
        # Expand with synonyms for better matching
        identified_expanded = expand_with_synonyms(identified)
        
        for expected in expected_issues:
            if expected["id"] in matched_ids:
                continue
            # Compare against description with synonym expansion
            desc_expanded = expand_with_synonyms(expected["description"])
            sim = semantic_similarity(identified_expanded, desc_expanded)
            # Also check against category keywords
            cat_bonus = 0.2 if normalize_text(expected["category"]) in normalize_text(identified) else 0.0
            total = min(1.0, sim + cat_bonus)
            if total > best_score:
                best_score = total
                best_issue_id = expected["id"]

        # Threshold for matching: 0.15 (generous to accept varied phrasing)
        # Lowered from 0.2 to be more forgiving while maintaining quality
        if best_score >= 0.15 and best_issue_id:
            matched.append(best_issue_id)
            matched_ids.add(best_issue_id)

    detection_rate = len(matched) / len(expected_issues)

    missed = [e["id"] for e in expected_issues if e["id"] not in matched_ids]

    return {
        "detection_score": round(detection_rate, 4),
        "matched_issues": matched,
        "missed_issues": missed,
    }


def grade_fix_correctness(
    suggested_fixes: List[str],
    expected_issues: List[Dict],
) -> float:
    """
    Grade whether suggested fixes are valid.
    Checks each fix against the valid_fixes list using fuzzy matching.
    """
    if not expected_issues or not suggested_fixes:
        return 0.0

    total_score = 0.0
    max_possible = len(expected_issues)

    for fix in suggested_fixes:
        best_fix_score = 0.0
        for issue in expected_issues:
            valid_fixes = issue.get("valid_fixes", [])
            if valid_fixes:
                score = fuzzy_keyword_match(fix, valid_fixes)
                best_fix_score = max(best_fix_score, score)
        total_score += best_fix_score

    # Normalise by number of expected issues
    return round(min(1.0, total_score / max_possible), 4)


def grade_code_quality(
    suggestions: List[str],
    expected_issues: List[Dict],
) -> float:
    """
    Grade optimisation and code quality suggestions.
    Rewards mentions of performance, readability, security, best practices.
    """
    if not suggestions:
        return 0.0

    quality_keywords = [
        "performance", "complexity", "o(n)", "o(1)", "efficient",
        "readability", "clean", "maintainable", "naming",
        "security", "injection", "sanitize", "validate",
        "best practice", "pattern", "solid", "dry",
        "type hint", "typing", "documentation", "docstring",
        "test", "edge case", "error handling", "exception",
    ]

    combined = " ".join(suggestions)
    score = fuzzy_keyword_match(combined, quality_keywords)

    # Bonus for addressing performance issues specifically
    perf_issues = [i for i in expected_issues if i.get("category") == "performance"]
    if perf_issues:
        for s in suggestions:
            for pi in perf_issues:
                sim = semantic_similarity(s, pi["description"])
                if sim > 0.2:
                    score += 0.15
                    break

    return round(min(1.0, score), 4)


def grade_code_review(
    identified_issues: List[str],
    suggested_fixes: List[str],
    quality_suggestions: List[str],
    expected_issues: List[Dict],
) -> Dict[str, float]:
    """
    Full code review grading. Returns breakdown:
      detection_score (30%), fix_score (40%), quality_score (30%), total
    """
    detection = grade_issue_detection(identified_issues, expected_issues)
    detection_score = detection["detection_score"]
    fix_score = grade_fix_correctness(suggested_fixes, expected_issues)
    quality_score = grade_code_quality(quality_suggestions, expected_issues)

    total = (
        0.30 * detection_score
        + 0.40 * fix_score
        + 0.30 * quality_score
    )

    return {
        "detection_score": detection_score,
        "fix_score": fix_score,
        "quality_score": quality_score,
        "matched_issues": detection["matched_issues"],
        "missed_issues": detection["missed_issues"],
        "total": round(total, 4),
    }
