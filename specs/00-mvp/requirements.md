# 00-MVP Requirements

## Overview

Concrete inputs, outputs, canonical models and storage paths for the 00-MVP.

This document specifies the MVP implementation constraints. Key
requirements:

- Use Prefect flows for harvesting and orchestration.
- Use schema-driven normalization based on `{entity_type}.schema.yml`.
- Use Pydantic models for validation and coercion.
- Use parquet for normalized storage.

## Inputs

- `data/mock/drupalorg/issues.json` — sample issues JSON (harvester input)
- `data/raw/drupal/` — (optional) raw harvest output path

Additional requirements:

- Harvesting must be implemented as a Prefect Flow. It should be
   provider-agnostic, resumable, and support concurrency and retries.
- Normalization must be schema-driven. Mapping rules are defined in
   `data/schema/{entity_type}.schema.yml` and used by mappers to produce
   Pydantic model instances.
- Use Pydantic v2 models for canonical entities to validate and coerce
   fields before writing to parquet.
- The system must support large-volume fetching: paged fetches,
   checkpointing, configurable concurrency, and backoff/retry.

## Raw history layout

Raw harvests must be organized by harvest ID so every run is immutable,
auditable, and resumable.

Recommended layout:

- `data/raw/{provider}/{entity_type}/{harvest_id}/`
  - `manifest.json` — source URL, query params, row/page counts,
    checksums, timestamps
  - `checkpoint.json` — resume state for interrupted harvests
  - `pages/page_000001.json.gz`
  - `pages/page_000002.json.gz`
  - `...`

Harvest ID conventions:

- Use a stable, human-readable ID for each run, such as
  `2026-05-17T12-00-00Z_8f3a`.
- Preserve the original harvest ID in downstream logs and manifests.
- Never overwrite an existing harvest directory; create a new one for each run.

## Canonical Model (parquet schema overview)

- Issue (parquet schema)
  - `nid`: int64
  - `title`: string
  - `body`: string
  - `created`: int64 (unix ts)
  - `changed`: int64 (unix ts)
  - `author_id`: int64
  - `status`: int32
  - `priority`: string
  - `component`: string
  - `url`: string
  - `comments`: int32
  - `tags`: list[string]

Schema-driven mapping rules

- Each `{entity_type}.schema.yml` must declare canonical fields and types.
   Each field must include a `source` mapping that indicates the path in
   the raw JSON from which to extract the value (dot-separated). An example
   schema for `issue` lives at `data/schema/issue.schema.yml`.

Validation and transforms

- Fields defined in the schema must be validated by the Pydantic model.
   Mappers must perform light transforms such as timestamp coercion (to
   unix seconds), list conversion, and default value fill-ins.
- If a record fails validation, the mapper should emit a per-record error
   to `logs/` and continue. A configurable fail-fast flag may be provided
   for strict runs.

## Storage layout

- Raw JSON: `data/raw/drupal/issues/{harvest_id}/pages/*.json.gz`
- Normalized Issue parquet: `data/normalized/drupal/issues/part-*.parquet`
- Marts (data products): `data/marts/00-mvp/` (artifacts: summaries, indexes)

Writer conventions

- Use the `pyarrow` engine with `snappy` compression when writing parquet.
    Configure this via the `pandas.DataFrame.to_parquet` `engine` and
    `compression` parameters.
- Ensure timestamps are int64 unix seconds in the resulting parquet
   schema.

## Conventions

- Use snake_case for column names.
- Use parquet with pyarrow engine and snappy compression.
- Timestamps stored as int64 unix seconds.

Prefect and operational conventions

- Prefect flows must expose parameters for `provider`, `entity_type`,
   `harvest_id`, `input` (for local/mock inputs), concurrency, and
   retry/backoff settings.
- Flows must write `manifest.json` and `checkpoint.json` under the
   harvest directory and write page files under `pages/` as gzipped JSON.
- All flows and mappers must obey the agent governance in
   `agents/coding-agent/.instructions.md` and log errors to `logs/`.
