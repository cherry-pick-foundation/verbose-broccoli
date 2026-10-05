# Research: Wiki naming

Decision: use the existing XDG builders with `llm-wiki` in their current join.
Rationale: raw_import.py:375 and instance.py:37 contain the old container; the
CLI calls instance_path at __main__.py:77, and grammatical_competence.py:575
uses the same resolver. No shared helper or dependency is needed for two literals.
Alternative rejected: a new registry or compatibility abstraction adds no need.

Decision: update session_select.py:59's raw staging guard and synthetic case.
Rationale: it checks the former container name before creating a stage; actual
callers resolve the path through stage_dir at session_select.py:593. Keeping
that guard aligned preserves refusal before writing.

Decision: preserve history and external vault vocabulary. Current documentation
uses wiki; historical specs and constitution Governance retain dated names.
Consumer inspection reads only paths, metadata and public builder snippets.
Installed copied tools and old checkouts may still need their link; no unlink
is performed or implied. Main owns that decision after root's evidence report.
