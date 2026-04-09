"""
Code Review environment — OpenEnv compliant.

Phases: identify_issue → suggest_fix → optimize_code
ideal_steps=5, max_steps=8
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from grading.utils import clamp_score
from models import Action, Observation, Reward, RewardBreakdown, RewardPenalties
from tasks.base_environment import BaseEnvironment
from tasks.code_review.data import get_snippet_by_index
from tasks.code_review.grader import grade_code_review


class CodeReviewEnvironment(BaseEnvironment):
    """Simulate pull request code review."""

    TASK_NAME = "code_review"
    MAX_STEPS = 8
    IDEAL_STEPS = 5

    def __init__(self, snippet_index: int = 0) -> None:
        super().__init__(self.TASK_NAME, self.MAX_STEPS, self.IDEAL_STEPS)
        self._snippet_index = snippet_index
        self._snippet: Dict = {}

        # Accumulated review artifacts
        self._identified_issues: List[str] = []
        self._suggested_fixes: List[str] = []
        self._quality_suggestions: List[str] = []

    # -------------------------------------------------------------------
    # Abstract implementations
    # -------------------------------------------------------------------

    def _get_phase_order(self) -> List[str]:
        return ["identify_issue", "suggest_fix", "optimize_code"]

    def _get_valid_action_types(self) -> List[str]:
        # Code review allows interleaved actions since you might
        # find issues, fix them, then find more in the same pass
        return ["identify_issue", "suggest_fix", "optimize_code"]

    def _get_initial_observation(self) -> Observation:
        self._snippet = get_snippet_by_index(self._snippet_index)
        self._identified_issues = []
        self._suggested_fixes = []
        self._quality_suggestions = []

        return Observation(
            task_name=self.TASK_NAME,
            step=0,
            instructions=(
                "You are a senior software engineer reviewing a pull request.\n\n"
                f"**PR Title**: {self._snippet['title']}\n"
                f"**Description**: {self._snippet['description']}\n\n"
                "Review the code below and perform these actions:\n"
                "1. **identify_issue** — describe a bug, vulnerability, or problem\n"
                "   (put the issue description in 'value')\n"
                "2. **suggest_fix** — propose a fix for an identified issue\n"
                "   (put the fix description in 'value')\n"
                "3. **optimize_code** — suggest a performance or quality improvement\n"
                "   (put the suggestion in 'value')\n\n"
                "You may perform multiple identify/fix cycles. "
                f"There are {len(self._snippet['issues'])} known issues."
            ),
            context=f"Language: {self._snippet['language']} | PR: {self._snippet['id']}",
            data=self._snippet["code"],
            feedback="",
            available_actions=["identify_issue", "suggest_fix", "optimize_code"],
            phase="identify_issue",
        )

    def _execute_action(
        self, action: Action
    ) -> Tuple[Observation, Reward, bool]:
        expected = self._snippet["issues"]

        # --- Record action ---
        if action.action_type == "identify_issue":
            self._identified_issues.append(action.value)
        elif action.action_type == "suggest_fix":
            self._suggested_fixes.append(action.value)
        elif action.action_type == "optimize_code":
            self._quality_suggestions.append(action.value)

        # --- Grade current state ---
        grades = grade_code_review(
            self._identified_issues,
            self._suggested_fixes,
            self._quality_suggestions,
            expected,
        )

        # --- Calculate progress ---
        total_expected = len(expected)
        issues_found = len(grades["matched_issues"])
        fixes_made = min(len(self._suggested_fixes), total_expected)
        optimizations = min(len(self._quality_suggestions), 2)

        progress_parts = (
            issues_found / max(1, total_expected) * 0.4
            + fixes_made / max(1, total_expected) * 0.4
            + optimizations / 2.0 * 0.2
        )
        progress = min(1.0, progress_parts)

        # --- Done condition ---
        # Done when: identified ≥80% issues AND suggested fixes AND ≥1 optimization
        detection_threshold = 0.8
        done = (
            grades["detection_score"] >= detection_threshold
            and len(self._suggested_fixes) >= len(grades["matched_issues"])
            and len(self._quality_suggestions) >= 1
        )

        feedback = (
            f"Review progress:\n"
            f"  Issues found: {issues_found}/{total_expected} "
            f"(matched: {grades['matched_issues']})\n"
            f"  Fixes suggested: {len(self._suggested_fixes)}\n"
            f"  Optimizations: {len(self._quality_suggestions)}\n"
            f"  Detection: {grades['detection_score']:.2f} | "
            f"Fix: {grades['fix_score']:.2f} | "
            f"Quality: {grades['quality_score']:.2f} | "
            f"Total: {grades['total']:.2f}"
        )

        if grades["missed_issues"]:
            feedback += f"\n  ⚠ Still missing {len(grades['missed_issues'])} issue(s)"

        obs = Observation(
            task_name=self.TASK_NAME,
            step=self._step_count,
            instructions=(
                "Continue reviewing — find more issues, suggest fixes, or optimise."
                if not done
                else "Review complete! All major issues addressed."
            ),
            context=f"Language: {self._snippet['language']} | PR: {self._snippet['id']}",
            data=self._snippet["code"],
            feedback=feedback,
            available_actions=[] if done else ["identify_issue", "suggest_fix", "optimize_code"],
            phase=self._current_phase,
        )

        strict_score = clamp_score(grades["total"])
        strict_progress = clamp_score(progress)

        reward = Reward(
            score=strict_score,
            feedback=feedback,
            breakdown=RewardBreakdown(
                correctness=strict_score,
                progress=strict_progress,
            ),
        )

        return obs, reward, done
