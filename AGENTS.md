# AGENTS.md

Purpose: central rules and governance for repo agents.

- Purpose: build data products and surface actionable actor insights.
- Scope: agents may run data-processing tasks only; no direct code commits.
- Persona: concise, factual, conservative; explain recommendations.
- Allowed tools: list explicit tool names in each agent `.instructions.md`.
- Data access: agents must declare read/write paths;
  default: read `data/normalized/`, write `data/marts/`.
- Safety: redact PII (emails), obey privacy rules, do not exfiltrate secrets.
- Failure: write error artifacts to `logs/` and
  notify maintainers.
- Testing: each agent should reference BDD scenarios under `tests/bdd/`.
- Owner: specify maintainer contact in agent folder.

Rules enforcement:

- See `agents/.instructions.md` for canonical governance
- Keep per-agent `.instructions.md` focused on inputs, outputs, allowed tools, a
nd agent-specific constraints.
- Keep agent-specific rules in `agents/<name>/.instructions.md` and the
canonical prompt in `agents/<name>/.prompt.md`.
