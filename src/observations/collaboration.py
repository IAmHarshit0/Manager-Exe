import os
import json 

cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)

file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

contributors_list = repo_context["contributors"]["contributors"]
total_devs = len(contributors_list)

# Signal 1
if total_devs == 1:
    authorship_score = "High"
elif total_devs == 2:
    authorship_score = "Medium"
else:
    authorship_score = "Low"

# Signal 2
recent_commits = repo_context["commits"]["recent_commits"]
total_commits = repo_context["history"]["total_commits"]
bulk = 0
for i in recent_commits:
    insertions = i["insertions"]
    if insertions >= 5000:
        bulk += 1
    else:
        continue

bulk_ratio = (bulk / total_commits) if total_commits > 0 else 0.0

if bulk_ratio <= 0.2:
    bulk_rating = "High"
elif bulk_ratio <= 0.4:
    bulk_rating = "Medium"
else:
    bulk_rating = "Low"

