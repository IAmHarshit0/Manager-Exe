from github import Github
from github import Auth 
import os
from dotenv import load_dotenv

load_dotenv()

auth = Auth.Token(os.getenv("GithubToken"))
g = Github(auth=auth)

user = g.get_user()
print(f"User: {user.login}")
repo_url = "IAmHarshit0/AnimeRecommendations"
repo = g.get_repo(repo_url)
print(f"Repository: {repo.name}")

# Fetch initial root contents
contents = repo.get_contents("")

# Create a copy for the tree traversal so 'contents' isn't emptied out
queue = list(contents)

print("\n--- Root Directory Contents ---")
for content in contents:
    print(content.path)

print("\n--- Full Repository Tree Walking ---")
while queue: 
    file = queue.pop(0)
    if file.type == "dir":
        queue.extend(repo.get_contents(file.path))
    else:
        print(f"File: {file.path}")

print(f"\nBranches: {list(repo.get_branches())}")

# 1. Dynamically get the repository's default branch (handles main, master, dev, etc.)
default_branch = repo.default_branch
print(f"Default branch identified: {default_branch}")

branch = repo.get_branch(default_branch)
print(f"Default branch commit: {branch.commit}")

print("\n--- Reading README Content ---")
try:
    # 2. List top-level files to find any README variation (e.g., README.md, readme.MD, README.txt)
    repo_files = repo.get_contents("")
    readme_file = None

    for file in repo_files:
        if file.name.lower().startswith("readme"):
            readme_file = file
            break

    # 3. Read the file if found, otherwise throw an error
    if readme_file:
        print(f"Found file: {readme_file.name}")
        readme_text = readme_file.decoded_content.decode("utf-8")
        print(readme_text)
    else:
        print("Could not find any README file in the root directory.")

except Exception as e:
    print(f"Error reading README: {e}")
