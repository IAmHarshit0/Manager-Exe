import os
import json 
from dateutil import parser

cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)

file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

first_commit_date = repo_context["history"]["first_commit_date"]
last_commit_date = repo_context["history"]["last_commit_date"]
generated_date = repo_context["repository"]["generated_at"]

# first/last_commit_date are None when local git analysis failed or the
# repo has no commits -- parser.parse(None) would raise, so fall back to
# "unknown" ratings instead of crashing the report.
if first_commit_date and last_commit_date:
    first_commit = parser.parse(first_commit_date)
    last_commit = parser.parse(last_commit_date)
    generated_at = parser.parse(generated_date)

    # Signal 1
    lifespan = (last_commit - first_commit).days
    velocity_signal = "Burst" if lifespan < 30 else "Incremental"

    # Signal 2
    gap = (generated_at - last_commit).days
    recency_signal = "Recent" if gap < 30 else "Stale"
else:
    lifespan = None
    velocity_signal = "Unknown"
    gap = None
    recency_signal = "Unknown"