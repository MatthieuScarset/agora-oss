# 00-MVP BDD Scenarios

Feature: Harvesting

 Scenario: Harvest Drupal issues
  Given `data/mock/drupalorg/issues.json` is present
  When I run the harvester for provider "drupal" with an explicit `harvest_id`
  Then a raw output set is created at `data/raw/drupal/issues/{harvest_id}/`
  And the directory contains `pages/*.json.gz`, `manifest.json`, and `checkpoint.json`

 Example (developer):

 ```bash
 python -m scripts.harvest \
  --provider drupal \
  --input data/mock/drupalorg/issues.json \
  --out data/raw/drupal/issues/
 ```

Feature: Normalization

 Scenario: Normalize raw pages into canonical Issue parquet
  Given a raw harvest directory `data/raw/drupal/issues/{harvest_id}/`
  When I run the normalizer against that directory
  Then `data/normalized/drupal/issues/part-*.parquet` is written
  And the parquet schema matches the canonical `Issue` schema
  And at least one row has non-null `nid`, `title`, and `author_id`

 Example:

 ```bash
 python -m scripts.normalize --in data/raw/drupal/issues/*/ --out data/normalized/drupal/
 ```

Feature: Agentic data product

 Scenario: Generate issue overview summary
  Given normalized `Issue` parquet files in `data/normalized/drupal/issues/`
  When the agent runs `generate_summary(report_type=issue_overview)`
  Then `data/marts/00-mvp/issue_overview.json` exists
  And the JSON contains `top_issues` (list) and `summary_text` (string)

 Example:

 ```bash
 python -m scripts.agent --report-type issue_overview --in data/normalized/drupal/ --out data/marts/00-mvp/
 ```

Feature: Semantic search smoke

 Scenario: Build a small embeddings index
  Given `data/marts/00-mvp/issue_overview.json` and normalized issues exist
  When I run the local indexer
  Then embeddings are written under `data/marts/00-mvp/embeddings/`
  And a sample query returns at least one relevant issue id

 Example:

 ```bash
 python -m scripts.index_embeddings --in data/normalized/drupal/ --out data/marts/00-mvp/embeddings/
 ```
