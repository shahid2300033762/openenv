#!/usr/bin/env python3
"""
OpenEnv AI Evaluation Environment — CLI Entry Point.

Usage:
    python main.py --all              Run all tasks with heuristic baseline
    python main.py --task email_triage Run a specific task
    python main.py --baseline         Run OpenAI baseline agent (requires OPENAI_API_KEY)
    python main.py --validate         Validate OpenEnv manifest and models
"""

from __future__ import annotations

import argparse
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Action, Observation, Reward, State, StepResult
from tasks.email_triage.environment import EmailTriageEnvironment
from tasks.data_cleaning.environment import DataCleaningEnvironment
from tasks.code_review.environment import CodeReviewEnvironment
from tasks.incident_response.environment import IncidentResponseEnvironment
from baseline.agent import run_random_baseline


def create_environment(task_name: str, **kwargs):
    """Factory function to create task environments."""
    envs = {
        "email_triage": lambda: EmailTriageEnvironment(email_index=kwargs.get("index", 0)),
        "data_cleaning": lambda: DataCleaningEnvironment(),
        "code_review": lambda: CodeReviewEnvironment(snippet_index=kwargs.get("index", 0)),
        "incident_response": lambda: IncidentResponseEnvironment(incident_index=kwargs.get("index", 0)),
    }
    if task_name not in envs:
        raise ValueError(f"Unknown task: {task_name}. Available: {list(envs.keys())}")
    return envs[task_name]()


def validate_manifest():
    """Validate openenv.yaml and models."""
    import yaml

    print("\n  Validating OpenEnv compliance...\n")

    # 1. Check openenv.yaml
    try:
        with open("openenv.yaml", "r") as f:
            manifest = yaml.safe_load(f)
        assert "name" in manifest, "Missing 'name' field"
        assert "version" in manifest, "Missing 'version' field"
        assert "tasks" in manifest, "Missing 'tasks' field"
        assert "observation_space" in manifest, "Missing 'observation_space'"
        assert "action_space" in manifest, "Missing 'action_space'"
        assert "reward" in manifest, "Missing 'reward'"
        print(f"  OK openenv.yaml - valid ({manifest['name']} v{manifest['version']})")
        print(f"     Tasks: {[t['name'] for t in manifest['tasks']]}")
    except Exception as e:
        print(f"  ERR openenv.yaml - {e}")
        return False

    # 2. Check Pydantic models
    try:
        obs = Observation(task_name="test", instructions="test")
        act = Action(action_type="test", value="test", reasoning="test reasoning")
        rew = Reward(score=0.5, feedback="test")
        st = State(episode_id="test", task_name="test", max_steps=5, ideal_steps=3)
        sr = StepResult(observation=obs, reward=rew, done=False)
        print("  OK Pydantic models - all valid")
    except Exception as e:
        print(f"  ERR Pydantic models - {e}")
        return False

    # 3. Check environments implement correct interface
    for task_name in ["email_triage", "data_cleaning", "code_review", "incident_response"]:
        try:
            env = create_environment(task_name)
            obs = env.reset()
            assert isinstance(obs, Observation), f"reset() must return Observation, got {type(obs)}"

            state = env.state()
            assert isinstance(state, State), f"state() must return State, got {type(state)}"

            # Test step with a valid action
            valid_actions = obs.available_actions
            if valid_actions:
                action = Action(
                    action_type=valid_actions[0],
                    value="test value",
                    reasoning="Validation test",
                )
                result = env.step(action)
                assert isinstance(result, StepResult), f"step() must return StepResult"
                assert isinstance(result.observation, Observation)
                assert isinstance(result.reward, Reward)
                assert isinstance(result.done, bool)

            print(f"  OK {task_name} - interface compliant")
        except Exception as e:
            print(f"  ERR {task_name} - {e}")
            return False

    # 4. Determinism check
    print("\n  Determinism check...")
    for task_name in ["email_triage", "data_cleaning", "code_review", "incident_response"]:
        env1 = create_environment(task_name)
        env2 = create_environment(task_name)
        obs1 = env1.reset()
        obs2 = env2.reset()
        assert obs1.data == obs2.data, f"{task_name}: reset() not deterministic"
        assert obs1.instructions == obs2.instructions
    print("  OK All tasks deterministic\n")

    print("OK All validation checks passed!\n")
    return True


def run_task(task_name: str, verbose: bool = True, index: int = 0):
    """Run a single task with the heuristic baseline."""
    env = create_environment(task_name, index=index)
    return run_random_baseline(env, task_name, verbose=verbose)


def run_all_tasks(verbose: bool = True):
    """Run all four tasks and print summary."""
    results = []
    for task_name in ["email_triage", "data_cleaning", "code_review", "incident_response"]:
        result = run_task(task_name, verbose=verbose)
        results.append(result)

    # Print summary table
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    print(f"  {'Task':<20} {'Steps':>6} {'Avg':>8} {'Total':>8}")
    print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*8}")
    for r in results:
        print(f"  {r['task_name']:<20} {r['total_steps']:>6} "
              f"{r['avg_reward']:>8.3f} {r['total_reward']:>8.3f}")
    print("=" * 60)

    overall = sum(r["avg_reward"] for r in results) / len(results)
    print(f"  Overall average reward: {overall:.3f}")
    print("=" * 60 + "\n")

    return results


def run_openai_baseline(verbose: bool = True):
    """Run the OpenAI API baseline agent."""
    from baseline.agent import run_baseline_agent

    results = []
    for task_name in ["email_triage", "data_cleaning", "code_review", "incident_response"]:
        env = create_environment(task_name)
        result = run_baseline_agent(env, task_name, verbose=verbose)
        results.append(result)

    # Print summary
    print("\n" + "=" * 60)
    print("  OPENAI BASELINE RESULTS")
    print("=" * 60)
    print(f"  {'Task':<20} {'Steps':>6} {'Avg':>8} {'Total':>8}")
    print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*8}")
    for r in results:
        print(f"  {r['task_name']:<20} {r['total_steps']:>6} "
              f"{r['avg_reward']:>8.3f} {r['total_reward']:>8.3f}")
    print("=" * 60 + "\n")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="OpenEnv AI Evaluation Environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --all              Run all tasks with heuristic baseline
  python main.py --task email_triage
  python main.py --baseline         Run OpenAI API baseline (needs OPENAI_API_KEY)
  python main.py --validate         Validate OpenEnv compliance
        """,
    )
    parser.add_argument("--task", type=str, help="Run a specific task")
    parser.add_argument("--all", action="store_true", help="Run all tasks")
    parser.add_argument("--baseline", action="store_true", help="Run OpenAI baseline")
    parser.add_argument("--validate", action="store_true", help="Validate environment")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--index", type=int, default=0, help="Task item index")

    args = parser.parse_args()
    verbose = not args.quiet

    if args.validate:
        success = validate_manifest()
        sys.exit(0 if success else 1)

    if args.baseline:
        run_openai_baseline(verbose=verbose)
    elif args.task:
        run_task(args.task, verbose=verbose, index=args.index)
    elif args.all:
        validate_manifest()
        run_all_tasks(verbose=verbose)
    else:
        # Default: validate + run all
        validate_manifest()
        run_all_tasks(verbose=verbose)


if __name__ == "__main__":
    main()
