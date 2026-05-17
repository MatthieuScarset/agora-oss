# Roadmap

This roadmap details each phase of the Agora project.
It covers the MVP, multi-provider expansion, and scalable agentic
orchestration.

## Phase 0 - MVP

### Phase 0 — Goal

 Prove Agora's end-to-end value with one source and one entity type.

Key items:

- fetch raw issues from Drupal.org
- normalize into Agora models
- build agent-assisted data products
- expose semantic-searchable insights on a dashboard

### Phase 0 — Deliverables

- Drupal.org issue harvester (single project or small set)
- Raw-to-Agora transform: `Issue`
- Local lakehouse for raw + normalized data (parquet)
- Agentic data product generation
- Dashboard + semantic search
- BDD-style Markdown validation specs

## Phase 1 - Additional providers

### Phase 1 — Goal

Extend provider support and prove reuse of the canonical model.

### Phase 1 — Deliverables

- Add WordPress and Symfony providers
- Provider abstraction and ingestion interfaces
- Shared normalization pipeline across sources
- Data product generation for multiple providers
- Basic CI for ingestion flows

## Phase 2 - Scalable orchestration

### Phase 2 — Goal

Harden orchestration, scale for large datasets, and enrich agent actions.

### Phase 2 — Deliverables

- Scalable orchestration and scheduling
- Resilient retries and checkpointing for harvests
- Vector DB-backed semantic search
- Enhanced agent workflows for recommendations
- Observability and reliability improvements
