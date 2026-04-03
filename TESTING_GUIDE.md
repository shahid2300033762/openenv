# Testing Your OpenEnv Project - Complete Guide

## Option 1: Test the Live HuggingFace Space (Easiest)

No installation needed! Just visit:
https://huggingface.co/spaces/shahid21/openenv

### Steps:
1. Go to the URL above
2. Scroll down to see the API endpoints
3. Click on any endpoint (e.g., GET /health)
4. Click "Try it out"
5. Click "Execute"
6. See the response!

### Quick Tests:

**Test 1: Health Check**
- Endpoint: GET /health
- Click Try it out → Execute
- Expected response: `{"status":"ok","version":"1.0.0"}`

**Test 2: Create Email Triage Session**
- Endpoint: POST /reset
- Click Try it out
- Paste this in the request body:
```json
{
  "task_name": "email_triage",
  "index": 0
}
```
- Click Execute
- Should return: session_id + observation

**Test 3: Execute an Action**
- First run Test 2 to get a session_id
- Copy the session_id from response
- Endpoint: POST /step
- Paste this (replace SESSION_ID):
```json
{
  "session_id": "SESSION_ID",
  "action": {
    "action_type": "classify",
    "target": "email",
    "value": "complaint",
    "reasoning": "The customer is complaining about billing"
  }
}
```
- Click Execute
- Should return: observation + reward

---

## Option 2: Test Locally with Python

### Step 1: Install Dependencies
```bash
cd C:\Users\kshah\Desktop\env
pip install -r requirements.txt
```

### Step 2: Test Individual Environments

**Test Email Triage:**
```python
from tasks.email_triage.environment import EmailTriageEnvironment
from models import Action

env = EmailTriageEnvironment(email_index=0)
obs = env.reset()

print("=== EMAIL TRIAGE TEST ===")
print(f"Task: {obs.task_name}")
print(f"Instructions: {obs.instructions}")
print(f"Context: {obs.context}")
print(f"Data: {obs.data}")

# Take an action
action = Action(
    action_type="classify",
    target="email",
    value="complaint",
    reasoning="Customer discussing billing issues"
)

result = env.step(action)
print(f"\nReward Score: {result.reward.score}")
print(f"Reward Breakdown: {result.reward.breakdown}")
print(f"Done: {result.done}")
```

**Test Data Cleaning:**
```python
from tasks.data_cleaning.environment import DataCleaningEnvironment
from models import Action

env = DataCleaningEnvironment()
obs = env.reset()

print("=== DATA CLEANING TEST ===")
print(f"Task: {obs.task_name}")
print(f"Data:\n{obs.data}")

action = Action(
    action_type="fix_missing",
    target="column",
    value="age",
    reasoning="Fill missing age values with median"
)

result = env.step(action)
print(f"Reward: {result.reward.score}")
print(f"Done: {result.done}")
```

**Test Code Review:**
```python
from tasks.code_review.environment import CodeReviewEnvironment
from models import Action

env = CodeReviewEnvironment(snippet_index=0)
obs = env.reset()

print("=== CODE REVIEW TEST ===")
print(f"Task: {obs.task_name}")
print(f"Code:\n{obs.data}")

action = Action(
    action_type="identify_issue",
    target="bug",
    value="Off-by-one error in loop condition",
    reasoning="The loop should end at n-1, not n"
)

result = env.step(action)
print(f"Reward: {result.reward.score}")
```

**Test Incident Response:**
```python
from tasks.incident_response.environment import IncidentResponseEnvironment
from models import Action

env = IncidentResponseEnvironment(incident_index=0)
obs = env.reset()

print("=== INCIDENT RESPONSE TEST ===")
print(f"Task: {obs.task_name}")
print(f"Instructions: {obs.instructions}")
print(f"Security Log:\n{obs.data}")

action = Action(
    action_type="detect",
    target="threat",
    value="SQL injection attack",
    reasoning="Detected SQL injection in logs with malicious query patterns"
)

result = env.step(action)
print(f"Reward: {result.reward.score}")
print(f"Feedback: {result.observation.feedback}")
```

### Step 3: Run Full Inference

```bash
python inference.py
```

This will:
- Run all 4 tasks
- Create `inference_results.json` with results
- Show baseline agent scores

Look at the output:
```
Results saved to inference_results.json
```

View the results:
```bash
# On Windows PowerShell:
Get-Content inference_results.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Or just open it:
cat inference_results.json
```

---

## Option 3: Test with API Calls (curl/Postman)

### If you have the server running locally:

```bash
# Start the server
uvicorn server.app:app --port 7860
```

Then in another terminal:

**Test Health:**
```bash
curl http://localhost:7860/health
```

**Create Session:**
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name":"email_triage","index":0}'
```

**Execute Action:**
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"YOUR_SESSION_ID",
    "action":{
      "action_type":"classify",
      "target":"email",
      "value":"complaint",
      "reasoning":"Customer complaint about billing"
    }
  }'
```

---

## Option 4: Run All Tests

```bash
# Run comprehensive test suite
pytest tests/ -v

# See what happens:
# - 52 tests should pass
# - Covers all environments, models, graders
# - Tests reward calculations
```

---

## What You'll See in Output

### For Email Triage:
```
Observation:
  task_name: email_triage
  step: 1
  phase: classify
  instructions: "Classify this email into one of: complaint, inquiry, feedback, inquiry..."
  context: "Email from customer: [email content]"
  
Reward:
  score: 0.75 (if correct classification)
  breakdown: {
    correctness: 0.8,
    reasoning: 0.7,
    progress: 1.0
  }
```

### For Data Cleaning:
```
Reward:
  score: 0.33 (partial progress)
  breakdown: {
    correctness: 0.5 (fixed some issues),
    progress: 0.2 (progressed to next phase)
  }
  feedback: "Good start! Continue with duplicate removal"
```

### For Code Review:
```
Reward:
  score: 0.15 (challenging task)
  breakdown: {
    correctness: 0.2 (semantic similarity check),
    reasoning: 0.1 (reasoning evaluation)
  }
  feedback: "Partial match found. Consider more thorough analysis"
```

### For Incident Response:
```
Reward:
  score: 0.85 (good detection)
  breakdown: {
    correctness: 0.9 (IoC detection),
    reasoning: 0.8 (analysis quality),
    speed: 0.85 (within time window)
  }
  feedback: "Excellent threat detection! Continue with containment"
```

---

## Expected Output Summary

When you test, you should see:

✅ **Varying Scores** - Different actions produce different scores [0.0 - 1.0]
✅ **Detailed Feedback** - Each step explains why the score was given
✅ **Reward Breakdowns** - See how correctness, reasoning, and progress factor in
✅ **Phase Progression** - See tasks move through phases (email: classify → prioritize → respond)
✅ **Deterministic Results** - Same action always produces same score

---

## Quick Start (Copy-Paste Ready)

### Test 1: Verify Installation
```bash
cd C:\Users\kshah\Desktop\env
python -c "from models import Action, Observation; print('✅ All imports work!')"
```

### Test 2: Quick Environment Test
```bash
python -c "
from tasks.email_triage.environment import EmailTriageEnvironment
env = EmailTriageEnvironment()
obs = env.reset()
print(f'Email Triage Environment: {obs.task_name}')
print(f'Phase: {obs.phase}')
print(f'Instructions: {obs.instructions[:100]}...')
"
```

### Test 3: Full Inference
```bash
python inference.py
```

### Test 4: View Results
```bash
python -c "
import json
with open('inference_results.json') as f:
    results = json.load(f)
    for task, score in results.items():
        print(f'{task}: {score}')
"
```

---

## Troubleshooting

### If you get import errors:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### If you can't find inference_results.json:
```bash
# Check current directory
ls *.json
# or
Get-ChildItem *.json
```

### If tests fail:
```bash
# Run with more verbosity
pytest tests/ -v -s
```

---

## Summary

**Easiest:** Visit the live HF Space and use the Swagger UI (Option 1)
**Most Complete:** Run the inference script locally (Option 3)
**Most Detailed:** Test individual environments with Python (Option 2)

All three will show you that your project works perfectly! 🎉
