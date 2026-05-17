# 00-MVP Acceptance Criteria

Acceptance checklist (pass/fail)

1. JSON validity

- Assert that `data/mock/drupalorg/issues.json` parses as JSON.
 Recommended tools: `jq` or Python `json.load`.

1. Harvester

-- Run the harvester example command and assert a harvest directory exists at
 `data/raw/drupal/issues/{harvest_id}/` with non-zero-sized page files.
-- Assert that `manifest.json` and `checkpoint.json` exist in the harvest dir.

1. Normalizer

-- Run the normalizer example command against a harvest directory and assert
 that `data/normalized/drupal/issues/` contains at least one parquet file.
-- Validate the parquet schema matches `requirements.md` (column names and
 types).
-- Validate at least one row has non-null values for `nid`, `title`, and
 `author_id`.

1. Agentic product

-- Assert that `data/marts/00-mvp/issue_overview.json` exists and contains
 the keys `top_issues` and `summary_text`.

1. Semantic search index

-- Assert that `data/marts/00-mvp/embeddings/` contains index files or a
 small `index.sqlite` manifest, and that at least one embedding vector is
 stored.

## Verification commands (examples)

```python
import json
import pyarrow.parquet as pq

print('json load ok', json.load(open('data/mock/drupalorg/issues.json'))!=None)
print('parquet files', pq.ParquetDataset('data/normalized/drupal/issues').files)
```

## Minimal pass criteria

- All steps 1–4 succeed locally.
-- Artifacts exist under `data/raw/drupal/issues/{harvest_id}/`,
 `data/normalized/`, and `data/marts/00-mvp/`.

## Notes

-- If parquet writing requires additional dependencies, document them in
 `pyproject.toml` before implementation.
-- BDD scenarios are intentionally runnable via simple Python scripts. They
 should be adapted into CI workflows later.
