# 00-MVP Acceptance Criteria

This document lists measurable checks for each core MVP story. Each check
is runnable locally and intended to be promoted to CI later.

Story: Ingest (harvester)

- Check: Running the harvester with `--input data/mock/drupalorg/issues.json`
 creates a harvest directory `data/raw/drupal/issues/{harvest_id}/` containing
 gzipped page files and `manifest.json` + `checkpoint.json`.

Story: Normalize (normalizer)

- Check: Running the normalizer against a harvest directory writes at least
 one parquet file to `data/normalized/drupal/issues/`.
- Schema: Parquet column names and types match the canonical `Issue` schema in
 `requirements.md` and contain non-null `nid`, `title`, and `author_id` in at
 least one row.

Story: Productize (agent)

- Check: Running the agent with `report_type=issue_overview` writes
 `data/marts/00-mvp/issue_overview.json` with keys `top_issues` (list) and
 `summary_text` (string).

Story: Search index (embeddings/indexer)

- Check: Running the indexer produces vector files under
 `data/marts/00-mvp/embeddings/` (or a small `index.sqlite`) and at least one
 stored embedding can be queried.

## Quick verification examples

Python (quick checks):

```python
import json
import pyarrow.parquet as pq

print('json load ok', json.load(open('data/mock/drupalorg/issues.json')) is not None)
print('parquet files', pq.ParquetDataset('data/normalized/drupal/issues').files)
```

Shell (example):

```bash
# run harvester
python -m scripts.harvest --provider drupal --input data/mock/drupalorg/issues.json --out data/raw/drupal/issues/

# check for manifest and pages
ls data/raw/drupal/issues/*/manifest.json
ls data/raw/drupal/issues/*/pages/*.json.gz

# run normalizer
python -m scripts.normalize --in data/raw/drupal/issues/*/ --out data/normalized/drupal/

# list parquet files
find data/normalized/drupal/issues -name "*.parquet" | head
```

## Minimal pass criteria

- All story checks succeed locally and artifacts exist under `data/raw/`,
 `data/normalized/`, and `data/marts/00-mvp/`.

## Notes

- If parquet writing needs dependencies, add them to `pyproject.toml` and
 document local setup steps.
- BDD scenarios in `bdd.md` are intended to be runnable and should be
 adapted into CI later.
