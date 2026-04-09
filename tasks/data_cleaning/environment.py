"""
Data Cleaning environment — OpenEnv compliant.

Phases: fix_missing → remove_duplicates → normalize_casing → fix_format
ideal_steps=4, max_steps=10
"""

from __future__ import annotations

import copy
import re
from typing import Dict, List, Tuple

from grading.utils import clamp_score
from models import Action, Observation, Reward, RewardBreakdown, RewardPenalties  # type: ignore
from tasks.base_environment import BaseEnvironment  # type: ignore
from tasks.data_cleaning.data import (  # type: ignore
    COLUMNS,
    count_errors,
    csv_to_dataset,
    dataset_to_csv,
    get_messy_dataset,
)
from tasks.data_cleaning.grader import grade_data_cleaning  # type: ignore


class DataCleaningEnvironment(BaseEnvironment):
    """Step-by-step data cleaning of a messy tabular dataset."""

    TASK_NAME = "data_cleaning"
    MAX_STEPS = 10
    IDEAL_STEPS = 4

    def __init__(self) -> None:
        super().__init__(self.TASK_NAME, self.MAX_STEPS, self.IDEAL_STEPS)  # type: ignore
        self._original_dataset: List[Dict[str, str]] = []
        self._current_dataset: List[Dict[str, str]] = []
        self._original_row_count: int = 0
        self._snapshot_before: List[Dict[str, str]] = []

    # -------------------------------------------------------------------
    # Abstract implementations
    # -------------------------------------------------------------------

    def _get_phase_order(self) -> List[str]:
        return ["fix_missing", "remove_duplicates", "normalize_casing", "fix_format"]

    def _get_valid_action_types(self) -> List[str]:
        return ["fix_missing", "remove_duplicates", "normalize_casing", "fix_format"]

    def _get_initial_observation(self) -> Observation:
        self._original_dataset = get_messy_dataset()
        self._current_dataset = copy.deepcopy(self._original_dataset)
        self._original_row_count = len(self._original_dataset)
        self._snapshot_before = copy.deepcopy(self._original_dataset)

        errors = count_errors(self._current_dataset)
        csv = dataset_to_csv(self._current_dataset)

        return Observation(
            task_name=self.TASK_NAME,
            step=0,
            instructions=(
                "You are a data analyst. The dataset below has quality issues:\n"
                f"  - Missing values: {errors['missing']}\n"
                f"  - Duplicate rows: {errors['duplicates']}\n"
                f"  - Casing issues: {errors['casing_issues']}\n"
                f"  - Format errors: {errors['format_errors']}\n\n"
                "Clean the data step by step using these action types:\n"
                "  1. fix_missing — fill/remove missing values (value = strategy: 'fill_default' or 'remove_rows')\n"
                "  2. remove_duplicates — remove duplicate rows (value = 'deduplicate')\n"
                "  3. normalize_casing — fix casing in name/city columns (value = 'title_case')\n"
                "  4. fix_format — fix date/email/zip formats (value = 'standardize')\n\n"
                "Put your cleaned CSV in the 'target' field, or use the keyword strategies above."
            ),
            context=f"Dataset: {len(self._current_dataset)} rows, {len(COLUMNS)} columns",
            data=csv,
            feedback="",
            available_actions=["fix_missing", "remove_duplicates", "normalize_casing", "fix_format"],
            phase="fix_missing",
        )

    def _execute_action(
        self, action: Action
    ) -> Tuple[Observation, Reward, bool]:
        snapshot_before = copy.deepcopy(self._current_dataset)

        # --- Apply transformation ---
        if action.action_type == "fix_missing":
            self._apply_fix_missing(action.value)
        elif action.action_type == "remove_duplicates":
            self._apply_remove_duplicates()
        elif action.action_type == "normalize_casing":
            self._apply_normalize_casing()
        elif action.action_type == "fix_format":
            self._apply_fix_format()

        # --- Grade improvement ---
        grades = grade_data_cleaning(
            snapshot_before, self._current_dataset, self._original_row_count
        )
        overall = grade_data_cleaning(
            self._original_dataset, self._current_dataset, self._original_row_count
        )

        errors_after = count_errors(self._current_dataset)
        all_clean = errors_after["total"] == 0
        done = all_clean

        # Progress = fraction of original errors fixed
        original_errors = count_errors(self._original_dataset)
        if original_errors["total"] > 0:
            progress = 1.0 - (errors_after["total"] / original_errors["total"])
        else:
            progress = 1.0
        progress = max(0.0, min(1.0, progress))

        feedback = (
            f"Applied '{action.action_type}'. Remaining errors: "
            f"missing={errors_after['missing']}, "
            f"duplicates={errors_after['duplicates']}, "
            f"casing={errors_after['casing_issues']}, "
            f"format={errors_after['format_errors']}. "
            f"Step improvement: {grades['total']:.2f}, "
            f"Overall progress: {overall['total']:.2f}"
        )

        csv = dataset_to_csv(self._current_dataset)

        obs = Observation(
            task_name=self.TASK_NAME,
            step=self._step_count,
            instructions="Continue cleaning or finish." if not done else "Dataset is clean!",
            context=f"Dataset: {len(self._current_dataset)} rows",
            data=csv,
            feedback=feedback,
            available_actions=[] if done else ["fix_missing", "remove_duplicates", "normalize_casing", "fix_format"],
            phase=self._current_phase,
        )

        strict_score = clamp_score(grades["total"])
        strict_correctness = clamp_score(overall["total"])
        strict_progress = clamp_score(progress)

        reward = Reward(
            score=strict_score,
            feedback=feedback,
            breakdown=RewardBreakdown(
                correctness=strict_correctness,
                progress=strict_progress,
            ),
        )

        return obs, reward, done

    # -------------------------------------------------------------------
    # Data transformations
    # -------------------------------------------------------------------

    def _apply_fix_missing(self, strategy: str) -> None:
        """Fill or remove missing values."""
        missing_sentinels = {"", "N/A", "null", "None", "n/a", "NULL"}
        if "remove" in strategy.lower():
            self._current_dataset = [
                row for row in self._current_dataset
                if not any(row.get(c, "") in missing_sentinels for c in COLUMNS)
            ]
        else:
            # Default: fill with reasonable defaults
            defaults = {
                "name": "Unknown",
                "email": "unknown@example.com",
                "city": "Unknown",
                "state": "NA",
                "zip": "00000",
                "date_joined": "2024-01-01",
                "plan": "Free",
                "amount": "0.00",
            }
            for row in self._current_dataset:
                for col in COLUMNS:
                    if row.get(col, "") in missing_sentinels:
                        row[col] = defaults.get(col, "")

    def _apply_remove_duplicates(self) -> None:
        """Remove exact duplicate rows (keep first occurrence)."""
        seen = set()
        deduped = []
        for row in self._current_dataset:
            key = "|".join(str(row.get(c, "")) for c in COLUMNS)
            if key not in seen:
                seen.add(key)
                deduped.append(row)
        self._current_dataset = deduped

    def _apply_normalize_casing(self) -> None:
        """Title-case name and city columns."""
        for row in self._current_dataset:
            for col in ("name", "city"):
                val = row.get(col, "")
                if val and val not in ("", "N/A", "null", "None"):
                    row[col] = val.title()

    def _apply_fix_format(self) -> None:
        """Standardise dates (YYYY-MM-DD), emails, and zip codes."""
        for row in self._current_dataset:
            # Fix dates
            date = row.get("date_joined", "")
            if date:
                row["date_joined"] = self._normalize_date(date)

            # Fix emails
            email = row.get("email", "")
            if email:
                # Remove double @
                email = re.sub(r"@{2,}", "@", email)
                # Add domain if missing
                if email.endswith("@"):
                    email += "example.com"
                row["email"] = email

            # Fix zip codes
            zip_code = row.get("zip", "")
            if zip_code and zip_code not in ("", "N/A", "null", "None"):
                digits = re.sub(r"[^0-9]", "", zip_code)
                if len(digits) < 5:
                    digits = digits.ljust(5, "0")
                elif len(digits) > 5:
                    match = re.search(r"^(\d{5})", digits)
                    if match:
                        digits = match.group(1)
                row["zip"] = digits

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Try to convert various date formats to YYYY-MM-DD."""
        import calendar

        # Already correct
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str

        # MM/DD/YYYY
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", date_str)
        if m:
            month, day, year = m.groups()
            month = min(int(month), 12)
            day = min(int(day), 28)
            return f"{year}-{int(month):02d}-{int(day):02d}"

        # "Month D, YYYY"
        months = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
        for mname, mnum in months.items():
            if mname in date_str.lower():
                dm = re.search(r"(\d{1,2})", date_str)
                ym = re.search(r"(\d{4})", date_str)
                if dm and ym:
                    day = min(int(dm.group(1)), 28)
                    return f"{ym.group(1)}-{mnum:02d}-{day:02d}"

        # Fallback
        return "2024-01-01"
