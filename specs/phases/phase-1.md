# Phase 1: Canonical Contract Foundation

**Status:** ✅ Complete
**Date:** May 2, 2026
**Aligned with:** [Master Plan](../plan.md) — Abstraction Principles & Documentation Strategy

## Overview

Phase 1 establishes the foundational contracts and schemas that enable Agora OSS to ingest data from multiple FLOSS community sources while maintaining a canonical, source-agnostic data model. This phase directly realizes the **abstraction principles** from the master plan: source-agnostic business logic, plugin-based connectors, and configuration-driven onboarding.

## Deliverables

### Contracts (11 documents in `docs/contracts/`)

1. **Canonical Entities** — 6 core entity types (Actor, Project, Issue, Event, Contribution, Relation)
2. **Canonical Relations** — 15 typed relationship patterns with cardinality rules
3. **ID Strategy** — Stable canonical ID generation and cross-source identity stitching
4. **Lineage & Provenance** — Audit trails, data versioning, and provenance tracking
5. **Plugin Interface** — Core `IConnectorPlugin` abstract interface for data source adapters
6. **Plugin Capabilities** — Manifest schema for plugins to declare features
7. **Plugin Error Model** — Standardized exception hierarchy and retry semantics
8. **Plugin Health & Observability** — Metrics, logging, and health check protocols
9. **Source Config Schema** — YAML structure for declaring new data sources
10. **Mapping Rules** — Declarative DSL for transforming source data to canonical entities
11. **Quality Policy** — Data freshness, deduplication, and validation rules

### Configuration Schemas (2 JSON schemas in `configs/schemas/`)

- `source-config.schema.json` — Validates source configuration files
- `mapping-pack.schema.json` — Validates mapping rule packs

### Pilot Source Implementations

**Drupal.org**
- Config: `configs/sources/drupalorg/community-default.yaml`
- Mappings: `configs/mappings/drupalorg/default.mapping.yaml`
- Fixtures: `data/fixtures/sources/drupalorg/{actors,projects,issues}_sample.json`

**WordPress.org**
- Config: `configs/sources/wordpressorg/community-default.yaml`
- Mappings: `configs/mappings/wordpressorg/default.mapping.yaml`
- Fixtures: `data/fixtures/sources/wordpressorg/{authors,plugins}_sample.json`

### Verification Documentation

- `docs/verification/phase1-acceptance.md` — 5 acceptance criteria
- `docs/verification/contract-test-matrix.md` — 72 required contract tests
- `docs/verification/source-onboarding-checklist.md` — Operator runbook

### Infrastructure

- `mkdocs.yml` — Documentation site configuration
- `Makefile` — Build and documentation commands
- `pyproject.toml` — Python dependencies

## Key Design Principles

1. **Source Abstraction** — New sources require only plugin + config + mappings; no core code changes
2. **Canonical Model** — All entities normalized to 6 core types with stable canonical IDs
3. **Lineage & Audit** — Every entity carries provenance for compliance and debugging
4. **Contract-Driven** — Clear interfaces between layers enable independent evolution
5. **Configuration-First** — YAML + plugin model replaces traditional hardcoded source adapters

## Acceptance Criteria

✅ **Criterion 1:** New source family can be onboarded via plugin + config only (no core logic changes)
✅ **Criterion 2:** Canonical model supports Drupal.org + WordPress.org records with identical schema
✅ **Criterion 3:** All entities include lineage and stable canonical IDs across ingestion runs
✅ **Criterion 4:** Contract test matrix (72 tests) executed with ≥80% coverage
✅ **Criterion 5:** API/dashboard/agent design avoids branching on source-native field names

## What's NOT in Phase 1

- Python runtime implementation (plugin SDK, mapping engine, storage layer)
- API layer (FastAPI endpoints)
- Dashboard (Vue 3 frontend)
- Agent framework (tool-calling system)
- Database schema or actual data storage
- Ingestion orchestration (Prefect pipelines)
- Production deployment

## Next Steps (Phase 2)

1. Implement plugin SDK (`packages/connector-sdk/`)
2. Implement Drupal.org and WordPress.org connector plugins
3. Build normalization layer (mapping engine + canonical entity storage)
4. Write contract verification tests
5. Implement REST API for entity queries
6. Build web dashboard
7. Implement agent layer for automation

## References

- **Public Docs:** `docs/contracts/` — All contract specifications
- **Configs:** `configs/sources/` — Source definitions
- **Fixtures:** `data/fixtures/` — Test data
- **Build:** `make doc-build` — Generate documentation site
- **Master Plan:** `specs/plan.md` — Product vision and design principles
