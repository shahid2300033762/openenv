"""Test that ALL float values in ALL responses are strictly in (0, 1)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Action, Reward, RewardBreakdown, RewardPenalties

def find_bad_floats(obj, path=''):
    """Recursively find all float values that are exactly 0.0 or 1.0."""
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            bad.extend(find_bad_floats(v, f'{path}.{k}'))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(find_bad_floats(v, f'{path}[{i}]'))
    elif isinstance(obj, float):
        if obj <= 0.0 or obj >= 1.0:
            bad.append((path, obj))
    return bad


def test_pydantic_models():
    print("=== Testing Pydantic model validators ===")
    
    r = Reward(score=0.0, feedback='test')
    assert 0.0 < r.score < 1.0, f'FAIL: Reward(score=0.0) -> {r.score}'
    print(f'  Reward(score=0.0) -> {r.score} OK')
    
    r = Reward(score=1.0, feedback='test')
    assert 0.0 < r.score < 1.0, f'FAIL: Reward(score=1.0) -> {r.score}'
    print(f'  Reward(score=1.0) -> {r.score} OK')
    
    r = Reward(score=-0.5, feedback='test')
    assert 0.0 < r.score < 1.0, f'FAIL: Reward(score=-0.5) -> {r.score}'
    print(f'  Reward(score=-0.5) -> {r.score} OK')
    
    rb = RewardBreakdown(correctness=0.0, reasoning_quality=0.0, progress=0.0)
    for field in ['correctness', 'reasoning_quality', 'progress']:
        v = getattr(rb, field)
        assert 0.0 < v < 1.0, f'FAIL: RewardBreakdown.{field} = {v}'
    print(f'  RewardBreakdown(all 0.0) -> clamped OK')
    
    rb = RewardBreakdown(correctness=1.0, reasoning_quality=1.0, progress=1.0)
    for field in ['correctness', 'reasoning_quality', 'progress']:
        v = getattr(rb, field)
        assert 0.0 < v < 1.0, f'FAIL: RewardBreakdown.{field} = {v}'
    print(f'  RewardBreakdown(all 1.0) -> clamped OK')
    
    rp = RewardPenalties(step_penalty=0.0, invalid_action_penalty=0.0, repetition_penalty=0.0, skip_penalty=0.0)
    for field in ['step_penalty', 'invalid_action_penalty', 'repetition_penalty', 'skip_penalty']:
        v = getattr(rp, field)
        assert 0.0 < v < 1.0, f'FAIL: RewardPenalties.{field} = {v}'
    print(f'  RewardPenalties(all 0.0) -> clamped OK')
    
    r = Reward(score=0.5, feedback='test', early_bonus=0.0)
    assert 0.0 < r.early_bonus, f'FAIL: early_bonus = {r.early_bonus}'
    print(f'  Reward(early_bonus=0.0) -> {r.early_bonus} OK')
    
    # Full model_dump with all zeros
    r = Reward(
        score=0.0, feedback='test',
        breakdown=RewardBreakdown(correctness=0.0, reasoning_quality=0.0, progress=0.0),
        penalties=RewardPenalties(step_penalty=0.0, invalid_action_penalty=0.0, repetition_penalty=0.0, skip_penalty=0.0),
        early_bonus=0.0
    )
    d = r.model_dump()
    bads = find_bad_floats(d, 'Reward')
    if bads:
        for path, val in bads:
            print(f'  BAD in model_dump: {path} = {val}')
        assert False, f'Found {len(bads)} bad floats'
    print(f'  Full model_dump (all zeros): OK')
    print(f'  JSON: {json.dumps(d)}')
    print()


def test_environments():
    from tasks.email_triage.environment import EmailTriageEnvironment
    from tasks.data_cleaning.environment import DataCleaningEnvironment
    from tasks.code_review.environment import CodeReviewEnvironment
    from tasks.incident_response.environment import IncidentResponseEnvironment
    
    print("=== Testing all environments ===")
    
    test_cases = [
        ('email_triage', EmailTriageEnvironment, [
            [('classify', 'complaint'), ('prioritize', 'high'), ('respond', 'Thank you for reaching out.')],
            [('classify', 'xyz'), ('prioritize', 'xyz'), ('respond', 'x')],
        ]),
        ('data_cleaning', DataCleaningEnvironment, [
            [('fix_missing', 'fill_default'), ('remove_duplicates', 'deduplicate'), ('normalize_casing', 'title_case'), ('fix_format', 'standardize')],
        ]),
        ('code_review', CodeReviewEnvironment, [
            [('identify_issue', 'SQL injection'), ('suggest_fix', 'parameterized queries'), ('optimize_code', 'performance')],
            [('identify_issue', 'x'), ('suggest_fix', 'x'), ('optimize_code', 'x')],
        ]),
        ('incident_response', IncidentResponseEnvironment, [
            [('detect', 'sql_injection'), ('analyze', 'IP 10.0.0.1'), ('contain', 'block IP'), ('remediate', 'patch'), ('document', 'report')],
            [('detect', 'x'), ('analyze', 'x'), ('contain', 'x'), ('remediate', 'x'), ('document', 'x')],
        ]),
    ]
    
    total_bads = []
    for task_name, EnvClass, sequences in test_cases:
        for seq_idx, action_seq in enumerate(sequences):
            env = EnvClass()
            obs = env.reset()
            
            for action_type, value in action_seq:
                try:
                    result = env.step(Action(
                        action_type=action_type,
                        value=value,
                        reasoning='Because this is needed therefore we proceed.'
                    ))
                    dump = result.model_dump()
                    bads = find_bad_floats(dump, f'{task_name}/seq{seq_idx}/{action_type}')
                    if bads:
                        total_bads.extend(bads)
                        for path, val in bads:
                            print(f'  BAD: {path} = {val}')
                    else:
                        print(f'  {task_name}/seq{seq_idx}/{action_type}: score={dump["reward"]["score"]:.4f} OK')
                    
                    if result.done:
                        break
                except Exception as e:
                    print(f'  ERROR: {task_name}/seq{seq_idx}/{action_type}: {e}')
                    break
            
            # Test already_done
            try:
                if env._done:
                    r = env.step(Action(action_type='classify', value='test', reasoning='test'))
                    dump = r.model_dump()
                    bads = find_bad_floats(dump, f'{task_name}/seq{seq_idx}/done')
                    if bads:
                        total_bads.extend(bads)
                        for path, val in bads:
                            print(f'  BAD: {path} = {val}')
                    else:
                        print(f'  {task_name}/seq{seq_idx}/done: score={dump["reward"]["score"]:.4f} OK')
            except Exception:
                pass
    
    print()
    if total_bads:
        print(f'FOUND {len(total_bads)} bad float values!')
        return False
    else:
        print('All environment scores strictly in (0, 1)!')
        return True


if __name__ == '__main__':
    test_pydantic_models()
    ok = test_environments()
    if ok:
        print('\n=== ALL TESTS PASSED ===')
    else:
        print('\n=== TESTS FAILED ===')
        sys.exit(1)
