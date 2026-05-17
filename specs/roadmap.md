# Roadmap

This roadmap details each phase of the Agora OSS project.

## Phase 0 - MVP

### Phase 0 — Goal

Prove Agora's end-to-end value with one source and one entity type.

Key items:

- fetch raw issues from Drupal.org
- normalize into Agora models
- expose widgets on a dashboard

### Phase 0 — Deliverables

- Provider abstraction and ingestion interfaces
- Shared normalization pipeline across sources
- Resilient retries and checkpointing for harvests - DAG with Prefect
- Functional ETL pipeline from raw Drupal.org to normalized Agora `Issues`
- Basic boostraph dashboard displaying totals in widgets

## Phase 1 - Additional providers

### Phase 1 — Goal

Extend provider support and prove reuse of the canonical model.

### Phase 1 — Deliverables

- Add WordPress and Symfony providers
- More agent-assisted data products showcasing actionable insights
- Semantic search

## Phase 2 - Scalable orchestration

### Phase 2 — Goal

Harden orchestration, scale for large datasets, and enrich agent actions.

### Phase 2 — Deliverables

- Scalable orchestration and scheduling
- Vector DB-backed semantic search
- Enhanced agent workflows for recommendations
- Observability and reliability improvements
