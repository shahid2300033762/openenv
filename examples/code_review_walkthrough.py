"""
Code Review Example - Quick start

Shows how to identify security issues and suggest fixes.
Note: This task is intentionally challenging (scores 0.6-1.2 are normal).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tasks.code_review.environment import CodeReviewEnvironment
from models import Action

# Initialize and reset
env = CodeReviewEnvironment()
obs = env.reset()

print("Code to review:", obs.data[:200], "...")

# Identify SQL injection
result = env.step(Action(
    action_type="identify_issue",
    value="SQL injection vulnerability - user input directly interpolated into query using f-strings",
    reasoning="F-string formatting allows SQL injection attacks"
))
print(f"Identify issue score: {result.reward.score:.2f}")

# Suggest fix
result = env.step(Action(
    action_type="suggest_fix",
    value="Use parameterized queries with placeholders to prevent SQL injection",
    reasoning="Parameterized queries safely escape user input"
))
print(f"Suggest fix score: {result.reward.score:.2f}")

print("\nNote: Code Review uses semantic matching.")
print("Scores 0.6-1.2 are expected - this is a hard task by design!")
