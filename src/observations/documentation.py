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
# .get(..., 0) instead of direct key access: a repo with no markdown files
# (no ".md" key at all) or no ".py"/".ipynb" files (e.g. a non-Python repo)
# would otherwise raise a KeyError here.
extension_counts = repo_context["files"]["file_extension_counts"]
md_count = extension_counts.get(".md", 0)
code_count = extension_counts.get(".py", 0) + extension_counts.get(".ipynb", 0)
total_files = repo_context["files"]["total_files"]

doc_to_code = (md_count / code_count) if code_count > 0 else 0.0
doc_density = (repo_context["documentation"]["character_count"] / total_files) if total_files > 0 else 0.0

if doc_to_code > 0.5 and doc_density > 150:
    documentation_quality = "High"
elif doc_to_code > 0.1 and doc_density > 50:
    documentation_quality = "Medium"
else:
    documentation_quality = "Low"