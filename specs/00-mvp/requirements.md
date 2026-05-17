# 00-MVP Requirements

## Overview

Concrete inputs, outputs, canonical models and storage paths for the 00-MVP.

This document specifies the MVP implementation constraints and minimal
operational expectations.

### Key requirements

- Use Prefect flows for harvesting and orchestration (Prefect examples are
   provided; equivalent orchestrators are acceptable if documented).
- Use schema-driven normalization based on `{entity_type}.schema.yml`.
- Use Pydantic v2 models for canonical entities and validation.
- Persist normalized data as parquet using `pyarrow` with `snappy`.

## Inputs

- `data/mock/drupalorg/issues.json` — sample issues JSON (harvester input).
- `data/raw/drupal/` — optional raw harvest output path for recorded runs.

### Additional guidance

- Harvesting flows should be provider-agnostic, resumable, and support
   concurrency and retries. Expose parameters for `provider`, `entity_type`,
   `harvest_id`, `input`, concurrency, and retry/backoff.
- Normalization must be schema-driven using `data/schema/{entity_type}.schema.yml`.
- Mappers produce Pydantic model instances and emit per-record validation
   errors into `logs/` (continue on error unless run with `--fail-fast`).
- Support paged fetching, checkpointing, configurable concurrency, and
   exponential backoff for external requests.

## Raw history layout

Raw harvests must be organized by harvest ID so every run is immutable,
auditable, and resumable.

Recommended layout:

- `data/raw/{provider}/{entity_type}/{harvest_id}/`
  - `manifest.json` — source URL, query params, row/page counts, checksums, timestamps
  - `checkpoint.json` — resume state for interrupted harvests
  - `pages/page_000001.json.gz`
  - `pages/page_000002.json.gz`
  - `...`

### Harvest ID conventions

- Use a stable, human-readable ID for each run, such as
   `2026-05-17T12-00-00Z_8f3a`.
- Preserve the original harvest ID in downstream logs and manifests.
- Never overwrite an existing harvest directory; create a new one for each run.

## Canonical Model (agora-agnostic Issue envelope)

The MVP previously surfaced provider-specific fields (Drupal). For the
Agora canonical model we define an agnostic, future-proof envelope that
receives mappings from provider-specific mappers. The mapper's job is to
translate provider fields into this envelope and preserve the original raw
payload under `metadata.raw`.

The Agora `Issue` is designed for semantic search and extraction of
actionable insights. The schema below balances structured metadata with free
text suitable for embeddings and NLP.

### Agora `Issue` (recommended fields)

- `agora_id`: string (UUID) — canonical unique id for this record
- `provider`: string — source provider id (e.g., `drupal`)
- `provider_id`: string — original provider identifier (raw nid or id)
- `harvest_id`: string — harvest run id that produced the raw payload
- `type`: string — entity type (e.g., `issue`)
- `title`: string — short title or headline
- `body`: string — full raw body/description (HTML or markdown preserved)
- `body_text`: string — cleaned plain-text body (for embeddings/search)
- `summary`: string | null — short agent-generated summary
- `created_at`: int64 (unix seconds)
- `updated_at`: int64 (unix seconds)
- `authors`: list[dict] — minimal author objects: `{id, name, role?}`
- `participants`: list[string] — normalized participant identifiers
- `assignees`: list[string]
- `status`: string — normalized status (`open`, `closed`, `assigned`, etc.)
- `priority`: string — normalized priority (`low|medium|high|unknown`)
- `component`: string | null
- `labels`: list[string] — generic tag/label list
- `comments_count`: int32
- `attachments`: list[dict] — `{url, mime_type, filename}`
- `language`: string | null — ISO language code when known
- `canonical_url`: string | null — stable URL to original item
- `embeddings_path`: string | null — relative paths to stored embeddings if present
- `extracted_actions`: list[string] — short curated action items (optional)
- `metrics`: dict — free form numeric metrics (e.g., reaction counts)
- `metadata`: dict — provider-specific metadata and raw payload under `raw`
- `schema_version`: string — canonical schema version (e.g., `agora-issue-v1`)

Notes:

- Keep `body` (original) and `body_text` (cleaned) to support different NLP
   pipelines and to preserve fidelity.
- `metadata.raw` MUST include the original provider JSON for traceability.
- `embeddings_path` is a pointer to a separate embeddings store; do not
   embed dense vectors inside parquet files for the MVP.

### Mapping guidance for mappers

- Each provider-specific mapper (e.g., Drupal mapper) MUST:
  - Extract provider identifiers into `provider_id` and set `provider`.
  - Map timestamp fields to `created_at`/`updated_at` as unix seconds.
  - Consolidate tags/terms into `labels`.
  - Extract and normalize participant/author info into `authors` and `participants`.
  - Preserve the original raw JSON under `metadata.raw` and record `harvest_id`.
  - Populate `body_text` by stripping HTML/Markdown and normalizing whitespace.

- Prefer normalized enumerations for `status` and `priority` in the mapper.

### Validation and transforms

- Implement Pydantic v2 models for the Agora `Issue` envelope. Mappers
   should produce instances of the model (or serializable dicts that validate)
   before writing to parquet.
- On validation error, emit a per-record error to `logs/` and continue unless
   `--fail-fast` is specified.
- Keep the schema backward-compatible by incrementing `schema_version` for
   non-breaking additions.

Example: provider-specific `nid` maps to `provider_id`; Drupal `body` maps to
`body` and to cleaned `body_text`.

## Storage layout

- Raw JSON: `data/raw/drupal/issues/{harvest_id}/pages/*.json.gz`
- Normalized Issue parquet: `data/normalized/drupal/issues/part-*.parquet`
- Marts (data products): `data/marts/00-mvp/` (artifacts: summaries, indexes)

### Writer conventions

- Use the `pyarrow` engine with `snappy` compression when writing parquet.
- Ensure timestamps are int64 unix seconds in the resulting parquet schema.
- Use snake_case for column names.

## Operational conventions

- Flows must write `manifest.json` and `checkpoint.json` under the harvest direc
tory and store page files under `pages/` as gzipped JSON.
- Log operational and per-record validation errors to `logs/`.
- Follow agent governance in `agents/coding-agent/.instructions.md`.
