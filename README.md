# Agora OSS

Open-source knowledge graph for FLOSS community data, turning fragmented signals
into actionable insights, a unified dashboard, and automated workflows.

## Quickstart

```bash
# Configure environment
# Copy the example file and adjust values if needed:
cp .env.example .env
#
# Start local platform stack
make docker-up
#
# Open key services
# - Prefect UI:     http://localhost:4200
# - MinIO API (S3): http://localhost:9000
# - MinIO Console:  http://localhost:9001
# - PostgreSQL:     http://localhost:5432
# - Redis:          http://localhost:6379
# - Node.js:        http://localhost:3000
#
# Smoke test
make smoke
#
# Bootstrap infra steps
make bootstrap
#
# Stop stack
make docker-down
```

## Infra

Important bootstrap and verification steps live in `infra/`:

- `infra/prefect_bootstrap.sh` for the Prefect bootstrap step
- `infra/smoke_stack.sh` for local stack smoke checks

## Development

Local tech stack:

- Prefect Server: flow orchestration API and UI.
- Prefect Worker: executes flow runs from local work pool.
- PostgreSQL + pgvector: primary relational storage and vector indexing.
- MinIO: local object storage with S3 API compatibility.
- Redis: cache/queue primitives for workers and services.
- Frontend Node.js: runs the dashboard in development mode.

Useful docker commands:

- `make docker-up` start stack
- `make docker-ps` show services status
- `make docker-logs` stream logs
- `make smoke` run stack smoke checks
- `make bootstrap` run infrastructure bootstrap steps
- `make docker-down` stop stack
- `make docker-reset` stop stack and remove volumes

---

Made by [Matthieu Scarset](https://matthieuscarset.com) with love, caffeine, and
questionable life choices.
