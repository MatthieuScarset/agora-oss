# Infra

This folder holds operational scripts for infrastructure bootstrap and validation,
separated from application code.

## Layout

```text
infra/
├── bootstrap.sh              # Central orchestrator (main entry point)
├── postgres/                 # PostgreSQL initialization
│   └── init/
│       └── pgvector.sql      # pgvector extension
└── README.md                 # This file
```

## Usage

Apply Prefect deployments after the stack is up:

```bash
make prefect-deploy
```

### Full Infrastructure Bootstrap

Bootstrap all services in the correct order and run health checks:

```bash
make bootstrap
# or directly:
./infra/bootstrap.sh
```

This orchestrator:

1. Verifies Docker Compose stack is running
2. Waits for PostgreSQL with pgvector extension
3. Waits for Redis
4. Waits for MinIO
5. **Bootstraps MinIO bucket** (inline)
6. **Bootstraps Prefect work pool** (inline)
7. **Runs comprehensive smoke tests** (inline)

All bootstrap logic is consolidated in a single script.

### Standalone Smoke Tests

For health checks only (without bootstrap):

```bash
make smoke
# or directly:
./infra/smoke_stack.sh
```

Checks: PostgreSQL+pgvector, Redis, MinIO, Prefect API, Frontend

### PostgreSQL Initialization

The pgvector extension is auto-initialized via Docker Compose volume mount:

- Path: `/docker-entrypoint-initdb.d/pgvector.sql`
- File: `postgres/init/pgvector.sql`

## Environment Variables

The bootstrap scripts use these variables from `.env`:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `REDIS_PORT`
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`
- `S3_BUCKET` (default: `agora-raw`)
- `PREFECT_WORK_POOL` (default: `agora-local-pool`)
- `PREFECT_API_PORT` (default: `4200`)
- `FRONTEND_PORT` (default: `3000`)
