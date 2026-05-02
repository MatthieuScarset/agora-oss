# Architecture Overview

Agora OSS is organized as a stack of independent layers, each with clear responsibilities, contracts, and failure modes. This design enables source agnosticity: new data sources can be added through configuration and plugins without modifying core product logic.

## Layer Model

```
┌─────────────────────────────────────────┐
│      Dashboard & User Interfaces        │ (UI Layer)
├─────────────────────────────────────────┤
│      Agent Layer & Automation           │ (Agent Layer)
├─────────────────────────────────────────┤
│      API & Query Layer                  │ (API Layer)
├─────────────────────────────────────────┤
│      Retrieval & Search Layer           │ (Retrieval Layer)
├─────────────────────────────────────────┤
│      Storage Layer (PostgreSQL, Redis)  │ (Storage Layer)
├─────────────────────────────────────────┤
│      Normalization & Mapping Layer      │ (Normalization Layer)
├─────────────────────────────────────────┤
│      Plugin & Connector Layer           │ (Plugin Layer)
├─────────────────────────────────────────┤
│      External Data Sources              │ (Source Layer)
└─────────────────────────────────────────┘
```

## Layers (Bottom to Top)

### [Source Layer](layers/source-layer.md)
External data sources: Drupal.org, WordPress ecosystems, GitHub, GitLab, etc.
- **Responsibility**: Provide heterogeneous community data
- **Contract**: Raw data exposed via HTTP APIs or exports

### [Plugin Layer](layers/plugin-layer.md)
Adapter framework for connecting sources to Agora.
- **Responsibility**: Transform source-native APIs into Agora's envelope format
- **Contract**: Typed plugin interface with capability discovery, incremental fetch, health reporting

### [Normalization Layer](layers/normalization-layer.md)
Maps source-native data to canonical entity model.
- **Responsibility**: Apply mapping rules, identity stitching, lineage tracking
- **Contract**: Canonical entities, provenance metadata, quality policy enforcement

### [Storage Layer](layers/storage-layer.md)
PostgreSQL (primary), Redis (cache), object storage (MinIO/S3).
- **Responsibility**: Persist canonical data, manage indexing, cache hot results
- **Contract**: Normalized schema, vector embeddings, audit trails

### [Retrieval Layer](layers/retrieval-layer.md)
Hybrid search: BM25 full-text + vector semantic retrieval.
- **Responsibility**: Fast, ranked retrieval across entities and relationships
- **Contract**: Search queries, ranked result sets, cross-language support

### [API Layer](layers/api-layer.md)
FastAPI-based REST/GraphQL endpoints.
- **Responsibility**: Expose data and operations to clients
- **Contract**: JSON schemas, rate limiting, authentication/authorization

### [Agent Layer](layers/agent-layer.md)
Autonomous tool-calling runtime for analysis and automation.
- **Responsibility**: Execute user-requested workflows, generate insights
- **Contract**: Tool registry, memory management, observability

### [Dashboard Layer](layers/dashboard-layer.md)
Vue 3 frontend for search, visualization, analytics, and management.
- **Responsibility**: User-facing interface for exploration and administration
- **Contract**: i18n support, responsive design, real-time updates

### [Infra Layer](layers/infra-layer.md)
Docker, Docker Compose, Kubernetes templates, observability stack.
- **Responsibility**: Local and cloud deployment, monitoring, secrets management
- **Contract**: ENV-based config, Prometheus metrics, structured logging

### [Config Layer](layers/config-layer.md)
YAML/JSON configuration for sources, mappings, quality policies, locales.
- **Responsibility**: Enable source and behavior tuning without code edits
- **Contract**: Config schema validation, hot reloading, audit trails

### [Quality & Observability Layer](layers/quality-observability-layer.md)
Data quality checks, freshness monitoring, request tracing.
- **Responsibility**: Validate data integrity, debug issues, report health
- **Contract**: Metrics, logs, traces, health endpoints

## Design Principles

1. **Layering**: Each layer has explicit inputs/outputs; no skip-layer coupling.
2. **Testability**: Each layer can be tested independently with mocked dependencies.
3. **Replaceability**: Implementation behind a contract can be swapped without breaking consumers.
4. **Observability**: Every layer emits structured logs, metrics, and traces.
5. **Fail-Safe**: Degradation of one source/layer does not cascade to break the entire system.

## Contracts

Every layer exposes a **contract**—a set of schemas, interfaces, and error codes that downstream layers depend on. See [Contracts](../contracts/index.md) for details.
