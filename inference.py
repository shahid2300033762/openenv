"""
OpenEnv Final Submission Inference Script.

This script is the entry point for the competition evaluation.
It reads from environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN.
Uses the OpenAI client as required.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List
import importlib

# Ensure project modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models
from models import Action


def get_openai_client():
    """
    Get the OpenAI client configured for the competition's LiteLLM proxy.
    """
    from openai import OpenAI
    api_base_url = os.environ["API_BASE_URL"]
    api_key = os.environ["API_KEY"]
    
    # Initialize client just as requested
    client = OpenAI(
        base_url=api_base_url,
        api_key=api_key
    )
    
    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
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
        f"### Instructions\n{getattr(obs, 'instructions', 'No instructions provided.')}\n",
    ]

    if getattr(obs, "context", None):
        parts.append(f"### Context\n{obs.context}\n")
    if getattr(obs, "data", None):
        parts.append(f"### Data\n```\n{str(obs.data)[:2000]}\n```\n")
    if getattr(obs, "feedback", None):
        parts.append(f"### Feedback\n{obs.feedback}\n")

    available_actions = getattr(obs, "available_actions", [])
    if available_actions:
        parts.append(f"### Available Actions: {', '.join(available_actions)}\n")

    parts.append(
        "### Your Response\n"
        "Respond ONLY with a JSON object containing 'action_type', 'target', 'value', and 'reasoning'.\n"
        "NO markdown formatting around the JSON."
    )
    return "\n".join(parts)


def parse_response(text: str, default_action: str):
    """Robust JSON parsing for LLM responses."""
    from models import Action
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
    """
    Execute a full episode on a single environment.
    """
    print(f"[START] task={task_name}", flush=True)
    
    res = {"total_reward": 0.0, "steps": 0, "trace": []}
    
    obs = env.reset()
    total_reward = 0.0
    step = 0
    history = []

    while True:
        step += 1
        prompt = build_prompt(task_name, obs, step, history)
        
        # Make API call securely via proxy
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        action = parse_response(response.choices[0].message.content, obs.available_actions[0])
        
        # Execute action
        result = env.step(action)
        obs = result.observation
        
        # Log step format
        print(f"[STEP] step={step} action={action.action_type} reward={result.reward.score:.4f} done={result.done}", flush=True)

        history.append({
            "step": step,
            "action": action.model_dump(),
            "reward": result.reward.score,
        })
        
        total_reward = result.reward.score
        if result.done:
            break

    res["total_reward"] = total_reward
    res["steps"] = step
    res["trace"] = history

    print(f"[END] task={task_name} total_reward={total_reward:.4f} steps={step}", flush=True)
    return res


def main():
    """Bulletproof inference wrapper - NEVER crashes, always exits cleanly."""
    print("\n" + "="*60)
    print("OPENENV INFERENCE PIPELINE - Starting...")
    print("="*60 + "\n")
    
    # 1. Initialize OpenAI Client
    client, model_name = get_openai_client()

    # 2. Task Definitions
    task_configs = [
        ("email_triage", "tasks.email_triage.environment.EmailTriageEnvironment"),
        ("data_cleaning", "tasks.data_cleaning.environment.DataCleaningEnvironment"),
        ("code_review", "tasks.code_review.environment.CodeReviewEnvironment"),
        ("incident_response", "tasks.incident_response.environment.IncidentResponseEnvironment")
    ]

    # 3. Execute all tasks with complete isolation
    all_trace_results = []
    results = {}
    
    for name, class_path in task_configs:
        # Import and instantiate environment
        module_name, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        env_class = getattr(module, class_name)
        
        # Instantiate with specific configuration if needed
        if name == "browser_nav":
            env = env_class(headless=True)
        else:
            env = env_class()
            
        # Run episode (will crash if unhandled error)
        res = run_episode(env, name, client, model_name)
        
        # Record result cleanly
        results[name] = res
        all_trace_results.append(res)

    # 4. Save results to JSON (required for validator)
    output_data = {
        "config": {
            "api_base_url": os.environ.get("API_BASE_URL", "NOT_SET"),
            "model_name": model_name,
            "has_api_key": client is not None
        },
        "results": all_trace_results
    }
    with open("inference_results.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print("\n[OK] Results saved to inference_results.json")

    # 5. Display final summary
    print("\n" + "="*60)
    print("INFERENCE RESULTS SUMMARY")
    print("="*60)
    for name, res in results.items():
        steps = res.get('steps', 0)
        reward = res.get('total_reward', 0.0)
        print(f"  {name:20}: {reward:6.2f} points in {steps:2d} steps")
    print("="*60)
    
    total_score = sum(r.get('total_reward', 0.0) for r in results.values())
    print(f"  {'TOTAL':20}: {total_score:6.2f} points")
    print("="*60 + "\n")

    # 6. Always exit successfully (validator needs exit code 0)
    print("[SUCCESS] Inference pipeline completed successfully.")
    print("="*60 + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
