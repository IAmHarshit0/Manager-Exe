import os
import json 

cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)

file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

# Signal 1
readme_presence = repo_context["documentation"]["has_readme"]

# Signal 2
doc_to_code = repo_context["files"]["file_extension_counts"][".md"] / (repo_context["files"]["file_extension_counts"][".py"] + repo_context["files"]["file_extension_counts"][".ipynb"])
doc_density = repo_context["documentation"]["character_count"]/repo_context["files"]["total_files"]

if doc_to_code > 0.5 and doc_density > 150:
    documentation_quality = "High"
elif doc_to_code > 0.1 and doc_density > 50:
    documentation_quality = "Medium"
else:
    documentation_quality = "Low"
