import requests
import json

BASE_URL = "https://shahid21-openenv.hf.space"

print("=" * 80)
print("TESTING POST /reset")
print("=" * 80)

# 1. Test /reset endpoint
reset_response = requests.post(f"{BASE_URL}/reset", json={
    "task_name": "email_triage",
    "index": 0
})

reset_data = reset_response.json()
print(json.dumps(reset_data, indent=2))

session_id = reset_data["session_id"]
print(f"\n✓ Session created: {session_id}\n")

print("=" * 80)
print("TESTING POST /step")
print("=" * 80)

# 2. Test /step endpoint
step_response = requests.post(f"{BASE_URL}/step", json={
    "session_id": session_id,
    "action": {
        "action_type": "classify",
        "target": "email",
        "value": "complaint",
        "reasoning": "Customer frustrated about duplicate billing"
    }
})

step_data = step_response.json()
print(json.dumps(step_data, indent=2))

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Phase after reset: {reset_data['observation']['phase']}")
print(f"Available actions: {reset_data['observation']['available_actions']}")
print(f"\nPhase after step: {step_data['observation']['phase']}")
print(f"Score: {step_data['reward']['score']:.4f}")
print(f"Feedback: {step_data['reward']['feedback']}")
print(f"Done: {step_data['done']}")
