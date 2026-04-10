"""
Final Pre-Submission Risk Assessment
Checks all critical requirements to avoid disqualification
"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def check_critical_logging_format():
    """CRITICAL: Check that inference.py has [START], [STEP], [END] logging."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: Logging Format Compliance")
    print("="*80)
    
    # Check if markers exist in code
    with open("inference.py") as f:
        code = f.read()
    
    has_start = "[START]" in code
    has_step = "[STEP]" in code
    has_end = "[END]" in code
    
    print(f"  {'✓' if has_start else '✗'} [START] marker found in code")
    print(f"  {'✓' if has_step else '✗'} [STEP] marker found in code")
    print(f"  {'✓' if has_end else '✗'} [END] marker found in code")
    
    if not (has_start and has_step and has_end):
        print("\n  ❌ CRITICAL FAILURE: Missing required logging markers!")
        print("  This WILL cause disqualification or incorrect scoring!")
        return False
    
    # Run inference and check output
    print("\n  Running inference.py to verify output format...")
    try:
        result = subprocess.run(
            [sys.executable, "inference.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        
        # Check for actual [START], [STEP], [END] in output
        start_count = len(re.findall(r"\[START\]", output))
        step_count = len(re.findall(r"\[STEP\]", output))
        end_count = len(re.findall(r"\[END\]", output))
        
        print(f"\n  Output Analysis:")
        print(f"    [START] markers: {start_count} (expected: 4, one per task)")
        print(f"    [STEP] markers: {step_count} (expected: 10+)")
        print(f"    [END] markers: {end_count} (expected: 4, one per task)")
        
        if start_count >= 4 and step_count > 0 and end_count >= 4:
            print("\n  ✓ LOGGING FORMAT VERIFIED - WILL NOT BE DISQUALIFIED")
            return True
        else:
            print("\n  ❌ LOGGING FORMAT INCOMPLETE - RISK OF DISQUALIFICATION")
            return False
            
    except Exception as e:
        print(f"\n  ⚠ Could not verify output (error: {e})")
        return False


def check_grader_variability():
    """Check that graders produce variable scores (not hardcoded)."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: Graders Not Fake")
    print("="*80)
    
    from main import create_environment
    from models import Action
    
    all_good = True
    
    for task_name in ["email_triage", "data_cleaning", "code_review", "incident_response"]:
        env = create_environment(task_name)
        obs = env.reset()
        
        scores = []
        # Try different actions
        test_values = ["test1", "test2", "different_value", "x", "y"]
        
        for val in test_values[:3]:  # Test 3 different actions
            action = Action(
                action_type=obs.available_actions[0] if obs.available_actions else "test",
                target="test",
                value=val,
                reasoning=f"Test reasoning for {val}"
            )
            result = env.step(action)
            scores.append(result.reward.score)
            env.reset()  # Reset for next test
        
        # Check if scores vary or are always the same
        unique_scores = len(set(scores))
        all_same = unique_scores == 1
        
        status = "✗ FAKE" if all_same else "✓ REAL"
        print(f"  {status} {task_name}: {unique_scores} unique scores from 3 actions")
        
        if all_same and scores[0] == scores[1]:
            print(f"    ⚠ WARNING: All scores identical ({scores[0]}) - may be flagged as fake grader!")
            all_good = False
    
    if all_good:
        print("\n  ✓ GRADERS ARE REAL - WILL NOT BE DISQUALIFIED")
    else:
        print("\n  ⚠ Some graders may appear fake - review grading logic")
    
    return all_good


def check_runtime_limit():
    """Check that inference.py completes in < 20 minutes."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: Runtime < 20 Minutes")
    print("="*80)
    
    import time
    
    print("  Running inference.py with timeout...")
    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, "inference.py"],
            capture_output=True,
            text=True,
            timeout=1200  # 20 minute hard limit
        )
        elapsed = time.time() - start
        
        passed = elapsed < 1200 and result.returncode == 0
        
        minutes = elapsed / 60
        print(f"\n  Runtime: {elapsed:.1f}s ({minutes:.2f} minutes)")
        print(f"  Limit: 1200s (20 minutes)")
        
        if passed:
            print(f"\n  ✓ RUNTIME OK - WILL NOT BE DISQUALIFIED")
        else:
            print(f"\n  ❌ RUNTIME EXCEEDED - WILL BE DISQUALIFIED")
        
        return passed
        
    except subprocess.TimeoutExpired:
        print(f"\n  ❌ TIMEOUT - Exceeded 20 minute limit!")
        print("  WILL BE DISQUALIFIED")
        return False


def check_hf_space_readiness():
    """Check HuggingFace Space deployment readiness."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: HF Space Deployment")
    print("="*80)
    
    # Check Dockerfile exists
    if not os.path.exists("Dockerfile"):
        print("  ❌ Dockerfile missing - WILL BE DISQUALIFIED")
        return False
    
    print("  ✓ Dockerfile exists")
    
    # Check server exists
    if not os.path.exists("server/app.py"):
        print("  ❌ Server missing - WILL BE DISQUALIFIED")
        return False
    
    print("  ✓ Server exists")
    
    # Check server has required endpoints
    with open("server/app.py") as f:
        server_code = f.read()
    
    has_reset = "/reset" in server_code
    has_step = "/step" in server_code
    has_health = "/health" in server_code
    
    print(f"  {'✓' if has_reset else '✗'} /reset endpoint")
    print(f"  {'✓' if has_step else '✗'} /step endpoint")
    print(f"  {'✓' if has_health else '✗'} /health endpoint")
    
    if not (has_reset and has_step):
        print("\n  ❌ Missing required endpoints - WILL BE DISQUALIFIED")
        return False
    
    print("\n  ✓ HF SPACE READY - WILL NOT BE DISQUALIFIED")
    return True


def check_openenv_compliance():
    """Check OpenEnv specification compliance."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: OpenEnv Specification")
    print("="*80)
    
    try:
        result = subprocess.run(
            [sys.executable, "main.py", "--validate"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        passed = result.returncode == 0
        
        if passed:
            print("  ✓ OpenEnv validation passed")
            print("\n  ✓ SPEC COMPLIANT - WILL NOT BE DISQUALIFIED")
        else:
            print("  ❌ OpenEnv validation failed")
            print(f"\n{result.stdout}\n{result.stderr}")
            print("\n  ❌ SPEC VIOLATION - WILL BE DISQUALIFIED")
        
        return passed
        
    except Exception as e:
        print(f"  ❌ Validation error: {e}")
        print("\n  ❌ CANNOT VALIDATE - RISK OF DISQUALIFICATION")
        return False


def check_minimum_tasks():
    """Check that there are at least 3 tasks."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: Minimum 3 Tasks")
    print("="*80)
    
    import yaml
    
    with open("openenv.yaml") as f:
        config = yaml.safe_load(f)
    
    tasks = config.get("tasks", [])
    task_count = len(tasks)
    
    print(f"  Tasks defined: {task_count}")
    print(f"  Minimum required: 3")
    
    if task_count >= 3:
        print(f"\n  ✓ TASK REQUIREMENT MET - WILL NOT BE DISQUALIFIED")
        print(f"  Tasks: {[t.get('name', t.get('id')) for t in tasks]}")
        return True
    else:
        print(f"\n  ❌ INSUFFICIENT TASKS - WILL BE DISQUALIFIED")
        return False


def check_score_range():
    """Check that all scores are strictly in (0.0, 1.0)."""
    print("\n" + "="*80)
    print("CRITICAL CHECK: Score Range (0.0, 1.0)")
    print("="*80)
    
    from main import create_environment
    from models import Action
    
    all_valid = True
    
    for task_name in ["email_triage", "data_cleaning", "code_review", "incident_response"]:
        env = create_environment(task_name)
        obs = env.reset()
        
        # Test a few actions
        for i in range(3):
            action = Action(
                action_type=obs.available_actions[0] if obs.available_actions else "test",
                target="test",
                value=f"test{i}",
                reasoning="test"
            )
            result = env.step(action)
            score = result.reward.score
            
            if not (0.0 < score < 1.0):
                print(f"  ❌ {task_name}: Score {score} outside (0.0, 1.0)!")
                all_valid = False
            
            obs = result.observation
            if result.done:
                break
    
    if all_valid:
        print("  ✓ All scores in valid range (0.0, 1.0)")
        print("\n  ✓ SCORE RANGE VALID - WILL NOT BE DISQUALIFIED")
    else:
        print("\n  ❌ INVALID SCORES - MAY BE DISQUALIFIED")
    
    return all_valid


def main():
    """Run all critical checks."""
    print("\n" + "="*80)
    print("  FINAL PRE-SUBMISSION RISK ASSESSMENT")
    print("  Competition Disqualification Check")
    print("="*80)
    
    checks = [
        ("Logging Format [START][STEP][END]", check_critical_logging_format),
        ("Graders Not Fake", check_grader_variability),
        ("Runtime < 20 Minutes", check_runtime_limit),
        ("HF Space Deployment", check_hf_space_readiness),
        ("OpenEnv Compliance", check_openenv_compliance),
        ("Minimum 3 Tasks", check_minimum_tasks),
        ("Score Range (0.0, 1.0)", check_score_range),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed = check_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ⚠ Error in {name}: {e}")
            results.append((name, False))
    
    # Final summary
    print("\n" + "="*80)
    print("  DISQUALIFICATION RISK SUMMARY")
    print("="*80)
    
    critical_failures = []
    warnings = []
    
    for name, passed in results:
        if not passed:
            critical_failures.append(name)
            print(f"  ❌ CRITICAL: {name}")
        else:
            print(f"  ✓ PASS: {name}")
    
    print("\n" + "="*80)
    
    if not critical_failures:
        print("  🎉 ALL CRITICAL CHECKS PASSED!")
        print("  ✅ NO DISQUALIFICATION RISKS DETECTED")
        print("  ✅ SAFE TO SUBMIT")
        print("="*80 + "\n")
        return 0
    else:
        print("  ⚠️  CRITICAL FAILURES DETECTED!")
        print(f"  ❌ {len(critical_failures)} DISQUALIFICATION RISKS:")
        for fail in critical_failures:
            print(f"     - {fail}")
        print("\n  🚨 DO NOT SUBMIT - FIX ISSUES FIRST!")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
