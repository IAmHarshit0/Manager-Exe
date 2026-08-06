import os
import shutil
from dataclasses import dataclass, asdict, field
from typing import List, Optional
from git import Repo


@dataclass
class Commit:
    """Unified representation of a single commit's metadata and change footprint."""
    sha: str
    short_sha: str
    author: str
    date: str
    message: str
    files_changed: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class LocalGitAnalyzer:

    def __init__(
        self,
        repo_url: str,
        local_path: str,
        branch_name: Optional[str] = None,
        pull: bool = False,
    ):
        """Initializes and handles local cloning or loading of a Git repository.

        branch_name: if provided and `pull=True`, checked out before pulling
        so the pull lands on the branch you're about to analyze rather than
        whatever branch happened to be checked out already.
        pull: if True and the repo already exists locally, fetch + pull
        before analyzing. Off by default -- an already-cloned repo is
        otherwise loaded as-is with no network calls.
        """
        self.repo_url = repo_url
        self.local_path = local_path
        self.branch_name = branch_name
        self.pull = pull
        self.repo = self._initialize_repo()

    def _initialize_repo(self) -> Repo:
        """Robust Repository Management: Clones only if missing, else safely loads."""
        if not os.path.exists(os.path.join(self.local_path, ".git")):
            print(f"Cloning repository into {self.local_path}...")
            repo = Repo.clone_from(self.repo_url, self.local_path)
        else:
            print(f"Loading existing repository from {self.local_path}...")
            repo = Repo(self.local_path)

            if self._remote_mismatch(repo):
                repo = self._reclone_mismatched_repo(repo)
            elif self.pull:
                self._pull_latest(repo)

        assert not repo.bare, "Repository failed to load properly."
        return repo

    @staticmethod
    def _normalize_git_url(url: str) -> str:
        """Loose normalization so http vs https, trailing slash, trailing
        .git, and the ssh (git@host:owner/repo) vs https form all compare
        equal."""
        url = url.strip().rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        if url.startswith("git@"):
            url = url.replace(":", "/", 1).replace("git@", "https://", 1)
        return url.lower()

    def _remote_mismatch(self, repo: Repo) -> bool:
        """True if local_path's origin points somewhere other than
        repo_url. If there's no origin remote to compare against, treat it
        as not-mismatched -- there's nothing to contradict repo_url."""
        try:
            origin_url = next(repo.remotes.origin.urls)
        except Exception:
            return False
        return self._normalize_git_url(origin_url) != self._normalize_git_url(self.repo_url)

    def _reclone_mismatched_repo(self, repo: Repo) -> Repo:
        """local_path holds a different repository than the one requested.
        If the working tree is clean, wipe it and clone the correct repo
        fresh. If there are uncommitted changes, stop instead of risking
        deleting work that hasn't been committed anywhere."""
        try:
            origin_url = next(repo.remotes.origin.urls)
        except Exception:
            origin_url = "(unknown remote)"

        if repo.is_dirty(untracked_files=True):
            raise RuntimeError(
                f"'{self.local_path}' contains a different repository ({origin_url}) "
                f"than requested ({self.repo_url}), and it has uncommitted changes -- "
                f"refusing to delete it automatically. Commit/stash your changes, point "
                f"local_path elsewhere, or remove the folder manually and re-run."
            )

        print(
            f"⚠️ '{self.local_path}' holds a different repository ({origin_url}) than "
            f"requested ({self.repo_url}). Re-cloning..."
        )
        shutil.rmtree(self.local_path)
        return Repo.clone_from(self.repo_url, self.local_path)

    def _pull_latest(self, repo: Repo) -> None:
        """Fetches and pulls the latest changes for an already-cloned repository.
        Failures (no remote, diverged history, dirty working tree, etc.) are
        reported but non-fatal -- analysis proceeds on whatever was already
        on disk, same as if `pull` had been False."""
        try:
            origin = repo.remotes.origin
            print(f"Fetching latest changes for {self.local_path}...")
            origin.fetch()
            if self.branch_name and self.branch_name in repo.heads:
                repo.heads[self.branch_name].checkout()
            origin.pull()
            print(f"✅ Pulled latest changes ({repo.head.commit.hexsha[:7]}).")
        except Exception as e:
            print(f"⚠️ Pull skipped/failed: {e}")

    def get_file_tree(self) -> list:
        """Traverses the latest commit tree recursively and returns structured entries."""
        tree = self.repo.head.commit.tree
        flat_tree = []

        def _traverse(root, level=0):
            for entry in root:
                flat_tree.append(
                    {"name": entry.name, "type": entry.type, "level": level}
                )
                if entry.type == "tree":
                    _traverse(entry, level + 1)

        _traverse(tree)
        return flat_tree

    def print_file_tree(self):
        """Prints a streamlined visual representation of the repository tree."""
        tree_entries = self.get_file_tree()
        for entry in tree_entries:
            indent = "    " * entry["level"]
            prefix = "└── " if entry["level"] > 0 else ""
            print(f"{indent}{prefix}{entry['name']} [{entry['type']}]")

    def get_file_commit_count(self, target_file: str = "README.md") -> int:
        """Finds commits touching a specific target file using case-insensitive validation."""
        # Find matching filename case-sensitivities inside the current tree
        tree = self.repo.head.commit.tree
        actual_path = target_file

        for entry in tree:
            if entry.name.lower() == target_file.lower():
                actual_path = entry.name
                break

        commits = list(
            self.repo.iter_commits(all=True, max_count=10, paths=actual_path)
        )
        return len(commits)

    def get_commits(self, branch_name: str = "master", limit: int = 50) -> List[Commit]:
        """Builds a unified list of Commit objects: metadata + changed files + line stats."""
        commits = list(self.repo.iter_commits(branch_name, max_count=limit))
        result = []

        for commit in commits:
            parents = commit.parents

            if not parents:
                diffs = commit.diff(None, create_patch=False)
            else:
                diffs = parents[0].diff(commit)

            files_changed = [
                diff.b_path if diff.change_type == "A" else diff.a_path
                for diff in diffs
            ]

            stats = commit.stats.total
            clean_message = commit.message.split("\n")[0][:50]

            result.append(
                Commit(
                    sha=commit.hexsha,
                    short_sha=commit.hexsha[:7],
                    author=commit.author.name,
                    date=commit.committed_datetime.isoformat(),
                    message=clean_message,
                    files_changed=files_changed,
                    insertions=stats.get("insertions", 0),
                    deletions=stats.get("deletions", 0),
                )
            )
        return result

    def get_commit_date_range(self, branch_name: str = "master") -> dict:
        """Walks the full branch history to determine the first and last commit timestamps."""
        commits = list(self.repo.iter_commits(branch_name))

        if not commits:
            return {"first_commit_date": None, "last_commit_date": None, "total_commits": 0}

        # iter_commits yields newest-first, so index 0 is the last commit and -1 is the first
        last_commit = commits[0]
        first_commit = commits[-1]

        return {
            "first_commit_date": first_commit.committed_datetime.isoformat(),
            "last_commit_date": last_commit.committed_datetime.isoformat(),
            "total_commits": len(commits),
        }

    def get_contributor_stats(self, branch_name: str = "master") -> dict:
        """Aggregates unique contributors and per-author commit counts across full history."""
        commits = list(self.repo.iter_commits(branch_name))
        commits_per_author = {}

        for commit in commits:
            author_name = commit.author.name or "Unknown"
            author_email = commit.author.email or "unknown"
            key = f"{author_name} <{author_email}>"
            commits_per_author[key] = commits_per_author.get(key, 0) + 1

        # Sort contributors by commit count, most active first
        sorted_authors = sorted(
            commits_per_author.items(), key=lambda item: item[1], reverse=True
        )

        return {
            "total_contributors": len(commits_per_author),
            "contributors": [name for name, _ in sorted_authors],
            "commits_per_author": dict(sorted_authors),
        }

    def analyze(self, branch_name: str = "master") -> dict:
        """Compiles a comprehensive summary report of the local repository matrix."""
        file_tree = self.get_file_tree()

        # Count types
        total_files = sum(1 for item in file_tree if item["type"] == "blob")
        total_dirs = sum(1 for item in file_tree if item["type"] == "tree")

        # Extensions tracking
        extensions = {}
        for item in file_tree:
            if item["type"] == "blob":
                _, ext = os.path.splitext(item["name"])
                ext = ext.lower() if ext else "no_extension"
                extensions[ext] = extensions.get(ext, 0) + 1

        commits = self.get_commits(branch_name)
        commit_dicts = [c.to_dict() for c in commits]
        date_range = self.get_commit_date_range(branch_name)
        contributor_stats = self.get_contributor_stats(branch_name)

        total_files_modified = sum(len(c.files_changed) for c in commits)
        total_insertions = sum(c.insertions for c in commits)
        total_deletions = sum(c.deletions for c in commits)

        root_elements = [item["name"] for item in file_tree if item["level"] == 0]

        return {
            "repository_path": self.local_path,
            "active_branch": branch_name,
            "tree_summary": {
                "total_files": total_files,
                "total_directories": total_dirs,
                "extension_distribution": extensions,
                "root_elements_count": len(root_elements),
                "root_elements": root_elements,
            },
            "history_summary": {
                "analyzed_commits_count": len(commits),
                "latest_commit": commit_dicts[0] if commit_dicts else None,
                "first_commit_date": date_range["first_commit_date"],
                "last_commit_date": date_range["last_commit_date"],
                "total_commits": date_range["total_commits"],
            },
            "change_summary": {
                "total_file_modifications": total_files_modified,
                "total_insertions": total_insertions,
                "total_deletions": total_deletions,
                "total_lines_changed": total_insertions + total_deletions,
                "recent_commits": commit_dicts[:10],  # Return up to the latest 10 Commit objects
            },
            "contributor_summary": {
                "total_contributors": contributor_stats["total_contributors"],
                "contributors": contributor_stats["contributors"],
                "commits_per_author": contributor_stats["commits_per_author"],
            },
        }