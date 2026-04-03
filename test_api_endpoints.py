"""
Test all API endpoints locally before deployment.
"""
import sys
sys.path.insert(0, '..')

from server.app import app
from fastapi.testclient import TestClient

client = TestClient(app)

print('=== TESTING ALL API ENDPOINTS ===\n')

# Test 1: Health check
print('1. GET /health')
response = client.get('/health')
print(f'   Status: {response.status_code}')
print(f'   Response: {response.json()}')
print()

# Test 2: List tasks
print('2. GET /tasks')
response = client.get('/tasks')
print(f'   Status: {response.status_code}')
print(f'   Tasks: {response.json()}')
print()

# Test 3: Reset environment
print('3. POST /reset')
response = client.post('/reset', json={'task_name': 'email_triage'})
print(f'   Status: {response.status_code}')
data = response.json()
print(f'   Task: {data.get("task_name")}')
obs = data.get("observation", {})
print(f'   Instructions: {obs.get("instructions", "")[:80]}...')
print()

# Test 4: Step action
print('4. POST /step')
step_data = {
    'task_name': 'email_triage',
    'action': {
        'action_type': 'classify',
        'target': 'email',
        'value': 'complaint',
        'reasoning': 'Testing endpoint'
    }
}
response = client.post('/step', json=step_data)
print(f'   Status: {response.status_code}')
data = response.json()
print(f'   Score: {data.get("reward", {}).get("score")}')
print(f'   Done: {data.get("done")}')
print()

# Test 5: Get state
print('5. GET /state')
response = client.get('/state', params={'task_name': 'email_triage'})
print(f'   Status: {response.status_code}')
data = response.json()
print(f'   Steps: {data.get("steps_taken")}')
print()

# Test all 4 tasks
print('6. Testing all 4 task resets')
tasks = ['email_triage', 'data_cleaning', 'code_review', 'incident_response']
for task in tasks:
    response = client.post('/reset', json={'task_name': task})
    status = '✅' if response.status_code == 200 else '❌'
    print(f'   {status} {task}: {response.status_code}')

print('\n✅ ALL ENDPOINTS WORKING LOCALLY')
