# 00-MVP Requirements

## Overview

Concrete inputs, outputs, canonical models and storage paths for the 00-MVP.

## Inputs

- `data/mock/drupalorg/issues.json` — sample issues JSON (harvester input)
- `data/raw/drupal/` — (optional) raw harvest output path

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
  - `tags`: list<string>

## Storage layout

- Raw JSON: `data/raw/drupal/issues/{harvest_id}/pages/*.json.gz`
- Normalized Issue parquet: `data/normalized/drupal/issues/part-*.parquet`
- Marts (data products): `data/marts/00-mvp/` (artifacts: summaries, indexes)

## Conventions

- Use snake_case for column names.
- Use parquet with pyarrow engine and snappy compression.
- Timestamps stored as int64 unix seconds.
