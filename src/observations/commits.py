import os
import json
import re

# 1. Load context payload safely
cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)
file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

recent_commits = repo_context["commits"]["recent_commits"]
total_commits = len(recent_commits)

# Strict regex matching conventional commit pattern (e.g., feat:, chore(api):)
conventional_regex = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|chore)(\(.+\))?:", re.IGNORECASE)

semantic_count = 0
violations = 0

for commit in recent_commits:
    commit_message = commit["message"]
    if conventional_regex.match(commit_message):
        semantic_count += 1

    files_changed = commit["files_changed"]
    
    commit_extensions = set() 
    for file in files_changed:
        # Split extension and keep only valid ones (ignore files without an extension)
        parts = file.split(".")
        if len(parts) > 1:
            commit_extensions.add(parts[-1])
            
    if len(commit_extensions) > 1:
        violations += 1

# Calculate Signal 3A Rating
if total_commits > 0:
    semantic_ratio = semantic_count / total_commits
    if semantic_ratio > 0.8:
        semantic_signal = "High"
    elif semantic_ratio > 0.5:
        semantic_signal = "Medium"
    else:
        semantic_signal = "Low"
else:
    semantic_signal = "No Commits"

# Calculate Signal 3B Rating
if violations > 3:
    atomicity_signal = "High Violation"
elif violations > 1:
    atomicity_signal = "Medium Violation"
else:
    atomicity_signal = "Low Violation"
