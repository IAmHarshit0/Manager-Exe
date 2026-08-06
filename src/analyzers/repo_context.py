import json
import os
from datetime import datetime
from analyzers.github_analyzer import GithubAnalyzer
from analyzers.git_analyzer import LocalGitAnalyzer


def generate_repository_context(
    repo_url: str,
    local_path: str,
    output_filename: str = "repo_context.json",
    branch_name: str = "master",
    pull: bool = False,
    github_token: str = None,
):
    """Combines remote API analytics with deep local history mapping into a structured JSON file."""
    print("🚀 Initializing Git Context Compilation Workflow...")

    # 1. Initialize and execute Remote API analysis
    print("\n[1/4] Connecting to GitHub Remote API...")
    try:
        # Extracts owner/repo format from full URL for PyGithub compatibility
        repo_identifier = repo_url.replace("https://github.com", "").strip("/")
        if repo_identifier.endswith(".git"):
            repo_identifier = repo_identifier[:-4]

        remote_analyzer = GithubAnalyzer(token=github_token)
        remote_analyzer.load_repository(repo_identifier)
        remote_report = remote_analyzer.analyze()
        print(f"✅ Remote data fetched for: {remote_report['full_name']}")
    except Exception as e:
        print(f"⚠️ Remote analysis skipped/failed: {e}")
        remote_report = {"error": str(e)}

    # 2. Initialize and execute Local Repository analysis
    print("\n[2/4] Parsing Local Repository Storage Engine...")
    try:
        local_analyzer = LocalGitAnalyzer(
            repo_url=repo_url, local_path=local_path, branch_name=branch_name, pull=pull
        )
        local_report = local_analyzer.analyze(branch_name=branch_name)
        print(
            f"✅ Local history traced. Found {local_report['tree_summary']['total_files']} active tracking files."
        )
    except Exception as e:
        print(f"⚠️ Local analysis skipped/failed: {e}")
        local_report = {"error": str(e)}

    # 3. Structural Mold into Custom Unified Schema Format
    print("\n[3/4] Molding metrics into target JSON schema format...")
    
    # Safely unpack nested metrics to avoid KeyError anomalies if an analyzer failed
    remote_data = remote_report if "error" not in remote_report else {}
    local_data = local_report if "error" not in local_report else {}
    
    branch_sum = remote_data.get("branch_summary", {})
    file_sum = remote_data.get("file_summary", {})
    readme_sum = remote_data.get("readme_summary", {})
    remote_contrib_sum = remote_data.get("contributor_summary", {})

    tree_sum = local_data.get("tree_summary", {})
    hist_sum = local_data.get("history_summary", {})
    chg_sum = local_data.get("change_summary", {})
    local_contrib_sum = local_data.get("contributor_summary", {})

    # Prefer GitHub-native contributor data (aggregated across full remote history);
    # fall back to the local git log tally if the remote call failed or was skipped.
    if remote_contrib_sum.get("contributors"):
        contributors_block = {
            "source": "github_api",
            "total_contributors": remote_contrib_sum.get("total_contributors", 0),
            "contributors": remote_contrib_sum.get("contributors", []),
        }
    else:
        contributors_block = {
            "source": "local_git_log",
            "total_contributors": local_contrib_sum.get("total_contributors", 0),
            "contributors": local_contrib_sum.get("contributors", []),
            "commits_per_author": local_contrib_sum.get("commits_per_author", {}),
        }

    molded_context = {
        "repository": {
            "name": remote_data.get("repository_name"),
            "full_name": remote_data.get("full_name"),
            "description": remote_data.get("description"),
            "source_remote_url": repo_url,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        },
        "git": {
            "active_branch": branch_name,
            "default_branch": branch_sum.get("default_branch"),
            "latest_commit_sha": branch_sum.get("latest_commit_sha"),
            "total_branches": branch_sum.get("total_branches"),
            "all_branches": branch_sum.get("all_branches", [])
        },
        "history": {
            "analyzed_commits_count": hist_sum.get("analyzed_commits_count", 0),
            "total_commits": hist_sum.get("total_commits", 0),
            "first_commit_date": hist_sum.get("first_commit_date"),
            "last_commit_date": hist_sum.get("last_commit_date"),
            "latest_commit_details": hist_sum.get("latest_commit")
        },
        "commits": {
            "total_file_modifications": chg_sum.get("total_file_modifications", 0),
            "recent_commits": chg_sum.get("recent_commits", [])
        },
        "lines_changed": {
            "total_insertions": chg_sum.get("total_insertions", 0),
            "total_deletions": chg_sum.get("total_deletions", 0),
            "total_lines_changed": chg_sum.get("total_lines_changed", 0)
        },
        "contributors": contributors_block,
        "files": {
            "total_files": tree_sum.get("total_files", 0),
            "total_directories": tree_sum.get("total_directories", 0),
            "root_elements_count": file_sum.get("root_elements_count") or tree_sum.get("root_elements_count", 0),
            "root_elements": file_sum.get("root_elements") or tree_sum.get("root_elements", []),
            "file_extension_counts": tree_sum.get("extension_distribution", {})
        },
        "documentation": {
            "has_readme": readme_sum.get("has_readme", False),
            "readme_filename": readme_sum.get("readme_filename", "N/A"),
            "character_count": readme_sum.get("character_count", 0)
        }
    }

    # 4. Save compilation to external target storage file
    print(f"\n[4/4] Serializing matrix configuration to '{output_filename}'...")
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(molded_context, f, indent=4, ensure_ascii=False)
        print(f"🎉 Context compilation complete! Output file written.")
    except Exception as e:
        print(f"❌ Failed writing context data block matrix to disk: {e}")