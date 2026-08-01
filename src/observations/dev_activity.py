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

first_commit = parser.parse(first_commit_date)
last_commit = parser.parse(last_commit_date)
generated_at = parser.parse(generated_date)

# Signal 1
lifespan = (last_commit - first_commit).days
if lifespan < 30:
    velocity_signal = "Burst"
else:
    velocity_signal = "Incremental"

# Signal 2
gap = (generated_at - last_commit).days
if gap < 30:
    recency_signal = "Recent"
else:
    recency_signal = "Stale"