import os
import json
from observations.collaboration import total_devs, authorship_score, bulk_ratio, bulk_rating
from observations.commits import semantic_count, violations, semantic_signal, atomicity_signal
from observations.delivery import max_streak, has_config, has_data, stability, reproducibility
from observations.dev_activity import lifespan, gap, velocity_signal, recency_signal
from observations.documentation import readme_presence, doc_to_code, doc_density, documentation_quality
from observations.tree import pollution, env_leak, root_score

cwd = os.getcwd()
parent = os.path.dirname(cwd)
root = os.path.dirname(parent)

file_path = os.path.join(root, "repo_context.json")

with open(file_path, "r") as f:
    repo_context = json.load(f)

def generate_observation_report() -> str:
    """
    Aggregates all pre-loaded sub-module variables into a comprehensive,
    narrative-driven portfolio observation report text block.
    """
    
    # Placeholders left open for you to handle manually as requested
    repo_name = repo_context["repository"]["name"]
    repo_description = repo_context["repository"]["description"]

    report_text = f"""
=========================================================================
OBSERVATION REPORT: {repo_name}
=========================================================================
Description: {repo_description}

1. COLLABORATION METRICS
-----------------------------------------
* SIGNAL: Authorship Score
  - STATUS: {authorship_score}
  - WHAT IT MEASURES: Measures whether development is concentrated around a single contributor or distributed across multiple contributors.
  - EVIDENCE: Total individual developers tracked on project = {total_devs} author(s).

* SIGNAL: Bulk Rating
  - STATUS: {bulk_rating}
  - WHAT IT MEASURES: Measures how much of the repository was introduced through large commits versus incremental development.
  - EVIDENCE: Bulk-to-total commit structural injection footprint ratio = {round(bulk_ratio * 100, 1) if isinstance(bulk_ratio, (int, float)) else bulk_ratio}%.


2. COMMIT QUALITY METRICS
-----------------------------------------
* SIGNAL: Semantic Hygiene Compliance
  - STATUS: {semantic_signal}
  - WHAT IT MEASURES: Measures how consistently commit messages follow established naming conventions.
  - EVIDENCE: Verified {semantic_count} total commits cleanly matching standard naming rules.

* SIGNAL: Layer Atomicity Violations
  - STATUS: {atomicity_signal}
  - WHAT IT MEASURES: Measures whether commits remain focused on a single logical change instead of mixing unrelated modifications.
  - EVIDENCE: Flagged {violations} transaction(s) crossing multi-layer operational directories.


3. WORKSPACE LAYOUT & ARCHITECTURE
-----------------------------------------
* SIGNAL: Root Directory Organization
  - STATUS: {root_score}
  - WHAT IT MEASURES: Measures how well project files are organized by checking whether source code, datasets, and assets are grouped into dedicated directories.
  - EVIDENCE: Detected {pollution} unorganized code/data elements sitting outside dedicated subfolders.

* SIGNAL: Environment Runtime Leaks
  - STATUS: {env_leak}
  - WHAT IT MEASURES: Detects development artifacts such as cache files or local environment metadata that should generally not be committed.
  - EVIDENCE: System runtime local file leak state evaluated to = {env_leak}.


4. DELIVERY & CONFIGURATION MANAGEMENT
-----------------------------------------
* SIGNAL: Dependency Stability
  - STATUS: {stability}
  - WHAT IT MEASURES: Measures how stable the project's dependency configuration remained throughout development.
  - EVIDENCE: Maximum continuous trial-and-error environment tracking run sequence = {max_streak} commit(s).

* SIGNAL: Reproducibility Status
  - STATUS: {reproducibility}
  - WHAT IT MEASURES: Verifies if the project is self-contained, turnkey, and ready to execute with all configuration files and datasets included.
  - EVIDENCE: Manifests Verification: Configuration Guide={has_config} | Content/Data Assets={has_data}.


5. DEVELOPMENT VELOCITY & RECENT ACTIONS
-----------------------------------------
* SIGNAL: Velocity Profile
  - STATUS: {velocity_signal}
  - WHAT IT MEASURES: Measures the overall development pattern, distinguishing concentrated implementation bursts from long-term iterative development.
  - EVIDENCE: Total operational lifespan from first commit setup to completion push = {round(lifespan, 1) if isinstance(lifespan, (int, float)) else lifespan} time units.

* SIGNAL: Recency Profile Gap
  - STATUS: {recency_signal}
  - WHAT IT MEASURES: Measures how recently the repository has been actively maintained.
  - EVIDENCE: Project inactivity footprint gap delta = {gap} calendar day(s).


6. SYSTEM DOCUMENTATION HEALTH
-----------------------------------------
* SIGNAL: Documentation Quality
  - STATUS: {documentation_quality}
  - WHAT IT MEASURES: Measures how well the repository explains its purpose, setup, and usage.
  - EVIDENCE: Baseline global file system README manifest presence verification state = {readme_presence}.

* SIGNAL: Documentation Footprint Density
  - STATUS: {doc_density}
  - WHAT IT MEASURES: Evaluates the literal character payload distribution volume relative to the active repository code blocks.
  - EVIDENCE: Calculated character payload structural density ratio = {doc_to_code} documentation units per component.

=========================================================================
END
=========================================================================
"""
    return report_text

# --- RUNTIME EXECUTION ENTRYPOINT ---
if __name__ == "__main__":
    # Call the preloaded text block generator directly
    final_output = generate_observation_report()
    print(final_output)
