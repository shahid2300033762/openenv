"""
OpenEnv Final Submission Inference Script.

This script is the entry point for the competition evaluation.
It reads from environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN.
Uses the OpenAI client as required.
"""

import json
import os
import sys
from typing import Any, Dict, List

# Ensure project modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Action, TaskName
from tasks.email_triage.environment import EmailTriageEnvironment
from tasks.data_cleaning.environment import DataCleaningEnvironment
from tasks.code_review.environment import CodeReviewEnvironment
from tasks.incident_response.environment import IncidentResponseEnvironment


def get_openai_client():
    """Configure OpenAI client with competition-required environment variables."""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Missing dependencies. Install: pip install openai python-dotenv")
        sys.exit(1)

    api_base_url = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1/")
    model_name = os.environ.get("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("OPENAI_API_KEY")

    if not hf_token:
        print("WARNING: HF_TOKEN (or OPENAI_API_KEY) not set. Falling back to heuristic agent.")
        return None, model_name

    client = OpenAI(
        base_url=api_base_url,
        api_key=hf_token
    )
    return client, model_name


def build_prompt(
    task_name: str,
    obs: Any,
    step: int,
    history: List[Dict[str, Any]],
) -> str:
    """Standardized prompt building for the OpenEnv tasks."""
    parts = [
        f"## Task: {task_name} (Step {step})\n",
        f"### Instructions\n{obs.instructions}\n",
    ]

    if obs.context:
        parts.append(f"### Context\n{obs.context}\n")
    if obs.data:
        parts.append(f"### Data\n```\n{obs.data[:2000]}\n```\n")
    if obs.feedback:
        parts.append(f"### Feedback\n{obs.feedback}\n")

    if obs.available_actions:
        parts.append(f"### Available Actions: {', '.join(obs.available_actions)}\n")

    parts.append(
        "### Your Response\n"
        "Respond ONLY with a JSON object containing 'action_type', 'target', 'value', and 'reasoning'.\n"
        "NO markdown formatting around the JSON."
    )
    return "\n".join(parts)


def parse_response(text: str, default_action: str) -> Action:
    """Robust JSON parsing for LLM responses."""
    try:
        # Simple extraction if LLM adds text
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(text)
    except Exception:
        return Action(action_type=default_action, reasoning="Fallback due to parsing error", value="")

    return Action(
        action_type=data.get("action_type", default_action),
        target=str(data.get("target", "")),
        value=str(data.get("value", "")),
        reasoning=str(data.get("reasoning", "Agent reasoning process."))
    )


def run_episode(env, task_name: str, client, model_name: str):
    """Run a single episode from start to finish."""
    obs = env.reset()
    total_reward = 0.0
    step = 0
    history = []

    print(f"\n--- Running Task: {task_name} ---")

    while True:
        step += 1
        if client:
            prompt = build_prompt(task_name, obs, step, history)
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                action = parse_response(response.choices[0].message.content, obs.available_actions[0])
            except Exception as e:
                print(f"API Error: {e}")
                from baseline.agent import run_random_baseline
                # Fallback to internal heuristic if API fails mid-task
                return run_random_baseline(env, task_name, verbose=False)
        else:
            # Fallback to internal heuristic if no client
            from baseline.agent import run_random_baseline
            return run_random_baseline(env, task_name, verbose=False)

        result = env.step(action)
        obs = result.observation
        total_reward += result.reward.score
        
        print(f"Step {step}: {action.action_type} | Reward: {result.reward.score:.2f}")
        
        if result.done or step >= 10:
            break

    return {"total_reward": total_reward, "steps": step}


def main():
    client, model_name = get_openai_client()
    
    tasks = {
        "email_triage": EmailTriageEnvironment(),
        "data_cleaning": DataCleaningEnvironment(),
        "code_review": CodeReviewEnvironment(),
        "incident_response": IncidentResponseEnvironment()
    }

    results = {}
    for name, env in tasks.items():
        results[name] = run_episode(env, name, client, model_name)

    print("\n" + "="*40)
    print("FINAL SUBMISSION RESULTS")
    print("="*40)
    for name, res in results.items():
        print(f"{name:20}: Score {res['total_reward']:.2f} in {res['steps']} steps")


if __name__ == "__main__":
    main()
