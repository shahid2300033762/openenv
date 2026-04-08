"""
Data Cleaning grader — evaluates improvement, not exact output.

Compares BEFORE vs AFTER dataset error counts:
  - Missing values handled: 30%
  - Duplicates removed: 30%
  - Formatting corrected (includes casing): 40%

Penalises invalid transformations (data loss, new errors).
Deterministic.
"""

from __future__ import annotations

from typing import Dict, List

from grading.utils import clamp_score
from tasks.data_cleaning.data import count_errors  # type: ignore


def grade_data_cleaning(
    original_dataset: List[Dict[str, str]],
    cleaned_dataset: List[Dict[str, str]],
    original_row_count: int,
) -> Dict[str, float]:
    """
    Grade a data-cleaning step by comparing before/after error counts.

    Returns breakdown:
      missing_score, duplicates_score, format_score, total, data_loss_penalty
    """
    before = count_errors(original_dataset)
    after = count_errors(cleaned_dataset)

    # --- Missing values handled (30%) ---
    missing_improvement: float = 1.0
    if before["missing"] > 0:
        missing_improvement = max(0.001, float(before["missing"] - after["missing"]) / float(before["missing"]))

    # --- Duplicates removed (30%) ---
    dup_improvement: float = 1.0
    if before["duplicates"] > 0:
        dup_improvement = max(0.001, float(before["duplicates"] - after["duplicates"]) / float(before["duplicates"]))

    # --- Formatting corrected (40%) — covers format_errors + casing ---
    before_fmt = before["format_errors"] + before["casing_issues"]
    after_fmt = after["format_errors"] + after["casing_issues"]
    fmt_improvement: float = 1.0
    if before_fmt > 0:
        fmt_improvement = max(0.001, float(before_fmt - after_fmt) / float(before_fmt))

    # --- Data loss penalty ---
    # If the cleaned dataset lost valid rows (beyond removing duplicates),
    # penalise proportionally.
    expected_unique_rows = original_row_count - before["duplicates"]
    cleaned_count = len(cleaned_dataset)
    data_loss_penalty: float = 0.001
    if cleaned_count < expected_unique_rows:
        lost = expected_unique_rows - cleaned_count
        data_loss_penalty = min(0.3, 0.1 * float(lost))  # cap at 0.3

    # --- New errors penalty ---
    # If cleaning introduced MORE errors in any category, penalise.
    new_error_penalty: float = 0.001
    for key in ("missing", "format_errors", "casing_issues"):
        if int(after[key]) > int(before[key]):
            diff_val: int = int(after[key]) - int(before[key])
            new_error_penalty = float(new_error_penalty) + (0.05 * float(diff_val))  # type: ignore
    new_error_penalty = min(0.3, float(new_error_penalty))  # type: ignore

    total: float = (
        0.30 * missing_improvement
        + 0.30 * dup_improvement
        + 0.40 * fmt_improvement
        - data_loss_penalty
        - new_error_penalty
    )
    total = clamp_score(total)

    return {
        "missing_score": clamp_score(missing_improvement),
        "duplicates_score": clamp_score(dup_improvement),
        "format_score": clamp_score(fmt_improvement),
        "data_loss_penalty": clamp_score(data_loss_penalty),
        "new_error_penalty": clamp_score(new_error_penalty),
        "total": total,
    }
