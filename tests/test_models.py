"""Tests for Pydantic models."""

import pytest
from models import (
    Action, Observation, Reward, RewardBreakdown, RewardPenalties,
    State, StepResult, TaskName, ActionType, Phase
)


class TestModels:
    """Test Pydantic model validation and serialization."""

    def test_observation_creation(self):
        """Test Observation model creation."""
        obs = Observation(
            task_name="test_task",
            step=1,
            instructions="Test instructions",
            context="Test context",
            data="Test data",
            feedback="Test feedback",
            available_actions=["action1", "action2"],
            phase="test_phase"
        )
        assert obs.task_name == "test_task"
        assert obs.step == 1
        assert obs.instructions == "Test instructions"
        assert len(obs.available_actions) == 2

    def test_observation_validation(self):
        """Test Observation validation catches invalid data."""
        with pytest.raises(ValueError):
            Observation(
                task_name="test",
                step=-1,  # Invalid negative step
                instructions="test"
            )

    def test_action_creation(self):
        """Test Action model creation."""
        action = Action(
            action_type="classify",
            value="complaint",
            reasoning="This is a complaint email"
        )
        assert action.action_type == "classify"
        assert action.value == "complaint"
        assert action.reasoning == "This is a complaint email"

    def test_action_with_target(self):
        """Test Action with optional target field."""
        action = Action(
            action_type="fix_missing",
            target="column_name",
            value="mean",
            reasoning="Fill with mean value"
        )
        assert action.target == "column_name"

    def test_reward_creation(self):
        """Test Reward model creation."""
        reward = Reward(
            score=0.85,
            feedback="Good job!",
            breakdown=RewardBreakdown(
                correctness=0.9,
                reasoning_quality=0.8,
                progress=0.85
            ),
            penalties=RewardPenalties(
                step_penalty=0.05,
                invalid_action_penalty=0.0,
                repetition_penalty=0.0,
                skip_penalty=0.0
            )
        )
        assert reward.score == 0.85
        assert reward.breakdown.correctness == 0.9

    def test_reward_score_clamping(self):
        """Test that reward scores are clamped to strict (0, 1) — never exactly 0.0 or 1.0."""
        reward = Reward(score=0.0, feedback="Minimum")
        assert reward.score == 0.001  # Clamped from 0.0 to EPS
        
        reward = Reward(score=1.0, feedback="Maximum")
        assert reward.score == 0.999  # Clamped from 1.0 to 1.0 - EPS
        
        reward = Reward(score=0.5, feedback="Middle")
        assert reward.score == 0.5  # Valid scores unchanged

    def test_state_creation(self):
        """Test State model creation."""
        state = State(
            episode_id="test-episode-123",
            task_name="email_triage",
            step_count=3,
            max_steps=10,
            ideal_steps=5,
            done=False,
            phase="classify",
            completed_phases=["classify"],
            trace=[]
        )
        assert state.episode_id == "test-episode-123"
        assert state.step_count == 3
        assert not state.done

    def test_step_result_creation(self):
        """Test StepResult model creation."""
        obs = Observation(
            task_name="test",
            step=1,
            instructions="test"
        )
        reward = Reward(score=0.5, feedback="OK")
        result = StepResult(
            observation=obs,
            reward=reward,
            done=False,
            info={"test": "value"}
        )
        assert isinstance(result.observation, Observation)
        assert isinstance(result.reward, Reward)
        assert not result.done

    def test_enums(self):
        """Test enum definitions."""
        assert TaskName.EMAIL_TRIAGE == "email_triage"
        assert ActionType.CLASSIFY == "classify"
        assert Phase.CLASSIFY == "classify"

    def test_model_serialization(self):
        """Test models can be serialized to dict."""
        obs = Observation(
            task_name="test",
            step=1,
            instructions="test"
        )
        obs_dict = obs.model_dump()
        assert obs_dict["task_name"] == "test"
        assert obs_dict["step"] == 1

    def test_model_json_serialization(self):
        """Test models can be serialized to JSON."""
        action = Action(
            action_type="classify",
            value="test",
            reasoning="test reasoning"
        )
        json_str = action.model_dump_json()
        assert "classify" in json_str
        assert "test" in json_str
