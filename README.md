# Agora OSS

Open-source knowledge graph for FLOSS community data, turning fragmented signals
into actionable insights, a unified dashboard, and automated workflows.

## Quickstart

```bash
# Install required global developer tools
uv tool install go-task-bin ruff ty
uv sync --all-extras --dev
# Configure local environment
cp .env.example .env
```

---

## Repository layout (sketch)

Top-level folders and purpose (minimal placeholders):

```text
apps/
 api/           # FastAPI service
 mcp/           # Optional MCP server
workers/
 flows/         # Prefect flows
 tasks/         # Prefect tasks
 agents/        # Pluggable agent implementations
 tools/         # Shared agent tools
packages/
 agora/         # core Python package
 shared/        # shared utilities/models
specs/
 mission.md
 roadmap.md
 stack.md
 00-mvp/
  plan.md
  requirements.md
  validation.md
  features/
   issues/
data/
 raw/
 normalized/
 marts/
 schema/
tests/
 unit/
 integration/
 bdd/
docs/
ci/
```

---

Made by Github Copilot. Orchestrated by [Matthieu Scarset](https://matthieuscarset.com).
