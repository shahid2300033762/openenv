"""
Test script to verify inference.py handles all error scenarios gracefully.
"""

import os
import subprocess
import sys

def test_scenario(name, env_vars, should_succeed=True):
    """Run inference.py with specific environment variables."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    # Set up environment
    env = os.environ.copy()
    for key, value in env_vars.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    
    # Run inference
    result = subprocess.run(
        [sys.executable, "inference.py"],
        env=env,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Check results
    success = result.returncode == 0
    has_results = "inference_results.json" in result.stdout
    has_markers = "[START]" in result.stdout and "[END]" in result.stdout
    
    print(f"Exit Code: {result.returncode}")
    print(f"Has Results JSON: {has_results}")
    print(f"Has Required Markers: {has_markers}")
    
    if success and has_results and has_markers:
        print("✓ PASS: Completed successfully")
        return True
    else:
        print("✗ FAIL: Did not complete properly")
        print("\nSTDOUT:")
        print(result.stdout[-500:])
        print("\nSTDERR:")
        print(result.stderr[-500:])
        return False

def main():
    """Run all test scenarios."""
    print("="*60)
    print("INFERENCE.PY ROBUSTNESS TEST SUITE")
    print("="*60)
    
    tests = [
        ("No API credentials (fallback mode)", {
            "API_BASE_URL": None,
            "API_KEY": None,
            "MODEL_NAME": "gpt-4o-mini"
        }),
        
        ("Missing API_BASE_URL only", {
            "API_BASE_URL": None,
            "API_KEY": "test-key",
            "MODEL_NAME": "gpt-4o-mini"
        }),
        
        ("Missing API_KEY only", {
            "API_BASE_URL": "https://api.openai.com/v1",
            "API_KEY": None,
            "MODEL_NAME": "gpt-4o-mini"
        }),
        
        ("Invalid proxy URL (should fallback)", {
            "API_BASE_URL": "http://invalid-proxy-url:9999",
            "API_KEY": "invalid-key",
            "MODEL_NAME": "gpt-4o-mini"
        }),
    ]
    
    results = []
    for name, env_vars in tests:
        passed = test_scenario(name, env_vars)
        results.append((name, passed))
    
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    if passed_count == total_count:
        print("\n✓ ALL TESTS PASSED - inference.py is bulletproof!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
