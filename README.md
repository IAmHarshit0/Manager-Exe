# manager-exe

Analyzes a GitHub repository (remote metadata + local git history) and produces
an AI-generated portfolio/engineering review, using a local Ollama model.

## Install

```bash
git clone <this-repo>
cd manager-exe
uv sync
```

## Configure

**GitHub token** (needed for the remote-data step -- unauthenticated GitHub API
calls are capped at 60/hour and will fail fast). Set one of:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```
or a `.env` file in the directory you run `manager-exe` from:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```
or pass it per-command with `--github-token`.

**Ollama model.** Defaults to `llama3.2:latest` against `http://localhost:11434`.
Override either:
```bash
export MANAGER_EXE_OLLAMA_MODEL=mistral:latest
export MANAGER_EXE_OLLAMA_HOST=http://localhost:11434   # or a remote Ollama server
```
or per-command with `--model` / `--host`. Make sure the model is pulled first:
```bash
ollama pull llama3.2:latest
```

## Usage

```bash
# 1. Fetch remote + local git data into repo_context.json
uv run manager-exe scan <repo_url> <local_clone_path> [--branch master] [--pull]

# 2. Print the narrative observation report built from that data
uv run manager-exe report

# 3. Get the AI evaluation of that report
uv run manager-exe evaluate

# Or all three in one shot:
uv run manager-exe run <repo_url> <local_clone_path> --pull
```

`--pull` fetches + pulls the branch if `<local_clone_path>` already exists.
If that path holds a *different* repo than the one you asked for, it's
automatically re-cloned (unless it has uncommitted changes, in which case
you'll get an error instead of losing work).

### Example

```bash
uv run manager-exe run https://github.com/owner/repo.git ./clone --pull
```

## Notes

- `scan` works fully offline from GitHub if no token is available -- it just
  skips the remote step and reports on local git history only.
- `clone` is analyzed at whatever commit it's at; `--pull` keeps it current.