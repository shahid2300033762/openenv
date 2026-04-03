#!/usr/bin/env python3
"""Test the /reset endpoint locally."""

from starlette.testclient import TestClient
from server.app import app

client = TestClient(app)

print('Testing /reset endpoint with TestClient...')
print('-' * 50)

r = client.post('/reset')
print(f'Empty POST: {r.status_code}')
if r.status_code == 200:
    body = r.json()
    print(f'  ✅ Session: {body.get("session_id", "?")[:8]}...')
else:
    print(f'  ❌ Error: {r.json()}')

r2 = client.post('/reset', json={})
print(f'Empty JSON: {r2.status_code}')
if r2.status_code == 200:
    body = r2.json()
    print(f'  ✅ Session: {body.get("session_id", "?")[:8]}...')
else:
    print(f'  ❌ Error: {r2.json()}')

r3 = client.post('/reset', json={'task_name': 'code_review'})
print(f'With data: {r3.status_code}')
if r3.status_code == 200:
    body = r3.json()
    print(f'  ✅ Session: {body.get("session_id", "?")[:8]}...')
else:
    print(f'  ❌ Error: {r3.json()}')
