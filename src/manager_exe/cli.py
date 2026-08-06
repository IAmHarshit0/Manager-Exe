"""
Command-line interface for manager-exe.

This module only orchestrates the existing analyzer / report / evaluation
pipeline -- none of that internal logic is changed.

Note on cwd handling: `slm/report.py` locates `repo_context.json` by walking
two directories up from `os.getcwd()` (i.e. it assumes it's being run from
inside `src/slm`), and going by the same pattern it likely relies on
`observations/*.py` doing something similar. Rather than rewrite path
resolution across files I haven't seen, the `report` and `evaluate` commands
below `chdir` into `src/slm` before importing that code, so the existing
relative-path assumption keeps holding regardless of where `manager-exe`
itself is invoked from. If `observations/*.py` turns out to resolve paths
differently, that assumption will need revisiting.
"""

import argparse
import os
import sys
from pathlib import Path

# src/manager_exe/cli.py -> src/manager_exe -> src -> project root
PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
SLM_DIR = SRC_DIR / "slm"


def _ensure_src_on_path() -> None:
    """analyzers/, observations/, and slm/ are imported as top-level
    packages (see repo_context.py's `from analyzers...` and report.py's
    `from observations...`), which only works if `src/` is on sys.path.
    An editable install normally provides this via uv/pip, but we add it
    defensively so `manager-exe` also behaves under a plain
    `python -m manager_exe` invocation."""
    src_str = str(SRC_DIR)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


def cmd_scan(args: argparse.Namespace) -> None:
    _ensure_src_on_path()
    from analyzers.repo_context import generate_repository_context

    output_path = args.output or str(PROJECT_ROOT / "repo_context.json")
    generate_repository_context(
        repo_url=args.repo_url,
        local_path=args.local_path,
        output_filename=output_path,
        branch_name=args.branch,
        pull=args.pull,
        github_token=args.github_token,
    )


def cmd_report(args: argparse.Namespace) -> None:
    _ensure_src_on_path()
    original_cwd = os.getcwd()
    os.chdir(SLM_DIR)
    try:
        from slm.report import generate_observation_report

        print(generate_observation_report())
    finally:
        os.chdir(original_cwd)


def cmd_evaluate(args: argparse.Namespace) -> None:
    _ensure_src_on_path()
    original_cwd = os.getcwd()
    os.chdir(SLM_DIR)
    try:
        from slm.prompt import gen_prompt
        import ollama

        # Explicit Client(host=...) when --host/$MANAGER_EXE_OLLAMA_HOST/$OLLAMA_HOST
        # is set, otherwise ollama's own default client (localhost:11434).
        client = ollama.Client(host=args.host) if args.host else ollama

        prompt = gen_prompt()
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "What is your evaluation?"
                ),
            },
        ]

        try:
            response = client.chat(model=args.model, messages=messages)
        except ollama.ResponseError as e:
            if e.status_code == 404:
                raise SystemExit(
                    f"Model '{args.model}' isn't available on the Ollama server. "
                    f"Pull it first with: ollama pull {args.model}\n"
                    f"Or point at a different model with --model."
                ) from e
            raise SystemExit(f"Ollama returned an error: {e}") from e
        except ConnectionError as e:
            host_desc = args.host or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
            raise SystemExit(
                f"Couldn't reach an Ollama server at {host_desc}. Is it running? "
                f"Start it with: ollama serve\n"
                f"Or point at a different server with --host / $OLLAMA_HOST."
            ) from e

        print(response.message.content)
    finally:
        os.chdir(original_cwd)


def cmd_run(args: argparse.Namespace) -> None:
    """Convenience: scan -> report -> evaluate in one shot."""
    cmd_scan(args)
    cmd_report(args)
    cmd_evaluate(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manager-exe",
        description="Analyze a git repository and get an AI-generated portfolio evaluation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_p = subparsers.add_parser(
        "scan", help="Fetch remote + local git data into repo_context.json"
    )
    scan_p.add_argument("repo_url", help="e.g. https://github.com/owner/repo")
    scan_p.add_argument("local_path", help="Path to the local clone")
    scan_p.add_argument(
        "--branch", default="master", help="Branch to analyze (default: master)"
    )
    scan_p.add_argument(
        "--output",
        default=None,
        help="Output path for repo_context.json (default: project root)",
    )
    scan_p.add_argument(
        "--pull",
        action="store_true",
        help="If the local clone already exists, fetch + pull the given branch before analyzing",
    )
    scan_p.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GithubToken"),
        help="GitHub personal access token for the remote API step "
        "(default: $GITHUB_TOKEN, legacy $GithubToken, or a .env file in the cwd)",
    )
    scan_p.set_defaults(func=cmd_scan)

    report_p = subparsers.add_parser(
        "report", help="Print the narrative observation report from repo_context.json"
    )
    report_p.set_defaults(func=cmd_report)

    eval_p = subparsers.add_parser(
        "evaluate", help="Run the local LLM evaluation over the observation report"
    )
    eval_p.add_argument(
        "--model",
        default=os.environ.get("MANAGER_EXE_OLLAMA_MODEL", "qwen3.5:4b"),
        help="Ollama model tag (default: $MANAGER_EXE_OLLAMA_MODEL or qwen3.5:4b)",
    )
    eval_p.add_argument(
        "--host",
        default=os.environ.get("MANAGER_EXE_OLLAMA_HOST") or os.environ.get("OLLAMA_HOST"),
        help="Ollama server URL, e.g. http://localhost:11434 "
        "(default: $MANAGER_EXE_OLLAMA_HOST or $OLLAMA_HOST, else ollama's own default)",
    )
    eval_p.set_defaults(func=cmd_evaluate)

    run_p = subparsers.add_parser(
        "run", help="Run scan, report, and evaluate in sequence"
    )
    run_p.add_argument("repo_url", help="e.g. https://github.com/owner/repo")
    run_p.add_argument("local_path", help="Path to the local clone")
    run_p.add_argument(
        "--branch", default="master", help="Branch to analyze (default: master)"
    )
    run_p.add_argument(
        "--output",
        default=None,
        help="Output path for repo_context.json (default: project root)",
    )
    run_p.add_argument(
        "--model",
        default=os.environ.get("MANAGER_EXE_OLLAMA_MODEL", "qwen3.5:4b"),
        help="Ollama model tag (default: $MANAGER_EXE_OLLAMA_MODEL or qwen3.5:4b)",
    )
    run_p.add_argument(
        "--host",
        default=os.environ.get("MANAGER_EXE_OLLAMA_HOST") or os.environ.get("OLLAMA_HOST"),
        help="Ollama server URL (default: $MANAGER_EXE_OLLAMA_HOST or $OLLAMA_HOST)",
    )
    run_p.add_argument(
        "--pull",
        action="store_true",
        help="If the local clone already exists, fetch + pull the given branch before analyzing",
    )
    run_p.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GithubToken"),
        help="GitHub personal access token for the remote API step "
        "(default: $GITHUB_TOKEN, legacy $GithubToken, or a .env file in the cwd)",
    )
    run_p.set_defaults(func=cmd_run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()