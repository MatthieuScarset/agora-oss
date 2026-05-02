# Plan: Agora OSS


## TL;DR

Build Agora OSS as an agentic, actionable community platform with no hard coupling to any single data source. The system is driven by an abstraction layer (plugins + configuration), so new sources can be added without rewriting core product logic. Development is local-first, multilingual by design, and cloud scale-out comes only after the foundation is validated. Web3, blockchain, and token economics are optional extension layers: not required for the open-source baseline, but available to unlock advanced cloud features.

## Product Vision

- Generate actionable insights from heterogeneous community data.
- Enable search, analysis, synthesis, and automation across multiple sources.
- Run the full development lifecycle locally before any cloud dependency.
- Keep the architecture reusable for other communities and ecosystems.
- Serve both humans and automated workflows, not only dashboards.
- Support multilingual experiences end-to-end from day one.
- Allow optional crypto-native participation and incentive mechanisms.

## Abstraction Principles

- Agora OSS must not be source-specific in branding or domain model.
- Data sources are connected through plugins/adapters.
- Configuration defines what each source provides: entities, relationships, fields, refresh frequency, permissions, transformations, locales.
- Core business logic consumes one canonical model independent of source.
- Source connectors are replaceable without breaking API, UI, or agents.
- Web3 capability is a plugin class, not a hard dependency.

## Multilingual Strategy

- Language is a first-class attribute on every source, entity, document, and insight.
- Plugins must declare supported locales, default locale, translation availability, and fallback rules.
- Canonical model stores original text, detected language, translated variants, and language metadata.
- Search supports language-aware filtering and cross-language retrieval.
- UI adapts labels, formatting, and content presentation to active locale.
- Agent outputs are generated in the user's selected language when possible, with explicit fallback.
- Quality checks include translation freshness, locale coverage, and mixed-language handling.

## Web3 and Token-Economics Strategy (Optional)

- OSS baseline runs with Web3 disabled by default.
- Blockchain integration is modular through optional plugins and feature flags.
- Token economics is policy-driven and configurable per deployment.
- Cloud edition can unlock advanced features that require wallet identity, on-chain attestations, and programmable incentives.
- Core platform value must remain fully usable without wallet, token, or chain dependencies.

## OSS vs Cloud Feature Gating

- OSS baseline:
  - No mandatory wallet connection.
  - No mandatory token issuance.
  - Optional local mock for wallet and on-chain events.
  - Full core capabilities: ingestion, search, dashboard, agents, automation.
- Cloud enhanced:
  - Optional wallet-based identity and role proofs.
  - Optional on-chain reputation and contribution attestations.
  - Optional token incentives for validated actions and contributions.
  - Optional staking/slashing mechanics for governance workflows.
  - Optional premium automation triggers tied to token or role policies.

## Repository Strategy

Use a monorepo.

## Target Folder Layout

- apps/: executable apps (API, dashboard, agents, local orchestrator)
- packages/: shared code (schemas, types, clients, business logic, utilities)
- plugins/: source connectors and plugin runtime adapters
- configs/: source profiles, mappings, refresh rules, locale config, env-specific settings, token-policy config
- data/: fixtures, samples, exports, local test datasets
- infra/: Docker, local orchestration, scripts, service wiring
- docs/: architecture, standards, ADRs, onboarding

## Folder Rules

- One app = one clearly isolated entry point.
- Shared packages cannot depend on app-specific code.
- Plugins do not contain product business logic.
- Source activation/tuning must happen through config, not app rewrites.
- Canonical schemas and API contracts are defined once and reused.
- Web3 features are isolated behind capability flags and optional plugins.

## Framework Baseline Decision

- Do not build fully artisanal from scratch.
- Use a framework-led approach with thin custom layers.
- Primary recommendation: Python for the agentic core.
- PHP frameworks can be used for optional integration/portal needs, but not as core agent runtime.
- Keep existing NestJS backend as gateway/facade during transition.
- Prefer controlled polyglot evolution over big-bang rewrites.

## Documentation Workstream (Parallel, Not Deferred)
- Documentation is a first-class deliverable from Phase 1 onward, not a postscript.
- Publish docs as a static site with MkDocs.
- Every layer must be documented: source layer, plugin layer, normalization layer, storage layer, retrieval layer, API layer, agent layer, dashboard layer, infra layer, config layer, quality/observability layer.
- Each layer gets an overview page, contract page, data-flow page, and operator notes page.
- Documentation artifacts must track the same versioning discipline as code contracts.
- Docs are updated alongside contract changes and acceptance gates; no undocumented layer changes are allowed.

### MkDocs Site Structure
- docs/index.md
- docs/architecture/index.md
- docs/architecture/layers/source-layer.md
- docs/architecture/layers/plugin-layer.md
- docs/architecture/layers/normalization-layer.md
- docs/architecture/layers/storage-layer.md
- docs/architecture/layers/retrieval-layer.md
- docs/architecture/layers/api-layer.md
- docs/architecture/layers/agent-layer.md
- docs/architecture/layers/dashboard-layer.md
- docs/architecture/layers/infra-layer.md
- docs/architecture/layers/config-layer.md
- docs/architecture/layers/quality-observability-layer.md
- docs/contracts/index.md
- docs/runbooks/index.md
- mkdocs.yml

### Documentation Acceptance Criteria
1. MkDocs site builds in CI as a static artifact.
2. Every major layer has a dedicated page describing responsibilities, boundaries, inputs, outputs, and failure modes.
3. Architecture docs reference the same canonical terms used in contracts and schemas.
4. Contract changes require corresponding doc updates in the same change set.
5. A newcomer can understand the end-to-end system from docs without reading code first.

### Documentation Gating Rule
- Do not advance a phase unless the corresponding docs pages for the changed layers are updated.


## Tech Stack (Precise)


## Core Runtime

- Language: Python 3.12+
- API framework: FastAPI
- Validation/schema: Pydantic v2
- ASGI server: Uvicorn in dev, Gunicorn+Uvicorn workers in production
- Background jobs: Celery (optional) or Prefect-native task execution

## Data and Storage

- Primary DB: PostgreSQL 16
- Vector search: pgvector extension
- Caching: Redis
- Object/file storage (local): MinIO or local filesystem
- Object/file storage (cloud): S3-compatible bucket

## Ingestion and Orchestration

- Pipeline orchestration: Prefect 3
- Connectors/plugin SDK: custom Python package with typed plugin interface
- Data contracts: JSON Schema + Pydantic models
- Transform layer: Polars/Pandas (Polars preferred for performance)

## Search and AI

- Embeddings: sentence-transformers (local) and OpenAI-compatible provider (cloud option)
- Retrieval: hybrid BM25 + vector retrieval
- Reranking (optional): cross-encoder reranker
- LLM orchestration: lightweight adapter layer (provider-agnostic)
- Evaluation: prompt/retrieval test suite with deterministic fixtures

## Agent Layer

- Agent runtime: Python service with tool-calling abstraction
- Tool registry: typed tool interfaces + policy checks
- Memory: short-term in Redis, long-term in PostgreSQL
- Tracing/observability: OpenTelemetry + structured logs

## Frontend

- Framework: Vue 3 + TypeScript
- Build tool: Vite
- State management: Pinia
- UI layer: [Tailwind Admin](https://tailadmin.com/components) component library
- i18n: vue-i18n with locale packs and fallback chain

## Existing Backend Compatibility

- Keep NestJS as API gateway/facade during migration period
- Gradually route domain endpoints from NestJS to FastAPI
- Deprecate duplicated endpoints after parity validation

## Web3 (Optional Extension)

- Wallet auth: SIWE-compatible adapter (optional)
- Chain interaction: EVM-compatible provider adapter
- Indexing: chain event ingestion plugin
- Token policy engine: configurable rules service (off by default in OSS)
- Smart contracts: optional, audited, cloud-enabled feature set only

## DevOps and Environments

- Local orchestration: Docker Compose
- CI: Compatible with both GitHub Actions AND GitLab CI (lint, test, typecheck, build)
- Observability: Prometheus + Grafana + OpenTelemetry collector
- Secrets: dotenv for local, managed secrets in cloud
- IaC (cloud phase): Terraform (optional)

## Security Baseline

- API auth: API key + JWT support
- RBAC: role/permission model in core API
- Audit logs: immutable action/event trail
- PII handling: field-level masking and retention policy
- Dependency scanning: SCA + container image scan in CI

## Execution Plan


## Phase 1: Abstraction Layer + Local 
Foundation
1. Define canonical model: source, entity, relation, event, document, signal, action, locale metadata.
2. Define plugin contract: capabilities, schema, mapping, sync modes, auth, error model, locale support.
3. Define source configuration schema (including multilingual behavior and fallbacks).
4. Build local storage tiers for raw, normalized, and indexed data.
5. Formalize sync strategies: full refresh, incremental sync, backfill, reindex.
6. Add local source simulators and multilingual fixtures for testing.
7. Optional Web3 extension: define capability flags for wallet identity, chain events, token actions (disabled by default).

## Phase 2: Ingestion + Normalization

1. Onboard initial sources through plugin + config only.
2. Normalize all inputs into canonical schema.
3. Validate relationships and stable identifiers across sources.
4. Add quality rules: required fields, freshness, deduplication, traceability.
5. Add multilingual quality checks.
6. Build analytic-ready views for API, search, and dashboard.
7. Version mappings to handle source evolution safely.
8. Optional Web3 extension: ingest wallet-linked identities and on-chain attestations into optional canonical fields.

## Phase 3: Local API + Search

1. Expose local API over canonical model.
2. Provide explore/filter/aggregate endpoints.
3. Add multi-source semantic retrieval.
4. Enable cross-entity and cross-language responses.
5. Decouple retrieval logic from underlying storage engine.
6. Support filters by source, entity, time window, score, status, locale.
7. Add graceful fallback when sources/plugins are missing.
8. Optional Web3 extension: expose optional endpoints for wallet profile, attestations, and token-policy eligibility.

## Phase 4: Actionable Dashboard

1. Run dashboard locally on normalized data.
2. Start with decision views: trends, anomalies, opportunities, priority signals.
3. Add configurable source-specific views as optional overlays.
4. Ensure dashboard modules can be enabled via config.
5. Implement locale switching and multilingual rendering.
6. Validate behavior under partial/missing source conditions.
7. Optimize for actionability, not just observability.
8. Optional Web3 extension: add optional wallet/reputation panels and token-incentive simulation views.

## Phase 5: Agents + Action Loops

1. Connect agents to same data/tools used by API and dashboard.
2. Define core agent roles: explore, prioritize, synthesize, recommend, trigger.
3. Implement audited actions: notifications, summaries, escalations, task creation, enrichment.
4. Keep memory and decision traces for audit/replay.
5. Support behavior tuning per source/community/locale through config.
6. Add guardrails to prevent unwanted automated actions.
7. Ensure outputs are directly usable by humans and workflows.
8. Optional Web3 extension: allow policy-based token rewards for validated agent-supported outcomes.

## Phase 6: Automation + Scale-Out

1. Add workflows for sync, alerts, reports, and feedback loops.
2. Keep local orchestration as default dev/test reference.
3. Introduce cloud connectors as runtime variants only.
4. Preserve domain contracts across infrastructure migrations.
5. Document migration as infrastructure work, not product redesign.
6. Scale without breaking canonical schema and plugin interfaces.
7. Optional cloud unlocks: managed wallet providers, audited smart-contract integrations, and programmable incentive policies.

## Concrete Next Steps

1. Finalize canonical schema and plugin contract (with multilingual + optional web3 fields).
2. Implement source config format and validation.
3. Deliver one sample plugin + mock source mode.
4. Add optional Web3 mock plugin and feature flags.
5. Build local ingestion/normalization/index pipeline.
6. Publish local API for canonical entities.
7. Integrate semantic search + first actionable dashboard views.
8. Add first agent role and audited action path.
9. Instrument quality, logging, lineage, and traceability.
10. Prepare cloud runtime variant and optional token-policy engine after local stability.

## Verification

1. Start full stack locally without cloud credentials.
2. Add one new source via config/plugin without changing core app code.
3. Verify API, dashboard, and agents all consume canonical model.
4. Run multi-source, multi-entity, cross-language queries successfully.
5. Validate full/incremental sync strategies per source.
6. Confirm graceful degradation when plugin/source is unavailable.
7. Verify agent actions are auditable and replayable.
8. Verify OSS mode works with all Web3 features disabled.
9. Verify cloud mode can enable Web3 features by configuration only.

## Out of Scope (Now)

- Hard dependency on one source ecosystem.
- Mandatory wallet or token requirements in OSS baseline.
- Early cloud scale-out and production hardening.
- Full frontend/backend rewrite solely for migration readiness.
- Premature deep specialization for one community.

## Expected Outcome

Agora OSS becomes a local-first, multilingual, agentic community intelligence platform that delivers actionable insights and actions across multiple data sources through a stable canonical core and configurable plugin architecture. Web3/blockchain/token economics remain optional extension layers, enabling richer cloud features without compromising the open-source baseline.
