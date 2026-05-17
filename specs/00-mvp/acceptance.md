# 00-MVP Acceptance Criteria

Acceptance checklist (pass/fail)

1. JSON validity

- Assert: `data/mock/drupalorg/issues.json` parses as JSON. (Tool: `jq` or Python `json.load`)

1. Harvester

- Run harvester example command; assert a harvest directory exists at `data/raw/drupal/issues/{harvest_id}/` with non-zero-sized page files.
- Assert `manifest.json` and `checkpoint.json` exist in the harvest directory.

1. Normalizer

- Run normalizer example command against a harvest directory; assert `data/normalized/drupal/issues/` contains at least one parquet file.
- Validate parquet schema matches `requirements.md` (column names and types).
- Validate at least one row with non-null `nid`, `title`, `author_id`.

1. Agentic product

- Assert `data/marts/00-mvp/issue_overview.json` exists and contains the keys: `top_issues`, `summary_text`.

1. Semantic search index

- Assert `data/marts/00-mvp/embeddings/` contains index files (or a small `index.sqlite` manifest) and at least one embedding vector stored.

## Verification commands (examples)

```python
import json,pyarrow.parquet as pq
print('json load ok', json.load(open('data/mock/drupalorg/issues.json'))!=None)
print('parquet files', pq.ParquetDataset('data/normalized/drupal/issues').files)
```

## Minimal pass criteria

- All steps 1–4 succeed locally.
- Artifacts exist under `data/raw/drupal/issues/{harvest_id}/`, `data/normalized/`, and `data/marts/00-mvp/`.

## Notes

- If parquet writing requires additional dependencies, document them in `pyproject.toml` before implementation.
- BDD scenarios are intentionally runnable via simple Python scripts; they should be adapted into CI workflows later.
