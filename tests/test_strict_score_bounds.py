import json

from models import Action, Reward, RewardBreakdown, RewardPenalties
from server.app import _clamp_scores
from tasks.email_triage.environment import EmailTriageEnvironment


def _find_bad_floats(obj, path="root"):
    bad = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            bad.extend(_find_bad_floats(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            bad.extend(_find_bad_floats(value, f"{path}[{idx}]"))
    elif isinstance(obj, float):
        if obj <= 0.0 or obj >= 1.0:
            bad.append((path, obj))
    return bad


def test_reward_model_dump_clamps_nested_floats():
    reward = Reward(
        score=0.0,
        feedback="test",
        breakdown=RewardBreakdown(correctness=1.0, reasoning_quality=0.0, progress=0.0),
        penalties=RewardPenalties(
            step_penalty=0.0,
            invalid_action_penalty=1.0,
            repetition_penalty=0.0,
            skip_penalty=0.0,
        ),
        early_bonus=0.0,
    )

    assert not _find_bad_floats(reward.model_dump())


def test_step_result_dump_has_no_boundary_scores():
    env = EmailTriageEnvironment()
    obs = env.reset()
    result = env.step(
        Action(
            action_type=obs.available_actions[0],
            value="invalid",
            reasoning="Because this is needed therefore we proceed.",
        )
    )

    assert not _find_bad_floats(result.model_dump())


def test_server_clamp_scores_sanitizes_boundary_values():
    payload = {
        "score": 0.0,
        "reward": {"score": 1.0},
        "results": [{"total_reward": 0.0}, {"nested_score": 1.0}],
    }

    assert not _find_bad_floats(_clamp_scores(payload))


def test_inference_results_fixture_has_no_boundary_scores():
    with open("inference_results.json", encoding="utf-8") as fh:
        payload = json.load(fh)

    assert not _find_bad_floats(payload)
