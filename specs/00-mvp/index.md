# 00 - MVP Specifications

This directory contains the Phase 0 (00-MVP) specification set for Agora.
It operationalizes the Phase 0 goals in `specs/roadmap.md` and maps them to
concrete user stories, BDD-style acceptance criteria, and runnable smoke
scenarios.

Scope

- Provider: Drupal.org issues (mock inputs under `data/mock/drupalorg/`).
- Canonical entity: `Issue` stored as parquet under
  `data/normalized/drupal/issues/` and data products under
  `data/marts/00-mvp/`.
- Raw harvest history: immutable, per-run directories under
  `data/raw/{provider}/{entity_type}/{harvest_id}/`.

Core MVP Features (high-level user stories)

- Ingest: As a data engineer, I can harvest issue data from a provider into
  an immutable raw-harvest directory so runs are auditable and resumable.
- Normalize: As a data engineer, I can transform raw pages into a canonical
  `Issue` parquet dataset validated by Pydantic schemas.
- Productize: As a product user, I can view an agent-generated issue overview
  JSON that summarizes top issues and a short narrative.
- Searchable index: As a developer, I can build a small semantic-search index
  of issue embeddings for basic retrieval and demos.

Contents

- `requirements.md` — inputs, outputs, canonical models, storage layout, and
  run conventions.
- `bdd.md` — runnable Gherkin-style scenarios for harvester, normalizer,
  agent, and indexer.
- `acceptance.md` — measurable acceptance checks, verification commands, and
  minimal pass criteria.

How to use

1. Review and iterate on the user stories and BDD scenarios below.
2. Implement flows and mappers to satisfy the BDD scenarios.
3. Verify using the acceptance checklist and add CI runners later.
