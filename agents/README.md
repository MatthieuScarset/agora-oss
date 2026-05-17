# agents/

This folder contains agent definitions and governance for pluggable agents.

Conventions:

- `agents/<name>/.instructions.md` — agent-specific rules and allowed tools
- `agents/<name>/.prompt.md` — canonical prompt/persona for the agent
- `agents/<name>/tests.md` — (optional) BDD scenarios for the agent

Agents are executed by workers (see `workers/agents/`) and must declare
data access paths.

Important: generated outputs must be formatted and linted. Agents must
run `pre-commit run --all-files` before saving generated files to the repo.
