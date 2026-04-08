"""
Test to verify inference.py ATTEMPTS to use the LiteLLM proxy.
This simulates what the competition validator does.
"""

import os
import subprocess
import sys

def test_api_attempt():
    """Verify that inference.py attempts to call the API when credentials are provided."""
    
    print("="*60)
    print("TEST: Verify API Call Attempt (Simulating Validator)")
    print("="*60)
    
    # Set up environment like the validator does
    env = os.environ.copy()
    env["API_BASE_URL"] = "https://fake-litellm-proxy.example.com/v1"
    env["API_KEY"] = "sk-test-validator-key-12345"
    env["MODEL_NAME"] = "gpt-4o-mini"
    
    print(f"\nEnvironment set:")
    print(f"  API_BASE_URL: {env['API_BASE_URL']}")
    print(f"  API_KEY: {env['API_KEY'][:15]}...")
    print(f"  MODEL_NAME: {env['MODEL_NAME']}")
    
    print("\nRunning inference.py...\n")
    
    # Run inference
    result = subprocess.run(
        [sys.executable, "inference.py"],
        env=env,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Check output
    stdout = result.stdout
    stderr = result.stderr
    
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    # Key indicators
    client_init_success = "[OK] OpenAI client initialized successfully" in stdout
    api_attempt_made = "client.chat.completions.create" in stdout or "ERROR: API call failed" in stdout or "ERROR: Connection failed" in stdout or "ERROR:" in stdout
    fallback_message = "Falling back to heuristic" in stdout
    warning_no_client = "WARNING: No API client available" in stdout
    
    print(f"\n✓ Client initialized: {client_init_success}")
    print(f"✓ API attempt detected: {api_attempt_made or fallback_message}")
    print(f"✗ Premature fallback (bad): {warning_no_client}")
    
    # Look for specific error messages that indicate an API call was attempted
    connection_error = "Connection failed" in stdout or "Proxy connection" in stdout
    timeout_error = "timeout" in stdout.lower()
    
    print(f"\n✓ Connection/proxy error (good - means API was attempted): {connection_error}")
    print(f"✓ Timeout error (good - means API was attempted): {timeout_error}")
    
    # Show relevant output
    print("\n" + "="*60)
    print("RELEVANT OUTPUT (first 1500 chars):")
    print("="*60)
    print(stdout[:1500])
    
    if stderr:
        print("\n" + "="*60)
        print("STDERR (first 500 chars):")
        print("="*60)
        print(stderr[:500])
    
    # Verdict
    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)
    
    if warning_no_client:
        print("\n❌ FAIL: Code detected missing credentials and fell back WITHOUT attempting API")
        print("   The validator will see this as 'No API calls were made'")
        print("   FIX: Remove the early check for client==None")
        return False
    
    if client_init_success and (connection_error or timeout_error or "ERROR:" in stdout):
        print("\n✅ PASS: Client initialized and API call was ATTEMPTED")
        print("   The attempt failed (expected - fake proxy), but validator will see the attempt")
        return True
    
    if fallback_message:
        print("\n⚠️  PARTIAL: Fallback occurred, checking if API was attempted first...")
        if connection_error or timeout_error:
            print("   ✅ API was attempted before fallback - GOOD")
            return True
        else:
            print("   ❌ No evidence of API attempt - BAD")
            return False
    
    print("\n❓ UNCLEAR: Could not determine if API was attempted")
    print("   Review output above")
    return False

if __name__ == "__main__":
    success = test_api_attempt()
    sys.exit(0 if success else 1)
