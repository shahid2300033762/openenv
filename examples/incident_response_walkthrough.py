"""
Incident Response Example - Quick start

Shows how to handle cybersecurity incidents through the full lifecycle.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tasks.incident_response.environment import IncidentResponseEnvironment
from models import Action

# Initialize and reset
env = IncidentResponseEnvironment()
obs = env.reset()

print("Incident:", obs.instructions[:100], "...")
print("Logs:", obs.data[:150], "...")

# Detect attack
result = env.step(Action(
    action_type="detect",
    value="SQL injection attack",
    reasoning="Logs show SQL injection attempts in web requests"
))
print(f"Detection score: {result.reward.score:.2f}")

# Analyze indicators
result = env.step(Action(
    action_type="analyze",
    value="Attacker IP: 203.0.113.45, malicious SQL payloads in POST requests",
    reasoning="Identified IoCs from log analysis"
))
print(f"Analysis score: {result.reward.score:.2f}")

# Contain threat
result = env.step(Action(
    action_type="contain",
    value="Block IP at firewall, isolate affected web server, disable vulnerable endpoint",
    reasoning="Immediate containment to stop attack"
))
print(f"Containment score: {result.reward.score:.2f}")

# Remediate
result = env.step(Action(
    action_type="remediate",
    value="Patch application with parameterized queries, update WAF rules, rotate credentials",
    reasoning="Long-term fixes to prevent recurrence"
))
print(f"Remediation score: {result.reward.score:.2f}")

# Document
result = env.step(Action(
    action_type="document",
    value="SQL injection from 203.0.113.45. Blocked IP, patched code, updated security controls.",
    reasoning="Complete incident report for compliance"
))
print(f"Documentation score: {result.reward.score:.2f}")
print(f"Task complete: {result.done}")
