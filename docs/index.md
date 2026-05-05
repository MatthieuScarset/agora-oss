# Agora OSS Documentation

Welcome to the Agora OSS documentation. This site documents the architecture,
contracts, and operational procedures for the agentic, data-driven community
platform.

## Core Objective

Extract valuable insights from heterogeneous FLOSS community data through
ingestion and agentic analysis, and provide a unified, source-agnostic canonical
model for search, analysis, and automation.

## Data source provider

Pluggable data-source providers ingest raw community data and normalize it
to the project's canonical models. See the Drupal example at
[providers/drupal.py](providers/drupal.py#L1-L300).

- Reads mock JSON by default (`data/mock/drupalorg/`) via `fetch()`.
- Normalizes records with `normalize()` into `Actor`, `Project`, `Issue`.
- To use live Drupal, implement HTTP fetching (use `fetch_config.endpoints`).

Work in progress
