"""
Baseline agent using OpenAI API.

Reads OPENAI_API_KEY from environment variables.
Runs step-by-step through each environment with structured, task-aware prompts
that include instructions, previous observations, and feedback.
Produces reproducible, deterministic scores.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from models import Action


def _get_openai_client():
    """Lazy-load OpenAI client with competition-required environment variables."""
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        raise ImportError("openai not found.")

    # Strict environment variable check for competition
    try:
        api_key = os.environ["API_KEY"]
        base_url = os.environ["API_BASE_URL"]
        return OpenAI(api_key=api_key, base_url=base_url)
    except KeyError as e:
        raise ValueError(f"Environment variable {e} must be set for competition evaluation.")


def build_prompt(
    task_name: str,
    observation_instructions: str,
    observation_context: str,
    observation_data: str,
    observation_feedback: str,
    available_actions: List[str],
    step: int,
    history: List[Dict[str, Any]],
) -> str:
    """
    Build a structured, task-aware prompt for the LLM.
    Includes: instructions, context, data, previous observations, feedback.
    """
    parts = [
        f"## Task: {task_name} (Step {step})\n",
        f"### Instructions\n{observation_instructions}\n",
    ]

    if observation_context:
        parts.append(f"### Context\n{observation_context}\n")

    if observation_data:
        # Truncate very long data to stay within context limits
        data_preview = observation_data[:3000]
        if len(observation_data) > 3000:
            data_preview += "\n... [truncated]"
        parts.append(f"### Data\n```\n{data_preview}\n```\n")

    if observation_feedback:
        parts.append(f"### Feedback from Previous Step\n{observation_feedback}\n")

    if history:
        parts.append("### Previous Actions")
        for h in history[-5:]:  # Last 5 actions for context
            parts.append(
                f"- Step {h.get('step', '?')}: "
                f"{h.get('action_type', '?')} -> score: {h.get('score', '?')}"
            )
        parts.append("")

    if available_actions:
        parts.append(f"### Available Actions: {', '.join(available_actions)}\n")

    parts.append(
        "### Your Response\n"
        "Respond with a JSON object containing:\n"
        '- "action_type": one of the available actions\n'
        '- "target": what the action targets\n'
        '- "value": the content/value for the action\n'
        '- "reasoning": your detailed reasoning for this action\n'
        "\nRespond ONLY with valid JSON, no markdown fences."
    )

    return "\n".join(parts)


def parse_llm_response(response_text: str, available_actions: List[str]) -> Action:
    """
    Parse LLM response into an Action.
    Handles common formatting issues (markdown fences, extra text).
    """
    text = response_text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(
            l for l in lines if not l.strip().startswith("```")
        )

    # Try to extract JSON
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        import re
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

    action_type = data.get("action_type", available_actions[0] if available_actions else "")
    target = data.get("target", "")
    value = data.get("value", "")
    reasoning = data.get("reasoning", "Based on the current task context and instructions.")

    return Action(
        action_type=action_type,
        target=str(target),
        value=str(value),
        reasoning=str(reasoning) if reasoning else "Agent analysis of the current task.",
    )


def run_baseline_agent(env, task_name: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Run the baseline OpenAI agent through an environment.

    Args:
        env: An OpenEnv-compliant environment instance
        task_name: Name of the task for prompt context
        verbose: Print step-by-step output

    Returns:
        Dict with final_score, steps, trace
    """
    client = _get_openai_client()
    history: List[Dict[str, Any]] = []

    # Reset environment
    obs = env.reset()
    total_reward = 0.0
    step = 0
    
    # Required [START] logging format for competition
    print(f"[START] task={task_name}", flush=True)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Baseline Agent - {task_name}")
        print(f"{'='*60}")

    while True:
        step += 1

        # Build structured prompt
        prompt = build_prompt(
            task_name=task_name,
            observation_instructions=obs.instructions,
            observation_context=obs.context,
            observation_data=obs.data,
            observation_feedback=obs.feedback,
            available_actions=obs.available_actions,
            step=step,
            history=history,
        )

        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model=os.environ.get("MODEL_NAME", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI agent completing professional tasks. "
                            "Follow the instructions carefully and respond with valid JSON. "
                            "Provide detailed reasoning for every action."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,  # Deterministic
                max_tokens=1000,
            )
            llm_text = response.choices[0].message.content or ""
        except Exception as e:
            if verbose:
                print(f"  ⚠ OpenAI API error: {e}")
            llm_text = json.dumps({
                "action_type": obs.available_actions[0] if obs.available_actions else "unknown",
                "target": "",
                "value": "Fallback action due to API error",
                "reasoning": f"API call failed: {e}",
            })

        # Parse response
        action = parse_llm_response(llm_text, obs.available_actions)

        # Execute step
        result = env.step(action)
        obs = result.observation
        reward = result.reward
        done = result.done

        total_reward += reward.score
        
        # Required [STEP] logging format for competition
        print(f"[STEP] step={step} action={action.action_type} reward={reward.score:.4f} done={done}", flush=True)

        # Track history
        history.append({
            "step": step,
            "action_type": action.action_type,
            "value": action.value[:100],
            "score": reward.score,
            "feedback": reward.feedback[:200],
        })

        if verbose:
            print(f"\n  Step {step}: {action.action_type}")
            print(f"    Score: {reward.score:.3f} | Total: {total_reward:.3f}")
            print(f"    Feedback: {reward.feedback[:150]}")

        if done:
            break

    avg_reward = total_reward / max(1, step)
    
    # Required [END] logging format for competition
    print(f"[END] task={task_name} total_reward={total_reward:.4f} steps={step}", flush=True)

    if verbose:
        print(f"\n  {'─'*40}")
        print(f"  Final: {step} steps | Avg reward: {avg_reward:.3f}")
        print(f"  Total reward: {total_reward:.3f}")
        print(f"{'='*60}\n")

    return {
        "task_name": task_name,
        "total_steps": step,
        "total_reward": round(total_reward, 4),
        "avg_reward": round(avg_reward, 4),
        "trace": history,
    }


def run_random_baseline(env, task_name: str, verbose: bool = True, suppress_markers: bool = False) -> Dict[str, Any]:
    """
    Run a deterministic heuristic baseline (no LLM required).
    Uses fixed, reasonable actions for each task.
    """
    env.reset()  # Initialize environment
    total_reward = 0.0
    step = 0
    history: List[Dict[str, Any]] = []
    
    # Required logging format for competition
    if not suppress_markers:
        print(f"[START] task={task_name}", flush=True)

    # Pre-defined deterministic actions per task
    HEURISTIC_ACTIONS = {
        "email_triage": [
            Action(action_type="classify", target="email", value="complaint",
                   reasoning="The email mentions billing issues and frustration, suggesting a complaint."),
            Action(action_type="prioritize", target="email", value="high",
                   reasoning="Billing complaints should be high priority to retain the customer."),
            Action(action_type="respond", target="email",
                   value="Thank you for reaching out. We sincerely apologize for the inconvenience. Our billing team will investigate this immediately and process any necessary corrections. You should see a resolution within 24 hours.",
                   reasoning="A professional response should acknowledge, apologize, and provide actionable next steps."),
        ],
        "data_cleaning": [
            Action(action_type="fix_missing", target="dataset", value="fill_default",
                   reasoning="Missing values should be filled with sensible defaults to preserve data integrity."),
            Action(action_type="remove_duplicates", target="dataset", value="deduplicate",
                   reasoning="Duplicate rows waste storage and skew analysis; removing them is standard practice."),
            Action(action_type="normalize_casing", target="dataset", value="title_case",
                   reasoning="Consistent casing ensures reliable grouping and aggregation in downstream queries."),
            Action(action_type="fix_format", target="dataset", value="standardize",
                   reasoning="Standardizing date/email/zip formats prevents parsing errors in production."),
        ],
        "code_review": [
            Action(action_type="identify_issue", target="code", value="SQL injection vulnerability — user input directly interpolated into query",
                   reasoning="The code uses f-strings to build SQL queries from request parameters, creating a critical security risk."),
            Action(action_type="identify_issue", target="code", value="Password stored and compared in plain text — no hashing",
                   reasoning="Storing passwords in plain text is a severe security violation. Hashing with salt is required."),
            Action(action_type="identify_issue", target="code", value="No input validation — username/password could be None or empty",
                   reasoning="Lack of validation can lead to NullPointerExceptions or logic errors when credentials are missing."),
            Action(action_type="identify_issue", target="code", value="is_admin flag read directly from DB without verification",
                   reasoning="Implicitly trusting role flags from the database without a secure role-based access control system is risky."),
            Action(action_type="suggest_fix", target="code", value="Use parameterized queries or prepared statements",
                   reasoning="Parameterized queries prevent SQL injection by treating input as data rather than executable code."),
            Action(action_type="suggest_fix", target="code", value="Hash passwords with bcrypt or argon2",
                   reasoning="Strong hashing algorithms provide one-way protection for user credentials."),
            Action(action_type="optimize_code", target="code", value="Implement input validation, use type hints, and add proper error handling with try/except blocks to improve readability, security, and performance.",
                   reasoning="General code quality improvements ensure maintainability and robustness."),
        ],
        "incident_response": [
            Action(action_type="detect", target="incident", value="sql_injection",
                   reasoning="Logs show WAF alerts and database errors matching SQL injection patterns on the login endpoint."),
            Action(action_type="analyze", target="indicators", value="sql syntax in login payload",
                   reasoning="Found malicious SQL fragments in the request payload logs."),
            Action(action_type="analyze", target="indicators", value="authentication bypass using OR 1=1",
                   reasoning="Detected classic authentication bypass attempt in the authentication logs."),
            Action(action_type="analyze", target="indicators", value="unauthorized data access",
                   reasoning="Admin session was established from the attacker's IP followed by large data queries."),
            Action(action_type="analyze", target="indicators", value="large data export following breach",
                   reasoning="A data export of ~15,000 records was initiated by the compromised admin user."),
            Action(action_type="contain", target="threat", value="block source IP 185.220.101.42",
                   reasoning="Blocking the source IP stops further communication from the attacker."),
            Action(action_type="contain", target="threat", value="invalidate session f3a7b9c2",
                   reasoning="Terminating the compromised session prevents further unauthorized access."),
            Action(action_type="remediate", target="systems", value="implement parameterized queries",
                   reasoning="Fixing the root cause prevents future SQL injection attacks."),
            Action(action_type="remediate", target="systems", value="add rate limiting to API endpoints",
                   reasoning="Rate limiting mitigates brute force and automated exploitation attempts."),
            Action(action_type="document", target="incident", value="SUMMARY: SQL injection attack on /api/users/login from IP 185.220.101.42. TIMELINE: Detected at 09:15, contained within 5 minutes. IMPACT: unauthorized local session for admin user and large data export of ~15,000 records. LESSONS: Implement parameterized queries and WAF rules to block SQL patterns. Blocked malicious IP and invalidated compromised sessions.",
                   reasoning="The final report summarizes the incident findings, actions, and remediation steps."),
        ],
    }

    actions = HEURISTIC_ACTIONS.get(task_name, [])

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Heuristic Baseline - {task_name}")
        print(f"{'='*60}")

    for action in actions:
        step += 1
        result = env.step(action)
        reward = result.reward
        done = result.done
        total_reward += reward.score

        history.append({
            "step": step,
            "action_type": action.action_type,
            "value": action.value,
            "score": reward.score,
        })

        # Required [STEP] logging format for competition
        print(f"[STEP] step={step} action={action.action_type} reward={reward.score:.4f} done={done}", flush=True)

        if verbose:
            print(f"  Step {step}: {action.action_type} -> {reward.score:.3f}")

        if done:
            break

    avg_reward = total_reward / max(1, step)
    
    # Required [END] logging format for competition
    print(f"[END] task={task_name} total_reward={total_reward:.4f} steps={step}", flush=True)

    if verbose:
        print(f"  Final: {step} steps | Avg: {avg_reward:.3f} | Total: {total_reward:.3f}")
        print(f"{'='*60}\n")

    return {
        "task_name": task_name,
        "total_steps": step,
        "total_reward": round(total_reward, 4),
        "avg_reward": round(avg_reward, 4),
        "trace": history,
    }
