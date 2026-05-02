# Agora OSS Documentation

Welcome to the Agora OSS documentation. This site documents the architecture, contracts, and operational procedures for the agentic, community-driven data platform.

## Quick Start

- **[Architecture Overview](architecture/index.md)** — System design and layer responsibilities
- **[Roadmap](../specs/plan.md)** — Project roadmap and design principles
- **[Contracts](contracts/index.md)** — Canonical data models, plugin interfaces, and config schemas
- **[Verification](verification/index.md)** — Acceptance criteria and test matrices

## Key Principles

1. **Source Agnostic**: Data sources connect through plugins; core logic never branches on source type.
2. **Multilingual First**: Language is a first-class attribute on every entity and document.
3. **Local-First**: Full development lifecycle works locally before any cloud dependency.
4. **Configuration-Driven**: New sources added through config + plugin artifacts, no core edits.
5. **Web3 Optional**: Blockchain and token mechanics are plugins, not requirements.

## Core Objective

Build an agentic, community-driven data platform that ingests heterogeneous FLOSS community data through plugins and exposes a unified, source-agnostic canonical model for search, analysis, and automation.

## Documentation Acceptance Criteria

1. MkDocs site builds in CI as a static artifact.
2. Every major layer has a dedicated page describing responsibilities, boundaries, inputs, outputs, and failure modes.
3. Architecture docs reference the same canonical terms used in contracts and schemas.
4. Contract changes require corresponding doc updates in the same change set.
5. A newcomer can understand the end-to-end system from docs without reading code first.
