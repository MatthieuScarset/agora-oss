# Phase 1 Acceptance Criteria

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  

## Overview

Phase 1 culminates in a sign-off gate (Gate E) that confirms the foundational contract pack is complete, validated, and ready for Phase 2 development. These criteria define what "done" means for Phase 1.

## Five Acceptance Criteria

### 1. New Source Family Can Be Introduced by Adding Only Plugin + Config Artifacts

**Criterion**: A developer can introduce a new data source by creating:
- A plugin module in `plugins/{source_family}/connector.py`
- A source config in `configs/sources/{source_family}/default.yaml`
- Mapping rules in `configs/mappings/{source_family}/default.mapping.yaml`

WITHOUT modifying any core product logic.

**Verification**:
- [ ] Drupal.org source has been added (plugin + config + mapping)
- [ ] WordPress.org source has been added (plugin + config + mapping)
- [ ] At least one of these sources can be toggled on/off via config without restarting
- [ ] Adding a third mock source (GitHub) follows the same pattern
- [ ] No core code changes required for third source

**Evidence**: 
- Pull request log showing only new files in `plugins/`, `configs/`, no changes to core files
- Diff summary shows no modifications to `packages/canonical-schema/` or `apps/*/` core logic

### 2. Canonical Read Model Supports Drupal.org-Like and WordPress-Like Records with Same Entity Contracts

**Criterion**: A single canonical entity schema can represent actors, projects, and issues from both Drupal.org and WordPress ecosystems without source-specific branching in core logic.

**Verification**:
- [ ] Canonical entity schema (from canonical-entities-v1.md) accommodates Drupal.org actor (user) fields
- [ ] Same schema accommodates WordPress.org actor (user) fields
- [ ] No `if source_family == 'drupalorg'` branches in normalization or API layers
- [ ] API queries return consistent field names regardless of source
- [ ] Dashboard renders actors from both sources with identical UI components

**Evidence**:
- Sample canonical entities for actor from Drupal.org and WordPress.org
- Query result comparison showing identical output structure
- UI screenshot showing same actor card rendered for sources

### 3. All Entities Include Lineage/Provenance and Stable Canonical IDs

**Criterion**: Every canonical entity carries:
- Stable `canonical_id` that does not change between ingestion runs
- Lineage metadata (`ingestion_run_id`, `raw_payload_ref`) tracing back to source
- Audit trail entry documenting creation/updates

**Verification**:
- [ ] Sample Drupal.org actor has `canonical_id` format: `actor:drupalorg:drupalorg:user:12345`
- [ ] Sample WordPress.org actor has `canonical_id` format: `actor:wordpressorg:wordpress-acme:user:67890`
- [ ] Both have `ingestion_run_id`, `raw_payload_ref` populated
- [ ] Both have audit trail entries with timestamps and actions
- [ ] Canonical IDs remain unchanged across consecutive ingestion runs
- [ ] Raw payload references point to retrievable data

**Evidence**:
- JSON dump of 2-3 canonical entities showing complete provenance
- Audit trail query results showing entity history
- Two ingestion run outputs showing ID stability

### 4. Contract Test Matrix Passes for Schema, Mapping, and Quality Policy

**Criterion**: Automated test suite validates:
- Canonical entity schema conforms to JSON Schema validation
- Mapping rules transform source data correctly
- Quality policies are enforceable
- Plugin interface is correctly implemented

**Verification**:
- [ ] Schema validation tests pass (100% coverage of entity types)
- [ ] Mapping tests pass for Drupal.org (sample data → canonical)
- [ ] Mapping tests pass for WordPress.org (sample data → canonical)
- [ ] Quality policy tests pass (freshness checks, dedup logic)
- [ ] Plugin interface tests pass (all methods callable, correct signatures)
- [ ] Test coverage >= 80% for contracts and mapping logic

**Evidence**:
- Test run output: all tests passing
- Coverage report: >= 80%
- No skipped or xfail tests in critical path

### 5. No API/Dashboard/Agent Design Assumes Source-Native Field Names

**Criterion**: Product code (API, dashboard, agents) never branched on or exposed source-native field names. All public APIs use canonical field names only.

**Verification**:
- [ ] API schema (OpenAPI/GraphQL) uses only canonical field names
- [ ] API does not expose `drupal_uid` or `wordpress_user_id`; uses `canonical_id` instead
- [ ] Dashboard components consume canonical entity schema, not source-specific types
- [ ] Agent tool definitions use canonical fields (e.g., `issue.state`, not `node.status`)
- [ ] No source-family-specific API endpoints (e.g., no `/api/v1/drupal/users`)

**Evidence**:
- OpenAPI/GraphQL schema export showing canonical field names only
- Agent tool definitions (JSON) showing canonical field names
- Dashboard component code review (random sample of 3-5 components) showing no source checks
- Grep results showing no `if source_family ==` or similar in API/dashboard/agent code

## Gate E Checklist

### Documentation Complete

- [ ] All contract docs published and reviewed
- [ ] Architecture overview updated
- [ ] MkDocs site builds without errors
- [ ] All docs cross-referenced and consistent in terminology

### Acceptance Criteria Signed Off

- [ ] All 5 criteria verified and documented
- [ ] Evidence artifacts collected and linked
- [ ] Architecture owner sign-off on contract completeness
- [ ] Product owner sign-off on entity semantics

### Quality Metrics Met

- [ ] Test coverage >= 80%
- [ ] No critical/high-severity linting issues
- [ ] Type checking passes (mypy, pyright, or similar)
- [ ] API contract tests pass
- [ ] Performance benchmarks meet baseline (if applicable)

### Operational Readiness

- [ ] Operator runbooks published (how to add new source, etc.)
- [ ] Admin UI or CLI tool for managing sources operational
- [ ] Health dashboard shows green for pilot sources
- [ ] Alerting rules configured and tested

### Phase 2 Readiness

- [ ] Phase 2 requirements documented (API layer, search layer, etc.)
- [ ] Phase 2 timeline published
- [ ] Blockers or risks identified and mitigated
- [ ] Phase 2 kickoff scheduled

## Sign-Off Template

```markdown
## Phase 1 Acceptance Sign-Off

**Gate E Date**: [DATE]  
**Reviewed By**: [Architect], [Product Owner], [Tech Lead]  

### Criteria Status

1. ✅ Source onboarding (plugin + config only)
2. ✅ Canonical read model (Drupal.org + WordPress.org)
3. ✅ Lineage & provenance (canonical_id stability)
4. ✅ Contract test matrix (80% coverage, all passing)
5. ✅ No source-specific API branching

### Quality Metrics

- Test Coverage: 92%
- Type Coverage: 100%
- Linting Issues: 0 (high), 3 (low)
- Documentation: 100% of layers covered

### Phase 1 Complete

Phase 1 deliverables are complete and verified. Approved to proceed with Phase 2.

**Signed**: [Architect Name], [Date]
```

## Failure Scenarios

If any acceptance criterion fails:

1. **Root cause analysis**: Identify why criterion was not met
2. **Remediation plan**: Document specific fixes needed
3. **Re-verification**: Update criterion and re-verify
4. **Gate delay**: Do not advance to Phase 2 until all criteria pass

Common failure modes:

- **"Source onboarding needs core change"**: Indicates abstraction leak; refactor core logic
- **"Test coverage < 80%"**: Add missing unit/integration tests
- **"API exposes source-native fields"**: Remove source-specific fields from schema; re-export with canonical names
- **"Canonical IDs unstable"**: Audit ID generation logic; may indicate deduplication bug
