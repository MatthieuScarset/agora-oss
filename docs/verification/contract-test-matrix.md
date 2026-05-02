# Contract Test Matrix

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  

## Overview

The contract test matrix defines required test coverage for each contract. All tests must pass before final sign-off.

## Test Coverage by Contract

### Canonical Entities v1

| Entity Type  | Test Case                               | Passes | Evidence                                     |
| ------------ | --------------------------------------- | ------ | -------------------------------------------- |
| Actor        | Schema validation (all required fields) | ✅      | test_canonical_actor_schema_valid.py         |
| Actor        | Schema validation (invalid email)       | ✅      | test_canonical_actor_schema_invalid_email.py |
| Actor        | Canonical ID generation                 | ✅      | test_actor_canonical_id.py                   |
| Actor        | Lineage fields present                  | ✅      | test_actor_lineage.py                        |
| Project      | Schema validation (all required fields) | ✅      | test_canonical_project_schema_valid.py       |
| Project      | Canonical ID generation                 | ✅      | test_project_canonical_id.py                 |
| Issue        | Schema validation (all required fields) | ✅      | test_canonical_issue_schema_valid.py         |
| Issue        | State field enum validation             | ✅      | test_issue_state_enum.py                     |
| Event        | Timestamps valid (start < end)          | ✅      | test_event_timestamps.py                     |
| Contribution | Contribution type enum validation       | ✅      | test_contribution_type_enum.py               |
| Relation     | Circular reference detection            | ✅      | test_relation_no_self_loop.py                |

**Total: 11 tests | Passing: 11 | Coverage: 100%**

### Canonical Relations v1

| Relation Type     | Test Case                   | Passes | Evidence                            |
| ----------------- | --------------------------- | ------ | ----------------------------------- |
| actor → project   | Maintains relation valid    | ✅      | test_rel_actor_maintains_project.py |
| actor → issue     | Reports relation valid      | ✅      | test_rel_actor_reports_issue.py     |
| project → project | Part-of relation valid      | ✅      | test_rel_project_part_of.py         |
| issue → issue     | Depends-on relation valid   | ✅      | test_rel_issue_depends_on.py        |
| All               | Reverse relation inference  | ✅      | test_rel_reverse_inference.py       |
| All               | Transitive closure (graphs) | ✅      | test_rel_transitive_closure.py      |

**Total: 6 tests | Passing: 6 | Coverage: 100%**

### ID Strategy v1

| Scenario        | Test Case                                             | Passes | Evidence                     |
| --------------- | ----------------------------------------------------- | ------ | ---------------------------- |
| Actor ID        | Drupal.org user:12345 → canonical_id                  | ✅      | test_id_drupalorg_actor.py   |
| Project ID      | Drupal.org node:views → canonical_id                  | ✅      | test_id_drupalorg_project.py |
| Email stitching | alice@example.com from Drupal.org + GitHub → 1 entity | ✅      | test_stitch_email_match.py   |
| Deduplication   | Same entity, two ingestion runs → 1 canonical         | ✅      | test_dedup_same_entity.py    |
| ID stability    | Canonical ID unchanged across 3 ingestion runs        | ✅      | test_id_stability_3_runs.py  |
| URL encoding    | Source ID with "/" → properly encoded                 | ✅      | test_id_url_encoding.py      |

**Total: 6 tests | Passing: 6 | Coverage: 100%**

### Lineage & Provenance v1

| Scenario         | Test Case                                 | Passes | Evidence                         |
| ---------------- | ----------------------------------------- | ------ | -------------------------------- |
| Ingestion Run ID | Format and consistency                    | ✅      | test_lineage_ingestion_run_id.py |
| Raw Payload Ref  | S3 URI valid and retrievable              | ✅      | test_lineage_raw_payload_ref.py  |
| Audit Trail      | Create action logged                      | ✅      | test_audit_create_action.py      |
| Audit Trail      | Update action logged                      | ✅      | test_audit_update_action.py      |
| Freshness        | Staleness detection works                 | ✅      | test_freshness_detection.py      |
| Version History  | Point-in-time query returns correct state | ✅      | test_version_history.py          |

**Total: 6 tests | Passing: 6 | Coverage: 100%**

### Plugin Interface v1

| Method                | Test Case                                   | Passes | Evidence                                |
| --------------------- | ------------------------------------------- | ------ | --------------------------------------- |
| discover_capabilities | Returns required manifest fields            | ✅      | test_plugin_discover_capabilities.py    |
| discover_capabilities | Manifest schema valid                       | ✅      | test_plugin_manifest_schema.py          |
| initialize            | Accepts valid config                        | ✅      | test_plugin_initialize_valid.py         |
| initialize            | Rejects invalid config (raises ConfigError) | ✅      | test_plugin_initialize_invalid.py       |
| fetch_full            | Yields RawEnvelopes                         | ✅      | test_plugin_fetch_full.py               |
| fetch_incremental     | Uses cursor state                           | ✅      | test_plugin_fetch_incremental_cursor.py |
| emit_raw_envelope     | Produces valid RawEnvelope                  | ✅      | test_plugin_emit_raw_envelope.py        |
| map_to_canonical      | Maps envelope to canonical entity           | ✅      | test_plugin_map_to_canonical.py         |
| report_health         | Returns health object                       | ✅      | test_plugin_report_health.py            |
| shutdown              | Closes resources cleanly                    | ✅      | test_plugin_shutdown.py                 |

**Total: 10 tests | Passing: 10 | Coverage: 100%**

### Plugin Capabilities v1

| Capability             | Test Case                     | Passes | Evidence                            |
| ---------------------- | ----------------------------- | ------ | ----------------------------------- |
| entity_types           | All declared types valid      | ✅      | test_cap_entity_types_valid.py      |
| supports_incremental   | If true, cursor_types present | ✅      | test_cap_incremental_consistency.py |
| supported_locales      | All BCP 47 valid              | ✅      | test_cap_locales_valid.py           |
| default_locale         | In supported_locales          | ✅      | test_cap_default_locale_in_list.py  |
| required_config_fields | Non-empty, all strings        | ✅      | test_cap_required_fields.py         |

**Total: 5 tests | Passing: 5 | Coverage: 100%**

### Plugin Error Model v1

| Error Type     | Test Case                            | Passes | Evidence                           |
| -------------- | ------------------------------------ | ------ | ---------------------------------- |
| ConfigError    | Raised on invalid config             | ✅      | test_err_config_error.py           |
| AuthError      | Raised on auth failure               | ✅      | test_err_auth_error.py             |
| FetchError     | Raised on network error              | ✅      | test_err_fetch_error.py            |
| TransformError | Raised on payload transform fail     | ✅      | test_err_transform_error.py        |
| MappingError   | Raised on mapping fail               | ✅      | test_err_mapping_error.py          |
| Retryable      | Non-retryable error not retried      | ✅      | test_err_no_retry_non_retryable.py |
| Retryable      | Retryable error retried with backoff | ✅      | test_err_retry_with_backoff.py     |

**Total: 7 tests | Passing: 7 | Coverage: 100%**

### Plugin Health & Observability v1

| Metric        | Test Case                    | Passes | Evidence                         |
| ------------- | ---------------------------- | ------ | -------------------------------- |
| report_health | Returns all required metrics | ✅      | test_health_required_metrics.py  |
| Logging       | Structured logs emitted      | ✅      | test_health_structured_logs.py   |
| Prometheus    | Metrics exportable           | ✅      | test_health_prometheus_export.py |
| Tracing       | OpenTelemetry spans created  | ✅      | test_health_otel_spans.py        |

**Total: 4 tests | Passing: 4 | Coverage: 100%**

### Source Config Schema v1

| Validation      | Test Case                      | Passes | Evidence                             |
| --------------- | ------------------------------ | ------ | ------------------------------------ |
| Valid config    | Drupal.org config validates    | ✅      | test_config_drupalorg_valid.py       |
| Valid config    | WordPress.org config validates | ✅      | test_config_wordpressorg_valid.py    |
| Required fields | Missing name rejected          | ✅      | test_config_missing_name.py          |
| Required fields | Missing connector rejected     | ✅      | test_config_missing_connector.py     |
| Required fields | Missing endpoints rejected     | ✅      | test_config_missing_endpoints.py     |
| Enum validation | Invalid source_family rejected | ✅      | test_config_invalid_source_family.py |
| Entity type     | Invalid entity_type rejected   | ✅      | test_config_invalid_entity_type.py   |
| Secrets         | Credentials never logged       | ✅      | test_config_no_creds_in_logs.py      |

**Total: 8 tests | Passing: 8 | Coverage: 100%**

### Mapping Rules v1

| Mapping           | Test Case                                     | Passes | Evidence                                 |
| ----------------- | --------------------------------------------- | ------ | ---------------------------------------- |
| Identity template | Drupal.org actor ID computed correctly        | ✅      | test_mapping_drupal_actor_id.py          |
| Field map         | Source fields correctly mapped                | ✅      | test_mapping_field_map.py                |
| Transformation    | Timestamp transform produces ISO 8601         | ✅      | test_mapping_timestamp_transform.py      |
| Transformation    | Email lowercase/trim applied                  | ✅      | test_mapping_email_normalize.py          |
| Relationships     | Maintains relationship extracted              | ✅      | test_mapping_relationship_extract.py     |
| Stitching         | Email match stitches actors                   | ✅      | test_mapping_stitch_email.py             |
| Conditional       | Conditional mapping applied correctly         | ✅      | test_mapping_conditional.py              |
| Dry-run           | Drupal.org fixture → canonical (no errors)    | ✅      | test_mapping_drupal_fixture_dryrun.py    |
| Dry-run           | WordPress.org fixture → canonical (no errors) | ✅      | test_mapping_wordpress_fixture_dryrun.py |

**Total: 9 tests | Passing: 9 | Coverage: 100%**

## Test Execution Summary

| Category                      | Total  | Passing | Coverage |
| ----------------------------- | ------ | ------- | -------- |
| Canonical Entities            | 11     | 11      | 100%     |
| Canonical Relations           | 6      | 6       | 100%     |
| ID Strategy                   | 6      | 6       | 100%     |
| Lineage & Provenance          | 6      | 6       | 100%     |
| Plugin Interface              | 10     | 10      | 100%     |
| Plugin Capabilities           | 5      | 5       | 100%     |
| Plugin Error Model            | 7      | 7       | 100%     |
| Plugin Health & Observability | 4      | 4       | 100%     |
| Source Config Schema          | 8      | 8       | 100%     |
| Mapping Rules                 | 9      | 9       | 100%     |
| **TOTAL**                     | **72** | **72**  | **100%** |

## Test Execution Command

```bash
# Run full contract test suite
pytest tests/contracts/ -v --cov=packages/canonical-schema --cov-report=html

# Run specific contract tests
pytest tests/contracts/test_canonical_entities_v1.py -v
pytest tests/contracts/test_mapping_rules_v1.py -v

# Run with coverage threshold
pytest tests/contracts/ --cov-fail-under=80
```

## Continuous Integration

Contract tests run on every commit:

1. **Lint**: mypy, pylint, code formatting
2. **Unit Tests**: Contract validation (72 tests)
3. **Integration Tests**: Plugin + config integration
4. **Schema Tests**: JSON schema validation
5. **Coverage Report**: HTML artifact

All tests must pass before PR approval.

## Fixture Data

Test fixtures located in `data/fixtures/`:

```
data/fixtures/
  sources/
    drupalorg/
      actors_sample.json       # 5 sample Drupal.org users
      projects_sample.json     # 3 sample Drupal.org projects
      issues_sample.json       # 10 sample Drupal.org issues
    wordpressorg/
      plugins_sample.json      # 5 sample WordPress plugins
      reviews_sample.json      # 10 sample reviews
  canonical/
    actors_sample_canonical.json      # Expected canonical output
    projects_sample_canonical.json
```

Fixtures are version-controlled and updated whenever entity schemas change.

## Future Test Enhancements

Future enhancements may add:

- Performance benchmarks (ingestion speed, query latency)
- Scalability tests (100k+ entities)
- Chaos engineering (fault injection, resilience testing)
- Cross-source join tests (relationships across Drupal + WordPress)
- AI/ML model evaluation (for entity resolution and stitching)
