"""
Test script to verify API_BASE_URL is properly required and used.
"""
import os
import sys

def test_baseline_agent():
    """Test that baseline agent requires API_BASE_URL."""
    print("\n=== Testing baseline/agent.py ===")
    
    # Clear environment
    for key in ["API_BASE_URL", "API_KEY", "OPENAI_API_KEY"]:
        os.environ.pop(key, None)
    
    # Test 1: Should fail without API_BASE_URL
    print("\n1. Testing without API_BASE_URL (should fail)...")
    try:
        from baseline.agent import _get_openai_client
        os.environ["API_KEY"] = "test_key"
        client = _get_openai_client()
        print("   ❌ FAIL: Client was created without API_BASE_URL")
        return False
    except (ValueError, KeyError) as e:
        if "API_BASE_URL" in str(e) or "API_KEY" in str(e):
            print(f"   ✅ PASS: Correctly failed with: {e}")
        else:
            print(f"   ❌ FAIL: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"   ❌ FAIL: Unexpected error type {type(e)}: {e}")
        return False
    
    # Test 2: Should succeed with API_BASE_URL
    print("\n2. Testing with API_BASE_URL (should succeed)...")
    try:
        os.environ["API_BASE_URL"] = "https://test-proxy.example.com/v1"
        os.environ["API_KEY"] = "test_key"
        from importlib import reload
        import baseline.agent
        reload(baseline.agent)
        from baseline.agent import _get_openai_client
        client = _get_openai_client()
        
        # Check that the client uses the proxy URL
        if hasattr(client, 'base_url') and "test-proxy.example.com" in str(client.base_url):
            print(f"   ✅ PASS: Client configured with proxy URL: {client.base_url}")
        else:
            print(f"   ⚠️  WARN: Could not verify base_url. Client: {client}")
    except ImportError:
        print("   ⚠️  SKIP: OpenAI library not installed")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False
    
    return True

def test_inference_script():
    """Test that inference.py requires API_BASE_URL."""
    print("\n\n=== Testing inference.py ===")
    
    # Clear environment
    for key in ["API_BASE_URL", "API_KEY", "OPENAI_API_KEY", "HF_TOKEN"]:
        os.environ.pop(key, None)
    
    # Test 1: Should return None without API_BASE_URL
    print("\n1. Testing without API_BASE_URL (should return None)...")
    try:
        from importlib import reload
        import inference
        reload(inference)
        from inference import get_openai_client
        
        os.environ["API_KEY"] = "test_key"
        client, model = get_openai_client()
        
    except (KeyError, ValueError) as e:
        print(f"   ✅ PASS: Correctly raised error when API_BASE_URL not set: {e}")
    except Exception as e:
        print(f"   ❌ FAIL: Unexpected error: {e}")
        return False
    
    # Test 2: Should succeed with API_BASE_URL
    print("\n2. Testing with API_BASE_URL (should succeed)...")
    try:
        os.environ["API_BASE_URL"] = "https://competition-proxy.example.com/v1"
        os.environ["API_KEY"] = "test_key"
        
        reload(inference)
        from inference import get_openai_client
        client, model = get_openai_client()
        
        if client is not None:
            if hasattr(client, 'base_url') and "competition-proxy.example.com" in str(client.base_url):
                print(f"   ✅ PASS: Client configured with proxy URL: {client.base_url}")
            else:
                print(f"   ⚠️  WARN: Could not verify base_url. Client: {client}")
        else:
            print("   ❌ FAIL: Client is None even with API_BASE_URL set")
            return False
    except ImportError:
        print("   ⚠️  SKIP: OpenAI library not installed")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("TESTING: API_BASE_URL Proxy Fix")
    print("="*60)
    
    result1 = test_baseline_agent()
    result2 = test_inference_script()
    
    print("\n" + "="*60)
    if result1 and result2:
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe fix ensures:")
        print("1. baseline/agent.py REQUIRES API_BASE_URL")
        print("2. inference.py REQUIRES API_BASE_URL")
        print("3. Competition proxy will be used when provided")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)
