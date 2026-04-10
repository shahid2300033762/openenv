"""
Email Triage environment — OpenEnv compliant.

Phases: classify → prioritize → respond
ideal_steps=3, max_steps=5
"""

from __future__ import annotations
from grading.utils import clamp_score

from typing import Dict, List, Optional, Tuple

from models import Action, Observation, Reward, RewardBreakdown, RewardPenalties
from tasks.base_environment import BaseEnvironment
from tasks.email_triage.data import EMAILS
from tasks.email_triage.grader import grade_email_triage


class EmailTriageEnvironment(BaseEnvironment):
    """Simulate customer support email triage."""

    TASK_NAME = "email_triage"
    MAX_STEPS = 5
    IDEAL_STEPS = 3

    def __init__(self, email_index: int = 0) -> None:
        super().__init__(self.TASK_NAME, self.MAX_STEPS, self.IDEAL_STEPS)
        self._email_index = email_index % len(EMAILS)
        self._email = EMAILS[self._email_index]

        # Accumulated answers
        self._classification: Optional[str] = None
        self._priority: Optional[str] = None
        self._response: Optional[str] = None

    # -------------------------------------------------------------------
    # Abstract implementations
    # -------------------------------------------------------------------

    def _get_phase_order(self) -> List[str]:
        return ["classify", "prioritize", "respond"]

    def _get_valid_action_types(self) -> List[str]:
        phase = self._current_phase
        if phase == "classify":
            return ["classify"]
        elif phase == "prioritize":
            return ["classify", "prioritize"]
        elif phase == "respond":
            return ["prioritize", "respond"]
        return ["classify", "prioritize", "respond"]

    def _get_initial_observation(self) -> Observation:
        email = self._email
        return Observation(
            task_name=self.TASK_NAME,
            step=0,
            instructions=(
                "You are a customer support agent. Read the email below and perform "
                "three steps in order:\n"
                "1. CLASSIFY the email (complaint / refund / failure / promotion / query)\n"
                "2. PRIORITIZE it (critical / high / medium / low)\n"
                "3. RESPOND with a professional reply\n\n"
                "Use the corresponding action_type for each step."
            ),
            context=f"From: {email['sender']}\nSubject: {email['subject']}",
            data=email["body"],
            feedback="",
            available_actions=["classify"],
            phase="classify",
        )

    def _execute_action(
        self, action: Action
    ) -> Tuple[Observation, Reward, bool]:
        email = self._email
        gt = email["ground_truth"]

        # --- Process action by type ---
        if action.action_type == "classify":
            self._classification = action.value
            grades = grade_email_triage(
                self._classification, None, None, gt
            )
            done = False
            feedback = (
                f"Classification recorded: '{action.value}'. "
                f"Now assign a priority level."
            )
            next_actions = ["prioritize"]
            correctness = grades["classification_score"]
            progress = 0.33

        elif action.action_type == "prioritize":
            self._priority = action.value
            grades = grade_email_triage(
                self._classification, self._priority, None, gt
            )
            done = False
            feedback = (
                f"Priority set to: '{action.value}'. "
                f"Now draft a professional response."
            )
            next_actions = ["respond"]
            correctness = grades["priority_score"]
            progress = 0.66

        elif action.action_type == "respond":
            self._response = action.value
            grades = grade_email_triage(
                self._classification, self._priority, self._response, gt
            )
            done = True
            feedback = (
                f"Response drafted. Final scores:\n"
                f"  Classification: {grades['classification_score']:.2f}\n"
                f"  Priority: {grades['priority_score']:.2f}\n"
                f"  Response: {grades['response_score']:.2f}\n"
                f"  Total: {grades['total']:.2f}"
            )
            next_actions = []
            correctness = grades["total"]
            progress = 0.999

        else:
            # Shouldn't reach here (base validates), but safety net
            return (
                self._last_observation or self._get_initial_observation(),
                Reward(
                    score=clamp_score(0.0),
                    feedback=f"Unknown action type: {action.action_type}",
                    penalties=RewardPenalties(invalid_action_penalty=0.2),
                ),
                False,
            )

        obs = Observation(
            task_name=self.TASK_NAME,
            step=self._step_count,
            instructions=(
                "Continue the email triage workflow."
                if not done
                else "Task complete."
            ),
            context=f"From: {email['sender']}\nSubject: {email['subject']}",
            data=email["body"],
            feedback=feedback,
            available_actions=next_actions,
            phase=self._current_phase,
        )

        strict_correctness = clamp_score(correctness)
        strict_progress = clamp_score(progress)

        reward = Reward(
            score=strict_correctness,
            feedback=feedback,
            breakdown=RewardBreakdown(
                correctness=strict_correctness,
                progress=strict_progress,
            ),
        )

        return obs, reward, done
