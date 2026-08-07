"""
Streamlit dashboard for manager-exe.

Thin UI layer over the existing scan -> report -> evaluate pipeline --
reuses analyzers/, observations/, and slm/ exactly as they are, the same
way cli.py does. See cli.py's module docstring for why the chdir-into-
src/slm step exists (report.py and observations/*.py locate
repo_context.json relative to the process's cwd).

Run with:
    uv run streamlit run src/manager_exe/app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st

PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
SLM_DIR = SRC_DIR / "slm"

src_str = str(SRC_DIR)
if src_str not in sys.path:
    sys.path.insert(0, src_str)


def run_scan(repo_url, local_path, branch, pull, github_token, output_path):
    from analyzers.repo_context import generate_repository_context

    generate_repository_context(
        repo_url=repo_url,
        local_path=local_path,
        output_filename=output_path,
        branch_name=branch,
        pull=pull,
        github_token=github_token or None,
    )


def run_report():
    original_cwd = os.getcwd()
    os.chdir(SLM_DIR)
    try:
        from slm.report import generate_observation_report

        return generate_observation_report()
    finally:
        os.chdir(original_cwd)


def run_evaluate(model, host, ctx=8192):
    original_cwd = os.getcwd()
    os.chdir(SLM_DIR)
    try:
        from slm.prompt import gen_prompt
        import ollama

        client = ollama.Client(host=host) if host else ollama
        prompt = gen_prompt()
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "What is your evaluation? Provide ONLY your final "
                    "evaluation. Do not repeat the prompt, instructions, "
                    "or templates."
                ),
            },
        ]
        response = client.chat(model=model, messages=messages, options={"num_ctx": ctx})
        return response.message.content
    finally:
        os.chdir(original_cwd)


def run_chat_turn(chat_history, model, host, ctx=8192):
    """chat_history is the list of {'role', 'content'} dicts accumulated so
    far in st.session_state (user/assistant turns only -- the system prompt
    with the report + raw repo_context.json is rebuilt fresh each call)."""
    original_cwd = os.getcwd()
    os.chdir(SLM_DIR)
    try:
        from slm.prompt import gen_chat_prompt
        import ollama

        client = ollama.Client(host=host) if host else ollama
        system_prompt = gen_chat_prompt()
        messages = [{"role": "system", "content": system_prompt}] + chat_history
        response = client.chat(model=model, messages=messages, options={"num_ctx": ctx})
        return response.message.content
    finally:
        os.chdir(original_cwd)


st.set_page_config(page_title="manager-exe", page_icon="🧭", layout="wide")
st.title("🧭 manager-exe")
st.caption("Repo analysis + AI engineering review, powered by a local Ollama model.")

with st.sidebar:
    st.header("Repository")
    repo_url = st.text_input("Repo URL", placeholder="https://github.com/owner/repo.git")
    local_path = st.text_input("Local clone path", value="clone")
    branch = st.text_input("Branch", value="master")
    pull = st.checkbox("Pull latest before analyzing", value=True)
    github_token = st.text_input(
        "GitHub token (optional)",
        type="password",
        help="Falls back to $GITHUB_TOKEN / a .env file if left blank. "
        "The remote-data step is skipped (not an error) without one.",
    )

    st.header("Ollama")
    model = st.text_input(
        "Model", value=os.environ.get("MANAGER_EXE_OLLAMA_MODEL", "llama3.2:latest")
    )
    host = st.text_input(
        "Host (optional)",
        value=os.environ.get("MANAGER_EXE_OLLAMA_HOST") or os.environ.get("OLLAMA_HOST", ""),
        placeholder="http://localhost:11434",
    )

    run_clicked = st.button("Run analysis", type="primary", use_container_width=True)

if "report_text" not in st.session_state:
    st.session_state.report_text = None
if "evaluation_text" not in st.session_state:
    st.session_state.evaluation_text = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if run_clicked:
    if not repo_url or not local_path:
        st.error("Repo URL and local clone path are required.")
    else:
        output_path = str(PROJECT_ROOT / "repo_context.json")
        with st.status("Scanning repository...", expanded=True) as status:
            try:
                run_scan(repo_url, local_path, branch, pull, github_token, output_path)
                status.update(label="Scan complete")
            except Exception as e:
                status.update(label="Scan failed", state="error")
                st.error(f"Scan failed: {e}")
                st.stop()

            try:
                st.session_state.report_text = run_report()
                status.update(label="Report generated")
            except Exception as e:
                status.update(label="Report generation failed", state="error")
                st.error(f"Report generation failed: {e}")
                st.stop()

            try:
                st.session_state.evaluation_text = run_evaluate(model, host or None)
                status.update(label="Evaluation complete", state="complete")
            except Exception as e:
                status.update(label="Evaluation failed", state="error")
                st.warning(f"AI evaluation failed (report below is still valid): {e}")
            st.session_state.chat_history = []

if st.session_state.evaluation_text:
    st.subheader("AI Evaluation")
    st.markdown(st.session_state.evaluation_text)

if st.session_state.report_text:
    with st.expander("Full observation report", expanded=not st.session_state.evaluation_text):
        st.code(st.session_state.report_text, language=None)

if not run_clicked and not st.session_state.report_text:
    st.info("Fill in the sidebar and click **Run analysis** to get started.")

if st.session_state.report_text:
    st.divider()
    st.subheader("Chat about this repo")
    st.caption(
        "The model can see both the report above and the full raw repo_context.json -- "
        "ask about anything in the data, not just what's in the narrative summary."
    )

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Ask about this repository...")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply = run_chat_turn(st.session_state.chat_history, model, host or None)
                except Exception as e:
                    reply = f"⚠️ {e}"
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})