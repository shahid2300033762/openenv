"""
Abstract base environment enforcing all OpenEnv guarantees:

- Strict Pydantic schema validation on every action
- Valid state-transition enforcement (phase progression)
- Automatic trace logging per step
- Max-steps auto-termination with partial scoring
- Repetition detection
- Invalid action rejection with penalty
- Dense reward at every step

Subclasses must implement:
    _get_initial_observation() → Observation
    _execute_action(action) → Tuple[Observation, Reward, bool]
    _get_valid_action_types() → List[str]
    _get_phase_order() → List[str]
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from models import Action, Observation, Reward, RewardBreakdown, RewardPenalties, State, StepResult
from grading.utils import (
    calculate_early_bonus,
    calculate_repetition_penalty,
    calculate_step_penalty,
    clamp_score,
    evaluate_reasoning,
)


class BaseEnvironment(ABC):
    """Abstract OpenEnv-compliant environment with all system guarantees."""

    def __init__(self, task_name: str, max_steps: int, ideal_steps: int) -> None:
        self.task_name = task_name
        self.max_steps = max_steps
        self.ideal_steps = ideal_steps

        # Episode state
        self._episode_id: str = ""
        self._step_count: int = 0
        self._done: bool = False
        self._current_phase: str = ""
        self._completed_phases: List[str] = []
        self._action_history: List[str] = []
        self._trace: List[Dict[str, Any]] = []
        self._last_observation: Optional[Observation] = None

    # -------------------------------------------------------------------
    # OpenEnv Interface (public)
    # -------------------------------------------------------------------

    def reset(self) -> Observation:
        """Initialize a new episode. Returns typed Observation."""
        self._episode_id = str(uuid.uuid4())
        self._step_count = 0
        self._done = False
        self._completed_phases = []
        self._action_history = []
        self._trace = []

        phases = self._get_phase_order()
        self._current_phase = phases[0] if phases else ""

        obs = self._get_initial_observation()
        self._last_observation = obs
        return obs

    def step(self, action: Action) -> StepResult:
        """Execute an action. Returns typed StepResult — never a raw dict."""
        if self._done:
            return StepResult(
                observation=self._last_observation or self._get_initial_observation(),
                reward=Reward(score=clamp_score(0.0), feedback="Episode already completed."),
                done=True,
                info={"error": "episode_already_done"},
            )

        self._step_count += 1

        # --- Schema validation ---
        try:
            action = Action.model_validate(action.model_dump())
        except Exception as e:
            return self._make_invalid_action_result(f"Schema validation failed: {e}")

        # --- Check action type validity ---
        valid_types = self._get_valid_action_types()
        if action.action_type not in valid_types:
            return self._make_invalid_action_result(
                f"Invalid action_type '{action.action_type}'. "
                f"Valid types for phase '{self._current_phase}': {valid_types}"
            )

        # --- Repetition detection ---
        action_key = f"{action.action_type}:{action.target}:{action.value[:100]}"
        rep_penalty = calculate_repetition_penalty(action_key, self._action_history)
        self._action_history.append(action_key)

        # --- Phase skip detection ---
        skip_penalty = self._check_phase_skip(action.action_type)

        # --- Execute task-specific logic ---
        obs, task_reward, task_done = self._execute_action(action)

        # --- Compute dense reward ---
        step_pen = calculate_step_penalty(self._step_count, self.ideal_steps)
        reasoning_bonus = evaluate_reasoning(action.reasoning)
        early_bonus = calculate_early_bonus(task_done, self._step_count, self.ideal_steps)
        # Ensure early_bonus is always > 0 for Reward field constraint
        if early_bonus <= 0.0:
            early_bonus = 0.001

        raw = task_reward.breakdown.correctness * 0.6 + task_reward.breakdown.progress * 0.4
        final = clamp_score(
            raw
            + reasoning_bonus
            + early_bonus
            - step_pen
            - rep_penalty
            - skip_penalty
            - task_reward.penalties.invalid_action_penalty
        )

        reward = Reward(
            score=final,
            feedback=task_reward.feedback,
            breakdown=RewardBreakdown(
                correctness=task_reward.breakdown.correctness,
                reasoning_quality=reasoning_bonus * 10,  # normalise to 0-1
                progress=task_reward.breakdown.progress,
            ),
            penalties=RewardPenalties(
                step_penalty=step_pen,
                invalid_action_penalty=task_reward.penalties.invalid_action_penalty,
                repetition_penalty=rep_penalty,
                skip_penalty=skip_penalty,
            ),
            early_bonus=early_bonus,
        )

        # --- Update phase ---
        self._advance_phase(action.action_type)

        # --- Auto-terminate at max_steps ---
        if self._step_count >= self.max_steps:
            task_done = True

        self._done = task_done
        obs.phase = self._current_phase
        obs.step = self._step_count
        self._last_observation = obs

        # --- Trace logging ---
        self._trace.append({
            "step": self._step_count,
            "action": action.model_dump(),
            "reward": reward.model_dump(),
            "observation_summary": obs.instructions[:200],
            "penalties": reward.penalties.model_dump(),
            "cumulative_score": sum(t.get("reward", {}).get("score", 0) for t in self._trace) + final,
        })

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
            info={
                "step": self._step_count,
                "phase": self._current_phase,
                "completed_phases": list(self._completed_phases),
            },
        )

    def state(self) -> State:
        """Return current episode state. Typed Pydantic model."""
        return State(
            episode_id=self._episode_id,
            step_count=self._step_count,
            task_name=self.task_name,
            max_steps=self.max_steps,
            ideal_steps=self.ideal_steps,
            phase=self._current_phase,
            completed_phases=list(self._completed_phases),
            done=self._done,
            trace=list(self._trace),
        )

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _make_invalid_action_result(self, message: str) -> StepResult:
        """Return a StepResult for an invalid / rejected action."""
        reward = Reward(
            score=clamp_score(0.0),
            feedback=f"❌ Action rejected: {message}",
            penalties=RewardPenalties(invalid_action_penalty=0.2),
        )
        obs = self._last_observation or self._get_initial_observation()
        obs.feedback = message
        obs.step = self._step_count

        self._trace.append({
            "step": self._step_count,
            "action": {"rejected": True, "reason": message},
            "reward": reward.model_dump(),
            "observation_summary": message[:200],
            "penalties": reward.penalties.model_dump(),
            "cumulative_score": sum(t.get("reward", {}).get("score", 0) for t in self._trace),
        })

        # Auto-terminate if at max steps
        if self._step_count >= self.max_steps:
            self._done = True

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
            info={"error": "invalid_action", "message": message},
        )

    def _check_phase_skip(self, action_type: str) -> float:
        """
        Penalise skipping a required workflow phase OR going backwards.
        Returns penalty amount (>= 0.001, never 0.0).
        """
        phases = self._get_phase_order()
        if not phases:
            return 0.001
        
        # Find expected phase
        expected_idx = len(self._completed_phases)
        if expected_idx >= len(phases):
            return 0.001
        expected_phase = phases[expected_idx]
        
        # If the action matches a later phase, it's a skip (forward jump)
        if action_type in phases:
            action_idx = phases.index(action_type)
            if action_idx > expected_idx:
                return 0.15  # Skip penalty
            # NEW: Penalize going backwards to completed phases
            if action_type in self._completed_phases:
                return 0.10  # Backward movement penalty
        return 0.001

    def _advance_phase(self, action_type: str) -> None:
        """
        Move to the next phase if action matches current phase.
        Enforces strict forward-only progression.
        """
        phases = self._get_phase_order()
        if action_type == self._current_phase and action_type not in self._completed_phases:
            self._completed_phases.append(action_type)
            next_idx = phases.index(action_type) + 1 if action_type in phases else 0
            if next_idx < len(phases):
                self._current_phase = phases[next_idx]
            else:
                self._current_phase = "completed"
        # Note: Backward movement is now penalized but not blocked,
        # allowing agents to correct mistakes with a cost

    # -------------------------------------------------------------------
    # Abstract methods (subclasses must implement)
    # -------------------------------------------------------------------

    @abstractmethod
    def _get_initial_observation(self) -> Observation:
        """Return the initial observation for this task."""
        ...

    @abstractmethod
    def _execute_action(self, action: Action) -> Tuple[Observation, Reward, bool]:
        """
        Execute a validated action. Return (observation, reward, done).
        The reward here carries task-specific correctness/progress scores;
        the base class adds penalties/bonuses on top.
        """
        ...

    @abstractmethod
    def _get_valid_action_types(self) -> List[str]:
        """Return list of valid action_type strings for the current phase."""
        ...

    @abstractmethod
    def _get_phase_order(self) -> List[str]:
        """Return ordered list of workflow phases for this task."""
        ...
