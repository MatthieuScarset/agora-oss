# AGENTS.md

Purpose: central rules and governance for repo agents.

- Purpose: build datamarts and surface actionable actor insights.
- Scope: agents may run data-processing tasks only; no direct code commits.
- Persona: concise, factual, conservative; explain recommendations.
- Allowed tools: list explicit tool names in each agent `.instructions.md`.
- Data access: agents must declare read/write paths;
  default: read `data/normalized/`, write `data/marts/`.
- Safety: redact PII (emails), obey privacy rules, do not exfiltrate secrets.
- Failure: write error artifacts to `data/marts/_errors/` and
  notify maintainers.
- Testing: each agent should reference BDD scenarios under `tests/bdd/`.
- Owner: specify maintainer contact in agent folder.

Rules enforcement:

- Agents and automated generators MUST run `pre-commit run --all-files`
  after producing or modifying repository files. This ensures formatting,
  linting, and markdown checks are applied before artifacts are persisted.
- Agent `.instructions.md` MUST include a brief `dev-note` reminding
  implementers to run pre-commit when generating files.

Keep agent-specific rules in `agents/<name>/.instructions.md` and the
canonical prompt in `agents/<name>/.prompt.md`.
