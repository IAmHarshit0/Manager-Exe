import os
from github import Github, Auth
from dotenv import load_dotenv, find_dotenv

class GithubAnalyzer:
    def __init__(self, token: str = None):
        """Initializes the GitHub client using an explicit token, an
        environment variable, or a .env file found starting from the
        current working directory. Using usecwd=True (rather than
        find_dotenv()'s default, which searches from this file's own
        location) matters once manager-exe is pip-installed: this file
        then lives in site-packages, far from the user's actual project
        and .env file."""
        if not token:
            load_dotenv(find_dotenv(usecwd=True))
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GithubToken")

        if not token:
            raise ValueError(
                "GitHub Token not found. Provide it via --github-token, "
                "set GITHUB_TOKEN (or the legacy GithubToken) in your "
                "environment, or add it to a .env file in your working "
                "directory."
            )

        self.auth = Auth.Token(token)
        self.g = Github(auth=self.auth)
        self.repo = None

    def load_repository(self, repo_url: str):
        """Connects to a specific repository."""
        self.repo = self.g.get_repo(repo_url)
        return self.repo

    def get_user_login(self) -> str:
        """Returns the authenticated user's login name."""
        return self.g.get_user().login

    def get_root_contents(self) -> list:
        """Returns a list of ContentFile objects from the root directory."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")
        return self.repo.get_contents("")

    def walk_repository_tree(self) -> list:
        """Traverses all directories and returns paths of all files in the repository."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")
        
        root_contents = self.get_root_contents()
        queue = list(root_contents)
        all_files = []
        
        while queue:
            file = queue.pop(0)
            if file.type == "dir":
                queue.extend(self.repo.get_contents(file.path))
            else:
                all_files.append(file.path)
                
        return all_files

    def get_branches(self) -> list:
        """Returns a list of all branch names in the repository."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")
        return [branch.name for branch in self.repo.get_branches()]

    def get_default_branch_commit(self) -> tuple:
        """Returns the default branch name and its latest commit SHA."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")
        
        default_branch = self.repo.default_branch
        branch = self.repo.get_branch(default_branch)
        return default_branch, branch.commit.sha

    def get_contributors(self) -> list:
        """Returns GitHub-native contributor logins with their total contribution counts."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")

        try:
            contributors = self.repo.get_contributors()
            return [
                {"login": c.login, "contributions": c.contributions}
                for c in contributors
            ]
        except Exception:
            # Some repos (e.g. very large ones) can throw on this endpoint; fail soft
            return []

    def read_readme(self) -> dict:
        """Finds and reads any case-insensitive variation of the README file."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")
            
        try:
            repo_files = self.get_root_contents()
            readme_file = None
            
            for file in repo_files:
                if file.name.lower().startswith("readme"):
                    readme_file = file
                    break
                    
            if readme_file:
                return {
                    "success": True,
                    "filename": readme_file.name,
                    "content": readme_file.decoded_content.decode("utf-8")
                }
            return {
                "success": False,
                "error": "Could not find any README file in the root directory."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze(self) -> dict:
        """Compiles a comprehensive summary report of the loaded repository."""
        if not self.repo:
            raise ValueError("No repository loaded. Call load_repository() first.")

        # Gather root items
        root_items = self.get_root_contents()
        root_paths = [item.path for item in root_items]

        # Gather total files and file extensions
        all_files = self.walk_repository_tree()
        extensions = {}
        for file_path in all_files:
            _, ext = os.path.splitext(file_path)
            if ext:
                ext = ext.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
            else:
                extensions["no_extension"] = extensions.get("no_extension", 0) + 1

        # Gather branch metadata
        default_branch, latest_sha = self.get_default_branch_commit()
        all_branches = self.get_branches()

        # Gather README status
        readme_info = self.read_readme()
        has_readme = readme_info["success"]
        readme_name = readme_info.get("filename", "N/A")

        # Gather contributor stats (GitHub-native, aggregated across full history)
        contributors = self.get_contributors()

        # Compile JSON/Dict report structure
        report = {
            "repository_name": self.repo.name,
            "full_name": self.repo.full_name,
            "description": self.repo.description,
            "branch_summary": {
                "default_branch": default_branch,
                "latest_commit_sha": latest_sha,
                "total_branches": len(all_branches),
                "all_branches": all_branches
            },
            "file_summary": {
                "total_files": len(all_files),
                "root_elements_count": len(root_paths),
                "root_elements": root_paths,
                "file_extension_counts": extensions
            },
            "readme_summary": {
                "has_readme": has_readme,
                "readme_filename": readme_name,
                "character_count": len(readme_info["content"]) if has_readme else 0
            },
            "contributor_summary": {
                "total_contributors": len(contributors),
                "contributors": contributors
            }
        }
        return report