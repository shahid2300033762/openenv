"""
Data Cleaning Example - Quick start

Shows how to systematically clean messy tabular data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tasks.data_cleaning.environment import DataCleaningEnvironment
from models import Action

# Initialize and reset
env = DataCleaningEnvironment()
obs = env.reset()

print("Dataset preview:", obs.data[:150], "...")

# Fix missing values
result = env.step(Action(
    action_type="fix_missing",
    value="fill_default",
    reasoning="Replace missing values with defaults"
))
print(f"Fix missing score: {result.reward.score:.2f}")

# Remove duplicates
result = env.step(Action(
    action_type="remove_duplicates",
    value="deduplicate",
    reasoning="Remove duplicate rows for data quality"
))
print(f"Dedupe score: {result.reward.score:.2f}")

# Normalize casing
result = env.step(Action(
    action_type="normalize_casing",
    value="title_case",
    reasoning="Standardize text casing"
))
print(f"Normalize score: {result.reward.score:.2f}")

# Fix formats
result = env.step(Action(
    action_type="fix_format",
    value="standardize",
    reasoning="Standardize date/email/zip formats"
))
print(f"Format score: {result.reward.score:.2f}")
print(f"Task complete: {result.done}")
