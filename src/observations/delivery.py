import os
import json 

cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)

file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

UNIVERSAL_CONFIGS = [
    "requirements.txt", "environment.yml", "pyproject.toml", "setup.py",
    "package.json", "package-lock.json", "cargo.toml", "cargo.lock", 
    "pom.xml", "build.gradle", "go.mod", "go.sum"
]

UNIVERSAL_DATA_EXTENSIONS = [
    ".csv", ".parquet", ".pkl", ".h5", ".db", ".sqlite", ".sql", ".tsv"
]

# Signal 1
recent_commits = repo_context["commits"]["recent_commits"]

streak = 0
max_streak = 0

for i in reversed(recent_commits):
    changes = i["files_changed"]

    is_config = True
    
    if len(changes) == 0:
        is_config = False
    else:
        for j in changes:
            if j.lower() not in UNIVERSAL_CONFIGS:
                is_config = False
                break

    if is_config:
        streak += 1
        if streak > max_streak:
            max_streak = streak
    else:
        streak = 0

if max_streak <= 1:
    stability = "High"
elif max_streak == 2:
    stability = "Medium"
else:
    stability = "Low"


# Signal 2
root_elements = repo_context["files"]["root_elements"]

has_config = False
has_data = False

for i in root_elements:
    file = i.lower()
    if file in UNIVERSAL_CONFIGS:
        has_config = True

    extension = "." + file.split(".")[-1]
    if extension in UNIVERSAL_DATA_EXTENSIONS:
        has_data = True

    if extension == ".json" and ("mock" in file or "data" in file):
        has_data = True

if has_config and has_data:
    reproducibility = "High"
elif has_config:
    reproducibility = "Medium"
else:
    reproducibility = "Low"

