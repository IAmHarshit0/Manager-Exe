# manager-exe

**Offline repository analysis and engineering review powered by local language models.**

`manager-exe` analyzes a GitHub repository using a combination of **GitHub metadata** and **local Git history**, converts the raw data into deterministic engineering observations, and passes those observations to a **local language model through Ollama** for interpretation.

The result is an engineering review that can be explored interactively through the CLI or a Streamlit dashboard.

> The goal of this project is not to have an LLM "read a codebase and judge it."
>
> The goal is to give a small local language model structured engineering evidence and let it reason about what that evidence means.

---

## What It Does

`manager-exe` follows a simple pipeline:

```text
GitHub Repository
       │
       ├── GitHub API ────────┐
       │                      │
       └── Local Git ─────────┤
                              ▼
                       Repository Context
                              │
                              ▼
                    Deterministic Analysis
                              │
                              ▼
                     Observation Report
                              │
                              ▼
                       Local Ollama Model
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Engineering Review          Interactive Chat
```

The analysis is deliberately split into two responsibilities:

**Deterministic analysis** answers:

> "What can we observe from the repository?"

**The language model** answers:

> "What might these observations mean?"

This separation keeps the model from being responsible for basic repository analysis and makes the resulting system easier to inspect, test, and reason about.

---

# Why I Built This

This project started as an experiment around the idea of an offline "roast my GitHub" tool.

The initial idea was simple: give a repository to an LLM and ask it to review the project.

That approach quickly raised a problem.

A language model should not have to independently discover every fact about a repository before it can reason about the repository. It also makes the analysis difficult to reproduce because the model can interpret the same repository differently from one run to another.

So the project evolved into a small engineering pipeline:

1. Gather repository metadata.
2. Inspect local Git history.
3. Convert raw data into deterministic observations.
4. Attach evidence to every observation.
5. Produce a structured engineering report.
6. Benchmark several small language models against the same report.
7. Select a local model based on the quality of its engineering interpretation.
8. Allow the user to interact with the resulting analysis.

The current project is the result of that iteration.

---

# Architecture

The project currently has four major stages.

## 1. Repository Analysis

The first stage gathers information from two sources.

### GitHub

The GitHub layer provides remote repository information such as:

* Repository name
* Description
* Repository structure
* Branches
* Contributors
* README presence
* File information
* Other available repository metadata

### Git

The local Git analyzer works against a local clone and extracts information from the repository history, including:

* Commit hashes
* Authors
* Commit dates
* Commit messages
* Changed files
* Insertions
* Deletions
* Commit-to-commit differences
* Repository activity history

A local clone is used deliberately because Git history contains information that is not available from the basic GitHub repository metadata alone.

The resulting information is stored in:

```text
repo_context.json
```

This file acts as the raw analytical context for the rest of the system.

---

# 2. Observation Engine

Raw repository data is not directly sent to the language model.

Instead, `manager-exe` runs a deterministic observation engine over the collected data.

The observation engine currently evaluates six engineering areas:

| Area                     | Signals                                      |
| ------------------------ | -------------------------------------------- |
| Collaboration            | Authorship Score, Bulk Rating                |
| Commit Quality           | Semantic Hygiene, Layer Atomicity            |
| Workspace / Architecture | Root Pollution, Environment Runtime Leaks    |
| Delivery                 | Dependency Stability, Reproducibility        |
| Development Activity     | Velocity, Recency                            |
| Documentation            | Documentation Quality, Documentation Density |

Each observation produces:

* A human-readable status
* An explanation of what the signal represents
* Evidence supporting the observation

For example:

```text
SIGNAL: Root Pollution Score
STATUS: High Risk
EXPLANATION: ...
EVIDENCE: Detected 6 unorganized code/data elements...
```

The observation engine is intentionally deterministic.

Given the same repository context, it should produce the same observations.

This creates a boundary between **measurement** and **interpretation**.

---

# 3. Local Language Model

Once the observation report has been generated, it is passed to a locally running language model through Ollama.

The model is instructed to act as an engineering manager and:

* Explain why the observations matter
* Prioritize important findings
* Identify strengths
* Identify engineering risks
* Recommend practical improvements
* Stay within the evidence provided
* Avoid inventing repository details

The model does not perform the underlying measurements.

It interprets the measurements produced by the observation engine.

This is important because the project is intended to work with relatively small language models rather than relying on a large cloud-hosted model.

---

# 4. Interactive Analysis

The project does not stop at generating a single AI response.

After the initial engineering review, the user can enter an interactive chat session — through the CLI or the Streamlit dashboard.

The model receives:

```text
Observation Report
        +
repo_context.json
        +
Conversation
```

This allows the user to ask questions about both the high-level findings and the underlying repository evidence.

For example:

```text
Why was the root directory considered high risk?

Which commits caused the dependency stability observation?

Why is the repository considered stale?

Show me the evidence behind the semantic hygiene finding.

What does the repository structure suggest about maintainability?
```

The distinction is intentional:

* **Observation report** provides the model with the important findings.
* **Raw repository context** allows deeper investigation when the summary is insufficient.

---

# Model Selection

One of the engineering exercises in this project was determining which small language model was most suitable for the task.

Several local models were given the same engineering report and evaluated on their ability to:

* Stay grounded in the supplied evidence
* Identify the most important findings
* Avoid inventing repository details
* Produce useful engineering recommendations
* Understand the distinction between observations and conclusions
* Provide practical rather than generic advice

The benchmark was not based solely on raw model performance metrics.

For this application, **useful engineering reasoning and grounded interpretation mattered more than simply producing fluent text**.

The current default model is:

```text
qwen3.5:4b
```

The model can be changed without changing the analysis pipeline — via `--model`/`--host` on any command, or the `MANAGER_EXE_OLLAMA_MODEL`/`MANAGER_EXE_OLLAMA_HOST` environment variables.

This means the observation engine and the language model remain relatively independent components.

---

# Running Locally

## Requirements

You will need:

* Python
* Git
* [`uv`](https://docs.astral.sh/uv/)
* Ollama, with a compatible local model pulled

A GitHub token is recommended but not required — it enables the authenticated
remote-metadata step and avoids GitHub's unauthenticated rate limit. Local
Git analysis works fine without one.

---

## Installation

```bash
git clone https://github.com/IAmHarshit0/Manager-Exe.git
cd manager-exe
uv sync
```

If you also want to use the Streamlit interface:

```bash
uv sync --extra ui
```

---

# Configure GitHub

Authenticated GitHub API requests are recommended because unauthenticated requests are subject to GitHub's rate limits.

Set:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

Alternatively, place the token in a `.env` file in the directory you run
`manager-exe` from:

```text
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

You can also provide it directly through the CLI with:

```text
--github-token
```

Without a token, local Git analysis can still be performed, but the GitHub metadata stage will be skipped.

---

# Configure Ollama

Start Ollama and pull the default model:

```bash
ollama pull qwen3.5:4b
```

The default configuration is:

```text
Model: qwen3.5:4b
Host:  http://localhost:11434
```

Both can be overridden through environment variables:

```bash
export MANAGER_EXE_OLLAMA_MODEL=mistral:latest
export MANAGER_EXE_OLLAMA_HOST=http://localhost:11434
```

or through the CLI:

```text
--model
--host
```

The model runs locally through Ollama rather than sending repository analysis to a hosted language-model API.

---

# CLI

The primary interface is the CLI.

## Scan a Repository

```bash
uv run manager-exe scan <repo_url> <local_clone_path> [--branch master] [--pull]
```

This performs the repository analysis and produces:

```text
repo_context.json
```

---

## Generate the Observation Report

```bash
uv run manager-exe report
```

This runs the deterministic observation engine and prints the engineering observation report.

---

## Generate an AI Engineering Review

```bash
uv run manager-exe evaluate
```

This sends the observation report to the configured local Ollama model.

---

## Chat With the Analysis

```bash
uv run manager-exe chat
```

The interactive session gives the model access to:

```text
Observation Report
+
repo_context.json
```

You can therefore move from a high-level engineering review into questions about the underlying evidence.

Type:

```text
exit
```

or press:

```text
Ctrl+C
```

to leave the session.

For larger repositories, the context size can be increased with:

```text
--ctx
```

The default context size is:

```text
8192
```

---

## Run Everything

The complete workflow can also be executed with:

```bash
uv run manager-exe run <repo_url> <local_clone_path> --pull
```

This combines the repository scan, observation generation, and AI evaluation into one workflow.

Example:

```bash
uv run manager-exe run https://github.com/owner/repo.git ./clone --pull
```

---

# Local Repository Handling

The Git analyzer requires a local repository because it works directly with Git history.

`manager-exe` therefore accepts a local clone path.

If the repository already exists and `--pull` is provided, the tool fetches and pulls the requested branch.

If the existing directory belongs to a different repository, `manager-exe` will re-clone it automatically.

If the directory contains uncommitted changes, the operation fails instead of deleting local work.

The goal is to make repeated repository analysis convenient without making the cloning workflow destructive.

---

# Streamlit Interface

A Streamlit interface is also available as an optional UI layer.

Install the UI dependency group:

```bash
uv sync --extra ui
```

Then run:

```bash
uv run streamlit run src/manager_exe/app.py
```

The dashboard provides the same underlying analysis pipeline with a browser-based interface — including a chat panel over the report and `repo_context.json`, mirroring the CLI's `chat` command.

The CLI remains the primary interface because it exposes the underlying workflow more directly and keeps the project lightweight.

The UI is treated as a presentation layer rather than a separate analysis system.

---

# Project Structure

The project is organized around the analysis pipeline rather than around a single LLM call.

A simplified view:

```text
manager-exe/
│
├── src/
│   ├── analyzers/          # GitHub API + local Git analysis, repo_context.json builder
│   ├── observations/       # Deterministic observation engine (six signal areas)
│   ├── slm/                # Ollama prompts, observation report, evaluate/chat logic
│   └── manager_exe/        # CLI (cli.py) and Streamlit dashboard (app.py)
│
├── repo_context.json       # generated by `scan`, written to the project root
├── pyproject.toml
├── README.md
└── LICENSE
```

The important architectural boundary is:

```text
Data Collection
      ↓
Deterministic Observations
      ↓
Structured Engineering Report
      ↓
Local SLM Interpretation
      ↓
Interactive Investigation
```

---

# Engineering Decisions

Several decisions were made deliberately during development.

### Deterministic analysis before the LLM

Rather than asking the model to inspect an entire repository and make arbitrary judgments, measurable repository properties are extracted first.

This makes the analysis more reproducible and gives the model a smaller, more meaningful context.

### Evidence attached to observations

Every signal is accompanied by evidence.

The model is therefore given not only:

```text
Root Pollution: High Risk
```

but also the information used to arrive at that observation.

This makes the model's reasoning easier to ground.

### Small local models

The project is specifically designed around local SLMs.

That introduces constraints around:

* Context size
* Reasoning ability
* Instruction following
* Hallucination
* Response quality

Those constraints are part of the engineering problem rather than something hidden behind a large hosted model.

### Model benchmarking

The model itself is treated as an interchangeable component.

Different local models can therefore be evaluated against the same deterministic report before selecting a default.

### CLI first

The CLI exposes the actual system rather than hiding the analysis behind a web interface.

It also makes the tool easier to run from scripts and other developer workflows.

---

# Validation

The project is intentionally small enough to be evaluated as an engineering experiment rather than pretending to be a production platform.

The validation questions are:

### Who needs this?

Developers who want a fast, local engineering perspective on a repository without sending repository analysis to a hosted AI service.

### Did anyone use it?

This project does not currently claim meaningful external adoption or production usage.

That is an explicit limitation.

### What did I learn?

The project provided practical experience with:

* GitHub API integration
* Git history analysis
* Repository context construction
* Deterministic signal generation
* Evidence-based analysis
* Prompt engineering
* Small language model evaluation
* Local Ollama inference
* CLI application design
* Interactive LLM workflows
* Separating deterministic systems from probabilistic systems

### What happens next?

The immediate focus is improving the reliability and usability of the existing CLI and validating the system against more repositories.

The Streamlit UI builds on the existing analysis pipeline without changing the underlying architecture.

---

# Limitations

`manager-exe` is not a replacement for:

* Human code review
* Security auditing
* Static analysis
* CI/CD systems
* Production observability
* Project management

The engineering review is based on the repository signals that the observation engine currently understands.

The LLM can also make incorrect interpretations, which is why the system deliberately provides the deterministic report and supporting evidence alongside the model output.

---

# License

This project is licensed under the MIT License.

```text
MIT License

Copyright (c) 2026 IAmHarshit0

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

# Project Status

`manager-exe` is an experimental portfolio and learning project focused on building a practical **offline LLM engineering tool**.

The core pipeline is functional:

```text
Repository
   ↓
GitHub + Git
   ↓
Repository Context
   ↓
Observation Engine
   ↓
Engineering Report
   ↓
Local SLM
   ↓
Interactive Chat
```

The project is intentionally being developed incrementally rather than attempting to become a full production platform from the beginning.