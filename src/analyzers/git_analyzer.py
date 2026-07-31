import os
from git import Repo
from pathlib import Path

repo_url = "https://github.com/IAmHarshit0/AnimeRecommendations"
local_path = "/home/iamha/projects/manager-exe/clone"

# 1. Robust Repository Management (Clones only if missing, else safely loads)
if not os.path.exists(os.path.join(local_path, ".git")):
    print(f"Cloning repository into {local_path}...")
    repo = Repo.clone_from(repo_url, local_path)
else:
    repo = Repo(local_path)

# Ensure we are pointing to a valid branch reference
assert not repo.bare, "Repository failed to load properly."

# # 2. Inspect Latest Commit Tree
tree = repo.head.commit.tree
# print(f"Latest Tree object: {tree}\n")

# # 3. Fetch History Safely (Fixed the list indexing bug from your original code)
# prev_commits = list(repo.iter_commits(all=True, max_count=10))
# if prev_commits:
#     tree = prev_commits[0].tree  # Fixed: Accessing the tree of the newest commit

# files_and_dirs = [(entry, entry.name, entry.type) for entry in tree]
# print("Files and Dirs in top commit:", files_and_dirs, "\n")

# 4. Streamlined Recursive Tree Visualizer
def print_files_from_git(root, level=0):
    for entry in root:
        indent = "    " * level
        prefix = "└── " if level > 0 else ""
        print(f"{indent}{prefix}{entry.name} [{entry.type}]")
        if entry.type == "tree":
            print_files_from_git(entry, level + 1)

print("--- Repository File Tree ---")
print_files_from_git(tree)
print()

# 5. Case-Insensitive Target File Tracking
target_file = "README.md"  # Fixed case sensitivity to match repository naming
commits_for_file_generator = repo.iter_commits(all=True, max_count=10, paths=target_file)
commits_for_file = list(commits_for_file_generator)
print(f"Commits touching {target_file}: {len(commits_for_file)}\n")

# 6. Optimized Chronological Logs
fifty_first_commits = list(repo.iter_commits("master", max_count=50))
print("--- Last 50 Commits ---")
for commit in fifty_first_commits:
    # Clean string extraction prevents multiline commit messages from breaking output format
    clean_message = commit.message.split('\n')[0][:50]
    print(f"Commit: {commit.hexsha[:7]} | Author: {commit.author.name} | Msg: {clean_message}")
print()

# 7. High-Speed Sequential Diff Analysis (Fixed the crash-heavy O(N²) nested loop)
print("--- Sequential Diffs (Newest to Oldest) ---")
for i in range(len(fifty_first_commits)):
    current = fifty_first_commits[i]
    
    # Handle the initial/root commit safely (which has no parents)
    parents = current.parents
    if not parents:
        # Diff against an empty tree string constants to see what files were born in commit 1
        diffs = current.diff(None, create_patch=False) 
    else:
        # Compare current against its immediate direct ancestor
        diffs = parents[0].diff(current)
        
    for diff in diffs:
        # Safely extract path status even if a file was entirely deleted/renamed
        status = diff.change_type
        path = diff.b_path if status == 'A' else diff.a_path
        print(f" [{status}] Commit {current.hexsha[:7]}: {path}")
