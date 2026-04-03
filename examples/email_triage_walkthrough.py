"""
Email Triage Example - Quick start

Shows how to classify, prioritize, and respond to customer emails.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tasks.email_triage.environment import EmailTriageEnvironment
from models import Action

# Initialize and reset
env = EmailTriageEnvironment()
obs = env.reset()

print("Email:", obs.data[:100], "...")

# Step 1: Classify
result = env.step(Action(
    action_type="classify",
    value="complaint",
    reasoning="Customer expresses frustration about billing"
))
print(f"Classify score: {result.reward.score:.2f}")

# Step 2: Prioritize  
result = env.step(Action(
    action_type="prioritize",
    value="high",
    reasoning="Billing issues need urgent attention"
))
print(f"Priority score: {result.reward.score:.2f}")

# Step 3: Respond
result = env.step(Action(
    action_type="respond",
    value="Thank you for contacting us. We apologize for the billing issue and will resolve it within 24 hours.",
    reasoning="Professional, empathetic response with clear timeline"
))
print(f"Response score: {result.reward.score:.2f}")
print(f"Task complete: {result.done}")
