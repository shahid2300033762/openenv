"""
Core Pydantic models for the OpenEnv AI Evaluation Environment.

All environment returns are strictly typed — no raw dicts allowed.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from grading.utils import clamp_score, clamp_score_tree


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskName(str, Enum):
    EMAIL_TRIAGE = "email_triage"
    DATA_CLEANING = "data_cleaning"
    CODE_REVIEW = "code_review"


class ActionType(str, Enum):
    # Email Triage actions
    CLASSIFY = "classify"
    PRIORITIZE = "prioritize"
    RESPOND = "respond"
    # Data Cleaning actions
    FIX_MISSING = "fix_missing"
    REMOVE_DUPLICATES = "remove_duplicates"
    NORMALIZE_CASING = "normalize_casing"
    FIX_FORMAT = "fix_format"
    # Code Review actions
    IDENTIFY_ISSUE = "identify_issue"
    SUGGEST_FIX = "suggest_fix"
    OPTIMIZE_CODE = "optimize_code"
    # Incident Response actions
    DETECT = "detect"
    ANALYZE = "analyze"
    CONTAIN = "contain"
    REMEDIATE = "remediate"
    DOCUMENT = "document"


class Phase(str, Enum):
    """Workflow phases for state-transition enforcement."""
    # Email
    CLASSIFY = "classify"
    PRIORITIZE = "prioritize"
    RESPOND = "respond"
    # Data Cleaning
    FIX_MISSING = "fix_missing"
    REMOVE_DUPLICATES = "remove_duplicates"
    NORMALIZE_CASING = "normalize_casing"
    FIX_FORMAT = "fix_format"
    # Code Review
    IDENTIFY_ISSUE = "identify_issue"
    SUGGEST_FIX = "suggest_fix"
    OPTIMIZE_CODE = "optimize_code"
    # Incident Response
    DETECT = "detect"
    ANALYZE = "analyze"
    CONTAIN = "contain"
    REMEDIATE = "remediate"
    DOCUMENT = "document"
    # Terminal
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    """Returned by reset() and step(). Typed Pydantic model — never a raw dict."""

    task_name: str = Field(..., description="Name of the current task")
    step: int = Field(0, ge=0, description="Current step number")
    instructions: str = Field(..., description="What the agent should do next")
    context: str = Field("", description="Background context for the task")
    data: str = Field("", description="Current data to work with")
    feedback: str = Field("", description="Feedback from the previous action")
    available_actions: List[str] = Field(
        default_factory=list,
        description="Valid action types for the current phase",
    )
    phase: str = Field("", description="Current workflow phase")


class Action(BaseModel):
    """Agent's action. Must include reasoning field."""

    action_type: str = Field(..., description="Type of action to perform")
    target: str = Field("", description="Target of the action")
    value: str = Field("", description="Value / content of the action")
    reasoning: str = Field(
        ...,
        min_length=1,
        description="Agent's reasoning for this action (REQUIRED)",
    )

    @field_validator("reasoning")
    @classmethod
    def reasoning_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reasoning must not be empty")
        return v


class RewardBreakdown(BaseModel):
    """Itemised score components inside a Reward."""

    correctness: float = Field(0.001, description="Clamped to (0, 1)")
    reasoning_quality: float = Field(0.001, description="Clamped to (0, 1)")
    progress: float = Field(0.001, description="Clamped to (0, 1)")

    @field_validator("correctness", "reasoning_quality", "progress", mode="before")
    @classmethod
    def strict_bounds(cls, v: float) -> float:
        """Ensure all scores are strictly in (0, 1)."""
        return clamp_score(float(v))

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Clamp all float values on serialisation."""
        raw = super().model_dump(**kwargs)
        return clamp_score_tree(raw)


class RewardPenalties(BaseModel):
    """Itemised penalties inside a Reward."""

    step_penalty: float = Field(0.001, description="Clamped to (0, 1)")
    invalid_action_penalty: float = Field(0.001, description="Clamped to (0, 1)")
    repetition_penalty: float = Field(0.001, description="Clamped to (0, 1)")
    skip_penalty: float = Field(0.001, description="Clamped to (0, 1)")

    @field_validator("step_penalty", "invalid_action_penalty", "repetition_penalty", "skip_penalty", mode="before")
    @classmethod
    def strict_bounds(cls, v: float) -> float:
        """Ensure all penalty values are strictly in (0, 1)."""
        return clamp_score(float(v))

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Clamp all float values on serialisation."""
        raw = super().model_dump(**kwargs)
        return clamp_score_tree(raw)


class Reward(BaseModel):
    """Dense reward returned at every step. Typed, never a raw dict."""

    score: float = Field(..., description="Final clamped score - strictly in (0, 1)")
    feedback: str = Field("", description="Human-readable grader feedback")
    breakdown: RewardBreakdown = Field(default_factory=RewardBreakdown)
    penalties: RewardPenalties = Field(default_factory=RewardPenalties)
    early_bonus: float = Field(0.001, ge=0.001, le=0.1)

    @field_validator("score", mode="before")
    @classmethod
    def score_strict_bounds(cls, v: float) -> float:
        """Competition validator requires scores strictly in (0, 1)."""
        return clamp_score(float(v))
    
    @field_validator("early_bonus", mode="before")
    @classmethod
    def early_bonus_strict_bounds(cls, v: float) -> float:
        """Ensure early_bonus is strictly > 0."""
        if v <= 0.0:
            return 0.001
        if v > 0.1:
            return 0.1
        return v

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override to clamp ALL floats to strict (0, 1) on serialisation."""
        raw = super().model_dump(**kwargs)
        return clamp_score_tree(raw)


class State(BaseModel):
    """Returned by state(). Full episode metadata."""

    episode_id: str = Field(..., description="Unique episode ID")
    step_count: int = Field(0, ge=0)
    task_name: str = Field(...)
    max_steps: int = Field(...)
    ideal_steps: int = Field(...)
    phase: str = Field("")
    completed_phases: List[str] = Field(default_factory=list)
    done: bool = Field(False)
    trace: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Safety utility: recursive float clamping for serialised output
# ---------------------------------------------------------------------------

def _clamp_all_floats(obj: Any, eps: float = 0.001) -> Any:
    """Recursively clamp every numeric score in a nested dict/list to strict (0, 1).
    
    This is the FINAL safety net.  The competition validator requires
    every task score to be strictly between 0 and 1 (not 0.0 and not 1.0).
    By clamping at the serialisation layer, we guarantee compliance no
    matter what upstream arithmetic produces.
    """
    return clamp_score_tree(obj, eps)


class StepResult(BaseModel):
    """Typed return of step(). Contains observation, reward, done flag, and info."""

    observation: Observation
    reward: Reward
    done: bool = Field(False)
    info: Dict[str, Any] = Field(default_factory=dict)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override to clamp ALL floats in serialised output to strict (0, 1)."""
        raw = super().model_dump(**kwargs)
        return _clamp_all_floats(raw)
