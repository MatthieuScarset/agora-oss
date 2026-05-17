# 00-MVP BDD Scenarios

Scenario: Harvest Drupal issues (harvester)

Given `data/mock/drupalorg/issues.json` is present
When the harvester is executed for provider `drupal` and project `drupal`
And a harvest ID is assigned for the run
Then a raw JSON output set appears under `data/raw/drupal/issues/{harvest_id}/pages/`
And `manifest.json` and `checkpoint.json` are written in the harvest directory
And the harvested payload contains the input data

Example command (developer-run):

python -m scripts.harvest --provider drupal --project drupal --harvest-id 2026-05-17T12-00-00Z_8f3a --input data/mock/drupalorg/issues.json --out data/raw/drupal/issues/

Scenario: Normalize raw issues → Issue parquet

Given a raw harvest directory at `data/raw/drupal/issues/{harvest_id}/`
When the normalizer runs
Then it writes `data/normalized/drupal/issues/part-*.parquet` with schema matching `requirements.md`
And the parquet contains at least one row where `nid`, `title`, and `author_id` are non-null

Example command:

python -m scripts.normalize --provider drupal --in data/raw/drupal/issues/harvest_id=2026-05-17T12-00-00Z_8f3a/ --out data/normalized/drupal/

Scenario: Agentic data product generation

Given normalized `Issue` parquet files
When the agent runs `generate_summary(report_type=issue_overview)`
Then a JSON summary is produced in `data/marts/00-mvp/issue_overview.json` containing top-5 issues by comment_count and a short text synopsis

Scenario: Dashboard / semantic search smoke

Given `data/marts/00-mvp/` contains `issue_overview.json` and embeddings exist
When a local semantic-search indexer is run
Then a small vector index file exists under `data/marts/00-mvp/embeddings/` and a sample query returns at least one relevant issue id
