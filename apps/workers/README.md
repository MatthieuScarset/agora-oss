# Workers

Prefect Flows (Ingestion & Processing)

## Local Docker Services

The local stack starts:

- a Prefect server (`prefect-server`) exposed on port 4200
- a Prefect worker (`prefect-worker`) connected to `PREFECT_WORK_POOL`

Default work pool is configured in `.env` via `PREFECT_WORK_POOL=agora-local-pool`.
