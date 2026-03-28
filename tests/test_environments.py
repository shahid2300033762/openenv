"""Tests for all task environments."""

import pytest
from tasks.email_triage.environment import EmailTriageEnvironment
from tasks.data_cleaning.environment import DataCleaningEnvironment
from tasks.code_review.environment import CodeReviewEnvironment
from models import Action, Observation, StepResult


class TestAllEnvironments:
    """Test common interface across all environments."""

    @pytest.fixture
    def environments(self):
        """Fixture providing all environment instances."""
        return [
            EmailTriageEnvironment(),
            DataCleaningEnvironment(),
            CodeReviewEnvironment()
        ]

    def test_reset_returns_observation(self, environments):
        """Test all environments return Observation on reset."""
        for env in environments:
            obs = env.reset()
            assert isinstance(obs, Observation)
            assert obs.step == 0

    def test_reset_is_deterministic(self, environments):
        """Test reset produces same results."""
        for env_class in [EmailTriageEnvironment, DataCleaningEnvironment, CodeReviewEnvironment]:
            env1 = env_class()
            env2 = env_class()
            obs1 = env1.reset()
            obs2 = env2.reset()
            assert obs1.data == obs2.data

    def test_step_returns_step_result(self, environments):
        """Test step returns StepResult."""
        for env in environments:
            obs = env.reset()
            if obs.available_actions:
                action = Action(
                    action_type=obs.available_actions[0],
                    value="test",
                    reasoning="test"
                )
                result = env.step(action)
                assert isinstance(result, StepResult)

    def test_max_steps_termination(self, environments):
        """Test environments terminate at max_steps."""
        for env in environments:
            env.reset()
            for _ in range(env.max_steps + 1):
                result = env.step(Action(
                    action_type="classify",
                    value="test",
                    reasoning="test"
                ))
            assert result.done

    def test_state_method(self, environments):
        """Test state() method works."""
        for env in environments:
            env.reset()
            state = env.state()
            assert state.task_name == env.task_name
            assert state.max_steps == env.max_steps


class TestEmailTriageEnvironment:
    """Specific tests for Email Triage."""

    def test_workflow_phases(self):
        """Test phase progression."""
        env = EmailTriageEnvironment()
        obs = env.reset()
        assert obs.phase == "classify"
        
        result = env.step(Action(
            action_type="classify",
            value="complaint",
            reasoning="test"
        ))
        assert result.observation.phase == "prioritize"

    def test_complete_task(self):
        """Test completing full email triage."""
        env = EmailTriageEnvironment()
        env.reset()
        
        env.step(Action(action_type="classify", value="complaint", reasoning="test"))
        env.step(Action(action_type="prioritize", value="high", reasoning="test"))
        result = env.step(Action(
            action_type="respond",
            value="Thank you for contacting us.",
            reasoning="test"
        ))
        assert result.done


class TestDataCleaningEnvironment:
    """Specific tests for Data Cleaning."""

    def test_data_provided(self):
        """Test data is provided on reset."""
        env = DataCleaningEnvironment()
        obs = env.reset()
        assert len(obs.data) > 0

    def test_cleaning_actions(self):
        """Test data cleaning actions."""
        env = DataCleaningEnvironment()
        env.reset()
        
        action = Action(
            action_type="fix_missing",
            target="column1",
            value="mean",
            reasoning="Fill with mean"
        )
        result = env.step(action)
        assert isinstance(result, StepResult)


class TestCodeReviewEnvironment:
    """Specific tests for Code Review."""

    def test_code_provided(self):
        """Test code snippet is provided."""
        env = CodeReviewEnvironment()
        obs = env.reset()
        assert len(obs.data) > 0
        assert "def " in obs.data or "function " in obs.data or "class " in obs.data

    def test_identify_issue(self):
        """Test identifying issues."""
        env = CodeReviewEnvironment()
        env.reset()
        
        action = Action(
            action_type="identify_issue",
            value="Missing error handling",
            reasoning="No try-catch block"
        )
        result = env.step(action)
        assert isinstance(result, StepResult)

    def test_suggest_fix(self):
        """Test suggesting fixes."""
        env = CodeReviewEnvironment()
        env.reset()
        
        # First identify
        env.step(Action(
            action_type="identify_issue",
            value="Bug in logic",
            reasoning="test"
        ))
        
        # Then fix
        result = env.step(Action(
            action_type="suggest_fix",
            value="Add null check",
            reasoning="test"
        ))
        assert isinstance(result, StepResult)


# Integration tests
class TestOpenEnvCompliance:
    """Test OpenEnv specification compliance."""

    def test_openenv_yaml_exists(self):
        """Test openenv.yaml file exists."""
        import os
        assert os.path.exists("openenv.yaml")

    def test_validation_passes(self):
        """Test main.py validation."""
        from main import validate_manifest
        assert validate_manifest() is True

    def test_all_tasks_defined(self):
        """Test all tasks are defined in manifest."""
        import yaml
        with open("openenv.yaml") as f:
            manifest = yaml.safe_load(f)
        task_names = [t["name"] for t in manifest["tasks"]]
        assert "email_triage" in task_names
        assert "data_cleaning" in task_names
        assert "code_review" in task_names
