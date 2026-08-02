import os
import json 

cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)

file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

root = repo_context["files"]["root_elements"]

WORKSPACE_RULES = {
    # --- LEVEL 1: ALLOWED ROOT ITEMS (Does NOT increase pollution score) ---
    "allowed_configs": [
        ".gitignore",         # Git ignore profiles
        "requirements.txt",   # Pip dependencies
        "environment.yml",    # Anaconda environments
        "setup.py",           # Legacy python packaging
        "pyproject.toml",     # Modern python packaging
        "dockerfile",         # Container settings
        "docker-compose.yml", # Multi-container setups
        "makefile",           # Build automation scripts
        "package.json",       # Node.js dependencies
        "cargo.toml",         # Rust package config
        "go.mod",             # Go module config
        ".env.example"        # Safe environment templates
    ],
    
    "allowed_docs": [
        "readme.md",          # Standard documentation
        "readme.txt",         # Plain text documentation
        "contributing.md",    # Open source contribution guides
        "changelog.md",       # Version history logs
        "license",            # Legal permissions
        "license.md",
        "license.txt"
    ],

    # --- LEVEL 2: ENVIRONMENT LEAKS (Triggers the 4B Boolean Flag) ---
    "environment_leaks": [
        "__pycache__",        # Python compiled code caches
        ".venv",              # Python local virtual environments
        "venv",
        "env",
        ".env",               # CRITICAL: Secret keys/passwords leak
        ".pytest_cache",      # Testing framework runtime data
        ".vscode",            # Visual Studio Code editor settings
        ".idea",              # PyCharm/IntelliJ editor settings
        ".ipynb_checkpoints", # Jupyter Notebook auto-saves
        "node_modules",       # Node.js heavy local packages
        ".ds_store"           # MacOS system layout clutter
    ]
}

# Signal 1 & 2
pollution = 0
env_leak = False
for i in root:
    if i.lower() in WORKSPACE_RULES["allowed_configs"] or i.lower() in WORKSPACE_RULES["allowed_docs"]:
        continue
    elif i in WORKSPACE_RULES["environment_leaks"]:
        env_leak = True
    else:
        pollution += 1

if pollution <= 2:
    root_score = "Low Risk"
elif pollution <= 5:
    root_score = "Medium Risk"
else:
    root_score = "High Risk"
