"""
OpenEnv Workflow Evaluation - Inference Script

This script runs baseline evaluations on all tasks using the OpenAI API.
Required environment variables:
  - API_BASE_URL: The API endpoint for the LLM
  - MODEL_NAME: The model identifier to use for inference
  - HF_TOKEN: Your Hugging Face / API key

Runtime: < 20 minutes on 2 vCPU, 8GB RAM
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Action, Observation
from main import create_environment


def get_env_config() -> Dict[str, str]:
    """
    Get required environment variables.
    
    Required:
      - API_BASE_URL: The API endpoint for the LLM
      - MODEL_NAME: The model identifier to use for inference  
      - HF_TOKEN: Your Hugging Face / API key (used as OpenAI API key)
    
    Returns:
        Dict with api_base_url, model_name, api_key
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_base_url = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("OPENAI_API_KEY", "")
    
    if not api_key:
        print("⚠ WARNING: HF_TOKEN or OPENAI_API_KEY not set. Using fallback heuristic baseline.")
        print("  To use LLM-based inference, set environment variables:")
        print("    - API_BASE_URL (default: https://api.openai.com/v1)")
        print("    - MODEL_NAME (default: gpt-4o-mini)")
        print("    - HF_TOKEN (or OPENAI_API_KEY)")
    
    return {
        "api_base_url": api_base_url,
        "model_name": model_name,
        "api_key": api_key,
    }


def get_openai_client(config: Dict[str, str]):
    """
    Create OpenAI client with configured base URL and API key.
    
    Uses OpenAI Client as required by submission guidelines.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package required for inference. "
            "Install with: pip install openai python-dotenv"
        )
    
    if not config["api_key"]:
        return None
    
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["api_base_url"],
    )


def build_prompt(
    task_name: str,
    observation: Observation,
    step: int,
    history: List[Dict[str, Any]],
) -> str:
    """Build structured prompt for the LLM."""
    parts = [
        f"## Task: {task_name} (Step {step})\n",
        f"### Instructions\n{observation.instructions}\n",
    ]
    
    if observation.context:
        parts.append(f"### Context\n{observation.context}\n")
    
    if observation.data:
        # Truncate long data to stay within token limits
        data_preview = observation.data[:3000]
        if len(observation.data) > 3000:
            data_preview += "\n... [truncated]"
        parts.append(f"### Data\n```\n{data_preview}\n```\n")
    
    if observation.feedback:
        parts.append(f"### Feedback\n{observation.feedback}\n")
    
    if history:
        parts.append("### Previous Actions")
        for h in history[-5:]:
            parts.append(
                f"- Step {h['step']}: {h['action_type']} -> score: {h['score']:.3f}"
            )
        parts.append("")
    
    if observation.available_actions:
        parts.append(f"### Available Actions: {', '.join(observation.available_actions)}\n")
    
    parts.append(
        "### Response\n"
        "Respond with a JSON object:\n"
        '{"action_type": "...", "target": "...", "value": "...", "reasoning": "..."}\n'
        "\nRespond ONLY with valid JSON."
    )
    
    return "\n".join(parts)


def parse_llm_response(response_text: str, available_actions: List[str]) -> Action:
    """Parse LLM JSON response into Action."""
    text = response_text.strip()
    
    # Remove markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.strip().startswith("```"))
    
    # Parse JSON
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from text
        import re
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}
    
    return Action(
        action_type=data.get("action_type", available_actions[0] if available_actions else ""),
        target=str(data.get("target", "")),
        value=str(data.get("value", "")),
        reasoning=str(data.get("reasoning", "Task analysis")),
    )


def run_llm_inference(env, task_name: str, client, model_name: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Run LLM-based inference through an environment.
    
    Args:
        env: OpenEnv-compliant environment
        task_name: Name of the task
        client: OpenAI client instance
        model_name: Model to use for inference
        verbose: Print step-by-step output
    
    Returns:
        Dict with results and scores
    """
    history: List[Dict[str, Any]] = []
    obs = env.reset()
    total_reward = 0.0
    step = 0
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"  Running: {task_name} (Model: {model_name})")
        print(f"{'='*70}")
    
    while True:
        step += 1
        
        # Build prompt
        prompt = build_prompt(task_name, obs, step, history)
        
        # Call LLM
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI agent completing professional tasks. Respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=1000,
            )
            llm_text = response.choices[0].message.content or ""
        except Exception as e:
            if verbose:
                print(f"  ! API error: {e}")
            llm_text = json.dumps({
                "action_type": obs.available_actions[0] if obs.available_actions else "unknown",
                "target": "",
                "value": "Fallback",
                "reasoning": f"API error: {e}",
            })
        
        # Parse and execute
        action = parse_llm_response(llm_text, obs.available_actions)
        result = env.step(action)
        obs = result.observation
        reward = result.reward
        done = result.done
        
        total_reward += reward.score
        history.append({
            "step": step,
            "action_type": action.action_type,
            "value": action.value[:100],
            "score": reward.score,
            "feedback": reward.feedback[:150],
        })
        
        if verbose:
            print(f"  Step {step}: {action.action_type} -> Score: {reward.score:.3f} (Total: {total_reward:.3f})")
        
        if done:
            break
    
    avg_reward = total_reward / max(1, step)
    
    if verbose:
        print(f"  {'─'*50}")
        print(f"  ✓ Completed: {step} steps | Avg: {avg_reward:.3f} | Total: {total_reward:.3f}")
        print(f"{'='*70}\n")
    
    return {
        "task_name": task_name,
        "total_steps": step,
        "total_reward": round(total_reward, 4),
        "avg_reward": round(avg_reward, 4),
        "trace": history,
    }


def run_heuristic_baseline(env, task_name: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Run deterministic heuristic baseline (no LLM required).
    Fast fallback for when API keys are not available.
    """
    from baseline.agent import run_random_baseline
    return run_random_baseline(env, task_name, verbose=verbose)


def main():
    """Main inference script - runs all tasks and produces scores."""
    start_time = time.time()
    
    print("\n" + "="*80)
    print("  OpenEnv Workflow Evaluation - Inference Script")
    print("="*80)
    
    # Get configuration
    config = get_env_config()
    client = get_openai_client(config)
    
    # Task list
    tasks = ["email_triage", "data_cleaning", "code_review", "incident_response"]
    results = []
    
    # Run inference on each task
    for task_name in tasks:
        try:
            env = create_environment(task_name)
            
            if client:
                # LLM-based inference
                result = run_llm_inference(
                    env, 
                    task_name, 
                    client, 
                    config["model_name"],
                    verbose=True
                )
            else:
                # Heuristic fallback
                result = run_heuristic_baseline(env, task_name, verbose=True)
            
            results.append(result)
            
        except Exception as e:
            print(f"! Error running {task_name}: {e}")
            results.append({
                "task_name": task_name,
                "error": str(e),
                "total_steps": 0,
                "total_reward": 0.0,
                "avg_reward": 0.0,
            })
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "="*80)
    print("  INFERENCE SUMMARY")
    print("="*80)
    
    for result in results:
        if "error" in result:
            print(f"  X {result['task_name']}: ERROR - {result['error']}")
        else:
            print(f"  + {result['task_name']}: {result['total_steps']} steps | "
                  f"Avg score: {result['avg_reward']:.3f} | Total: {result['total_reward']:.3f}")
    
    print(f"\n  Runtime: {elapsed:.1f}s (< 20min +)")
    print("="*80)
    
    # Save results
    output_file = "inference_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "config": {
                "api_base_url": config["api_base_url"],
                "model_name": config["model_name"],
                "has_api_key": bool(config["api_key"]),
            },
            "runtime_seconds": round(elapsed, 2),
            "results": results,
        }, f, indent=2)
    
    print(f"\n  Results saved to: {output_file}")
    print("\n  + Inference completed successfully!\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
