# API Documentation

## Overview

The OpenEnv Workflow Evaluation Environment exposes a RESTful API via FastAPI for remote agent evaluation.

**Base URL (Local)**: `http://localhost:7860`  
**Base URL (HF Space)**: `https://YOUR_USERNAME-openenv-workflow.hf.space`

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Example:**
```bash
curl http://localhost:7860/health
```

---

### 2. Create Session & Reset Environment

**POST** `/reset`

Create a new evaluation session and initialize an environment.

**Request Body:**
```json
{
  "task_name": "email_triage",  // email_triage | data_cleaning | code_review | incident_response
  "index": 0                     // Optional: scenario index (default: 0)
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "observation": {
    "task_name": "email_triage",
    "step": 1,
    "instructions": "Classify this email...",
    "context": "You are a customer support agent...",
    "data": "From: angry@customer.com\nSubject: Billing Issue...",
    "feedback": "",
    "available_actions": ["classify", "prioritize", "respond"],
    "phase": "classify"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "incident_response", "index": 0}'
```

**Available Tasks:**
- `email_triage` - Customer support email processing (Easy)
- `data_cleaning` - Dataset quality improvement (Medium)
- `code_review` - Pull request security review (Hard)
- `incident_response` - Cybersecurity incident response (Expert)

---

### 3. Execute Action

**POST** `/step`

Execute an action in an existing session.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": {
    "action_type": "detect",
    "target": "security_logs",
    "value": "SQL injection attack detected in application logs",
    "reasoning": "Multiple UNION SELECT statements in HTTP request parameters indicate SQLi attempts"
  }
}
```

**Response:**
```json
{
  "observation": {
    "task_name": "incident_response",
    "step": 2,
    "instructions": "Analyze the attack...",
    "context": "Detection phase complete...",
    "data": "Logs: [2026-03-28 10:00:01] ...",
    "feedback": "✓ Detection accuracy: 100%",
    "available_actions": ["analyze", "contain"],
    "phase": "analyze"
  },
  "reward": {
    "score": 0.85,
    "feedback": "Excellent detection! Attack type correctly identified.",
    "breakdown": {
      "correctness": 0.80,
      "reasoning_quality": 0.20,
      "progress": 0.15
    }
  },
  "done": false,
  "info": {
    "total_reward": 0.85,
    "step_count": 1
  }
}
```

**Action Schema:**
```json
{
  "action_type": "string",  // Required: One of available_actions from observation
  "target": "string",       // Required: What the action targets
  "value": "string",        // Required: Content/value for the action
  "reasoning": "string"     // Required: Detailed reasoning (improves score!)
}
```

**Example:**
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "action": {
      "action_type": "classify",
      "target": "email",
      "value": "complaint",
      "reasoning": "Customer is frustrated about billing errors"
    }
  }'
```

---

### 4. Get Session State

**GET** `/state/{session_id}`

Retrieve the current state of a session.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "incident_response",
  "step_count": 3,
  "current_phase": "contain",
  "done": false,
  "total_reward": 2.35,
  "trace": [
    {
      "step": 1,
      "action": "detect",
      "score": 0.85
    },
    {
      "step": 2,
      "action": "analyze",
      "score": 0.75
    },
    {
      "step": 3,
      "action": "contain",
      "score": 0.75
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:7860/state/550e8400-e29b-41d4-a716-446655440000
```

---

## Complete Workflow Example

### Python Example

```python
import requests

BASE_URL = "http://localhost:7860"

# 1. Create session
response = requests.post(f"{BASE_URL}/reset", json={
    "task_name": "incident_response",
    "index": 0
})
data = response.json()
session_id = data["session_id"]
observation = data["observation"]

print(f"Session created: {session_id}")
print(f"Instructions: {observation['instructions']}")

# 2. Execute actions
while True:
    # Get available actions
    available_actions = observation["available_actions"]
    print(f"\nAvailable actions: {available_actions}")
    
    # Your agent decides action (this is simplified)
    action = {
        "action_type": available_actions[0],
        "target": "security_logs",
        "value": "SQL injection detected in login form",
        "reasoning": "Pattern matching shows malicious input in user_id parameter"
    }
    
    # Execute action
    response = requests.post(f"{BASE_URL}/step", json={
        "session_id": session_id,
        "action": action
    })
    
    result = response.json()
    observation = result["observation"]
    reward = result["reward"]
    done = result["done"]
    
    print(f"Score: {reward['score']:.3f}")
    print(f"Feedback: {reward['feedback']}")
    
    if done:
        print(f"\nEpisode complete! Total reward: {result['info']['total_reward']}")
        break

# 3. Check final state
response = requests.get(f"{BASE_URL}/state/{session_id}")
final_state = response.json()
print(f"\nFinal state: {final_state}")
```

### JavaScript Example

```javascript
const BASE_URL = "http://localhost:7860";

async function runAgent() {
    // 1. Create session
    const resetResponse = await fetch(`${BASE_URL}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            task_name: 'email_triage',
            index: 0
        })
    });
    
    const { session_id, observation } = await resetResponse.json();
    console.log('Session created:', session_id);
    
    // 2. Execute action
    const stepResponse = await fetch(`${BASE_URL}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: session_id,
            action: {
                action_type: 'classify',
                target: 'email',
                value: 'complaint',
                reasoning: 'Customer mentions billing issues and frustration'
            }
        })
    });
    
    const result = await stepResponse.json();
    console.log('Score:', result.reward.score);
    console.log('Feedback:', result.reward.feedback);
}

runAgent();
```

### cURL Example

```bash
#!/bin/bash

# 1. Create session
SESSION_DATA=$(curl -s -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "code_review", "index": 0}')

SESSION_ID=$(echo $SESSION_DATA | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# 2. Execute action
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"action\": {
      \"action_type\": \"identify_issue\",
      \"target\": \"code\",
      \"value\": \"SQL injection vulnerability in login function\",
      \"reasoning\": \"User input is directly interpolated into SQL query using f-strings\"
    }
  }" | jq '.'

# 3. Get state
curl -s http://localhost:7860/state/$SESSION_ID | jq '.'
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Session not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Unknown task: invalid_task_name"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "action", "action_type"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Task-Specific Actions

### Email Triage
**Actions**: `classify`, `prioritize`, `respond`

**Example:**
```json
{
  "action_type": "classify",
  "target": "email",
  "value": "complaint",
  "reasoning": "Customer expresses frustration about service issues"
}
```

### Data Cleaning
**Actions**: `fix_missing`, `remove_duplicates`, `normalize_casing`, `fix_format`

**Example:**
```json
{
  "action_type": "fix_missing",
  "target": "column_name",
  "value": "fill_with_median",
  "reasoning": "Median is robust to outliers for this numeric column"
}
```

### Code Review
**Actions**: `identify_issue`, `suggest_fix`, `optimize_code`

**Example:**
```json
{
  "action_type": "identify_issue",
  "target": "login_function",
  "value": "SQL injection vulnerability - user input directly in query",
  "reasoning": "Line 42 uses f-string interpolation which is unsafe for SQL"
}
```

### Incident Response
**Actions**: `detect`, `analyze`, `contain`, `remediate`, `document`

**Example:**
```json
{
  "action_type": "detect",
  "target": "security_logs",
  "value": "SQL injection attack",
  "reasoning": "Multiple UNION SELECT statements in HTTP logs indicate SQLi attack"
}
```

---

## Running the Server

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn server.app:app --reload --port 7860

# Server available at: http://localhost:7860
# API docs: http://localhost:7860/docs
```

### Docker
```bash
# Build
docker build -t openenv-workflow .

# Run
docker run -p 7860:7860 openenv-workflow

# Test
curl http://localhost:7860/health
```

### HuggingFace Space
Deploy to HF Space and it automatically runs on port 7860.

**Space URL**: `https://YOUR_USERNAME-openenv-workflow.hf.space`

---

## Rate Limits

No rate limits currently implemented. Sessions are stored in-memory and will be lost on server restart.

## Authentication

No authentication required for the evaluation API.

---

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:7860/docs
- **ReDoc**: http://localhost:7860/redoc

These provide:
- Interactive API testing
- Complete schema documentation
- Example requests/responses
- Try-it-out functionality

---

## Session Management

- Sessions are stored in-memory (`_sessions` dict)
- Each session has a unique UUID
- Sessions persist until server restart
- No automatic cleanup (consider implementing TTL for production)

---

## Support

For issues or questions:
- GitHub: [Your Repository URL]
- Documentation: See README.md
- Validation: Run `python validate_submission.py`
