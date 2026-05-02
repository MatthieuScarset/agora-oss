# Contracts

Contracts are the formal specifications that each layer exposes to its consumers. A contract includes:

- **Data Schema**: JSON Schema or Pydantic model defining structure
- **Interface Definition**: Functions, error codes, version strategy
- **SLA/Guarantees**: Availability, ordering, transformation rules
- **Evolution Rules**: How changes are backwards compatible

All contracts in this section are versioned (v1, v2, etc.) and must remain stable during a major version. Breaking changes require a new contract version with a deprecation period.

## Canonical Data Model

The canonical model is the single source of truth for entities and their relationships across all sources.

- [Canonical Entities v1](canonical-entities-v1.md) — Core entity types and required fields
- [Canonical Relations v1](canonical-relations-v1.md) — Entity relationship model and ontology
- [ID Strategy v1](id-strategy-v1.md) — Stable ID generation, source identity mapping, deduplication rules
- [Lineage & Provenance v1](lineage-and-provenance-v1.md) — Data lineage, source attribution, audit trails

## Plugin System

Plugins are the adapters that connect external sources to Agora.

- [Plugin Interface v1](plugin-interface-v1.md) — Core plugin methods and lifecycle
- [Plugin Capabilities v1](plugin-capabilities-v1.md) — Capability discovery, feature flags, optional behaviors
- [Plugin Error Model v1](plugin-error-model-v1.md) — Error codes, retry semantics, health reporting
- [Plugin Health & Observability v1](plugin-health-and-observability-v1.md) — Metrics, logs, traces, status endpoints

## Configuration

Configuration drives source onboarding, mapping, quality policy, and locale support.

- [Source Config Schema v1](source-config-schema-v1.md) — YAML structure for defining a source and its attributes
- [Mapping Rules v1](mapping-rules-v1.md) — Rules engine for transforming source data to canonical entities

## Contract Evolution

1. **Design Phase**: Contract is proposed in a pull request with examples.
2. **Review Gate**: Architecture owner and affected layer owners sign off for approval.
3. **Stability Period**: Contract is immutable for the version.
4. **Deprecation**: New version proposed with migration path; old version has 2-phase deprecation (warning, then removal).

## How to Use Contracts

- **API Consumer**: Read the schema and example sections for your use case.
- **Plugin Developer**: Implement the interface; test against the contract test matrix.
- **Operator**: Validate config against the schema before deployment.
- **Product Team**: Use contracts to identify what new features require contract changes.
