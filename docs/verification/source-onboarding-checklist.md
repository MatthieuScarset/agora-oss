# Source Onboarding Checklist

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  

## Overview

This checklist guides operators through adding a new data source to Agora OSS. Following this checklist ensures the source is properly configured, tested, and monitored.

## Pre-Onboarding

### Research & Planning

- [ ] **Understand the source**: Read API documentation, data model, auth requirements
- [ ] **Identify entity types**: Which canonical entity types (actor, project, issue, etc.) does this source provide?
- [ ] **Map fields**: Document source field names and their canonical equivalents
- [ ] **Check existing plugin**: Does a plugin already exist for this source family? If yes, reuse it. If no, plan plugin development.
- [ ] **Estimate effort**: How complex is the data model? Any special handling needed?

### Stakeholder Approval

- [ ] **Architecture review**: Confirm data model and abstraction fit
- [ ] **Product approval**: Confirm source adds value to the platform
- [ ] **Ops approval**: Confirm monitoring, runbooks, and support plans
- [ ] **Security review**: Confirm API auth, data privacy, compliance requirements

## Source Configuration

### Create Config File

- [ ] **Create directory**: `configs/sources/{source_family}/{instance_name}/`
- [ ] **Create YAML file**: `configs/sources/{source_family}/{instance_name}/default.yaml`
- [ ] **Populate required fields**:
  - [ ] `name`: Human-readable name
  - [ ] `source_family`: Family identifier
  - [ ] `connector.plugin_name`: Which plugin to use
  - [ ] `connector.plugin_version`: Plugin version
  - [ ] `endpoints`: At least one endpoint for each entity type
  - [ ] `mapping_pack`: Reference to mapping rules file
- [ ] **Populate optional fields**:
  - [ ] `authentication`: Auth type and credentials reference
  - [ ] `refresh_policy`: Refresh schedule
  - [ ] `quality_policy`: Quality rules
  - [ ] `locales`: Supported languages
  - [ ] `metadata`: Tags, maintainer, contact

### Validate Configuration

- [ ] **Run schema validation**: 
  ```bash
  python -m agora.config validate configs/sources/{source_family}/{instance_name}/default.yaml
  ```
- [ ] **Check plugin exists**: 
  ```bash
  ls plugins/{plugin_name}/connector.py
  ```
- [ ] **Check mapping exists**: 
  ```bash
  ls configs/mappings/{source_family}/default.mapping.yaml
  ```
- [ ] **Test credentials**: If auth required, verify credentials are accessible:
  ```bash
  echo $API_KEY_ENV_VAR
  ```

### Example Config

Create file: `configs/sources/github/opensource-projects.yaml`

```yaml
name: "GitHub Open Source Projects"
source_family: "github"

connector:
  plugin_name: "github"
  plugin_version: "1.0.0"

endpoints:
  - url: "https://api.github.com/repos"
    entity_type: "project"
    pagination:
      strategy: "page"
      page_size: 100

authentication:
  type: "api_key"
  credentials_ref: "env:GITHUB_TOKEN"

refresh_policy:
  interval: "0 */12 * * *"
  strategy: "incremental"

quality_policy: "quality-policy.yaml"
mapping_pack: "github/default.mapping.yaml"

locales:
  - "en"

primary_locale: "en"

metadata:
  ecosystem: "GitHub"
  maintainer: "Platform Team"
  contact: "platform@example.com"
  tags:
    - "github"
    - "open-source"

enabled: false  # Start disabled; enable after testing
```

## Mapping Rules

### Check Mapping Pack Exists

- [ ] **Mapping file exists**: `configs/mappings/{source_family}/default.mapping.yaml`
- [ ] **Mapping schema valid**:
  ```bash
  python -m agora.mapping validate configs/mappings/{source_family}/default.mapping.yaml
  ```

### Test Mapping with Fixtures

- [ ] **Create fixture files**: Sample source data in `data/fixtures/sources/{source_family}/`
- [ ] **Dry-run mapping**: 
  ```bash
  python -m agora.mapping dryrun \
    --source-family {source_family} \
    --fixture data/fixtures/sources/{source_family}/sample.json
  ```
- [ ] **Inspect canonical output**: Verify fields are correctly mapped
- [ ] **Check all entity types**: Test at least one entity of each type from source

## Plugin Configuration

### Verify Plugin Implementation

- [ ] **Plugin module exists**: `plugins/{plugin_name}/`
- [ ] **Plugin class exists**: `plugins/{plugin_name}/connector.py` has `Connector(IConnectorPlugin)` class
- [ ] **All methods implemented**: discover_capabilities, initialize, fetch_full, fetch_incremental, emit_raw_envelope, map_to_canonical, report_health, shutdown
- [ ] **Tests exist**: `plugins/{plugin_name}/test_connector.py` with unit and integration tests

### Run Plugin Tests

- [ ] **Unit tests pass**: 
  ```bash
  pytest plugins/{plugin_name}/test_connector.py::TestConnectorUnit -v
  ```
- [ ] **Integration tests pass** (if credentials available): 
  ```bash
  pytest plugins/{plugin_name}/test_connector.py::TestConnectorIntegration -v
  ```

## Local Testing

### Test Single Ingestion Run

Enable source in config and run a single ingestion:

```bash
# Set config to enabled
sed -i 's/enabled: false/enabled: true/' configs/sources/{source_family}/{instance_name}/default.yaml

# Run ingestion
python -m agora.ingest \
  --source-family {source_family} \
  --config configs/sources/{source_family}/{instance_name}/default.yaml \
  --dry-run

# Check results
python -m agora.query "SELECT * FROM canonical_entities WHERE source_family='{source_family}' LIMIT 10;"
```

### Verify Data Quality

- [ ] **No errors in logs**: Check that ingestion completed without errors
- [ ] **Record count reasonable**: Is the number of ingested records expected? (e.g., if you know the source has 500 projects, did we ingest ~500?)
- [ ] **Sample records correct**: Spot-check 3-5 records to ensure mapping is accurate
- [ ] **Relationships extracted**: Are expected relations (e.g., maintains, contributes_to) present?
- [ ] **Timestamps valid**: Are created_at and updated_at reasonable?
- [ ] **IDs stable**: Run ingestion twice; IDs should not change

**Example query**:
```sql
-- Check record count
SELECT COUNT(*) as total FROM canonical_entities WHERE source_family='github';

-- Sample records
SELECT canonical_id, entity_type, display_name, created_at 
FROM canonical_entities 
WHERE source_family='github' 
LIMIT 5;

-- Check relationships
SELECT COUNT(*) as total FROM relations WHERE source_family='github';
```

### Test Incremental Fetch (if supported)

- [ ] **Full fetch**: Run ingestion with fresh state (no cursor)
- [ ] **Incremental fetch**: Run again with small time window (e.g., last 1 hour)
- [ ] **Verify delta**: Incremental should only return changed records
- [ ] **Cursor state preserved**: Each run should update cursor for next run

## Dashboard & API Testing

### Verify in Dashboard

- [ ] **Source appears in admin list**: Navigate to `/admin/sources`
- [ ] **Health status shows**: Green (healthy) or other appropriate status
- [ ] **Records searchable**: Try searching for entities from new source in dashboard
- [ ] **Filters work**: Filter by source_family, locale, etc.
- [ ] **No UI errors**: No console errors in browser dev tools

### Test API Endpoints

- [ ] **List entities from source**: 
  ```bash
  curl http://localhost:8000/api/v1/entities?source_family={source_family} | jq '.'
  ```
- [ ] **Get single entity**:
  ```bash
  curl http://localhost:8000/api/v1/entities/{canonical_id} | jq '.'
  ```
- [ ] **Search across sources** (including new one):
  ```bash
  curl "http://localhost:8000/api/v1/search?q=django&source_family={source_family}" | jq '.'
  ```

## Health & Monitoring

### Configure Alerts

- [ ] **Add alert rules**: Extend `monitoring/alerts.yaml` with rules for this source
- [ ] **Test alert**: Manually trigger (e.g., pause plugin) and verify alert fires
- [ ] **Alert routing**: Ensure alert goes to correct team/channel

### Verify Health Endpoint

- [ ] **Health check passes**: 
  ```bash
  curl http://localhost:8000/admin/health/sources/{source_family} | jq '.status'
  ```
- [ ] **Metrics present**: Prometheus metrics for this source are exported
- [ ] **Dashboard visible**: Source metrics visible in Grafana

## Staging/Production Deployment

### Prepare for Deployment

- [ ] **Config finalized**: All required fields populated, credentials injected via secrets
- [ ] **Tests pass in CI**: All plugin and contract tests passing
- [ ] **Documentation updated**: Add source to admin docs, operator runbook
- [ ] **Runbook prepared**: How to add source to prod, how to debug, escalation contacts

### Deploy to Staging

- [ ] **Deploy config**: Push `configs/sources/{source_family}/` to staging
- [ ] **Verify in staging**: Run ingestion, check health, test API
- [ ] **Staging sign-off**: Platform team approves

### Deploy to Production

- [ ] **Capacity plan**: Will ingestion impact prod infrastructure?
- [ ] **Maintenance window**: Schedule deployment during off-peak if needed
- [ ] **Secrets injected**: Credentials loaded from prod secrets store
- [ ] **Gradual rollout**: Start with single ingestion run, verify, then enable scheduling
- [ ] **Monitoring active**: Ops team monitoring alerts and metrics
- [ ] **Rollback plan**: Know how to disable source if issues arise

### Post-Deployment

- [ ] **Production ingestion runs**: First 3 scheduled runs complete successfully
- [ ] **Data freshness**: Data updated at expected intervals
- [ ] **No alerts firing**: Health checks green, error rates normal
- [ ] **Operator notified**: Support team knows source is live and has runbooks

## Ongoing Operations

### Weekly Review

- [ ] **Health dashboard**: All green?
- [ ] **Error rate**: Below acceptable threshold (<1% errors)?
- [ ] **Data freshness**: Most recent data within expected window?
- [ ] **API latency**: Response times within SLA?

### Monthly Review

- [ ] **Ingestion performance**: Is it getting slower? Any blockers?
- [ ] **Data quality**: Any new issues found? (dedup failures, mapping errors)
- [ ] **Operator feedback**: Any issues reported? Runbook improvements needed?
- [ ] **Cost analysis** (if cloud): Storage, compute, API call costs as expected?

### Quarterly Review

- [ ] **Dependency updates**: New plugin/mapping version available? Should we upgrade?
- [ ] **Source API changes**: Has source API changed? Mapping still correct?
- [ ] **Business value**: Is this source still providing value to users?
- [ ] **Retention policy**: Is data older than retention policy still stored?

## Troubleshooting Common Issues

### Issue: "ConfigError: Missing required field"

**Cause**: Config file incomplete or malformed YAML  
**Fix**:
1. Check config file against source-config-schema-v1.md
2. Validate YAML syntax: `python -m yaml config.yaml`
3. Ensure all required fields present

### Issue: "AuthError: Invalid credentials"

**Cause**: API key not valid, expired, or permissions insufficient  
**Fix**:
1. Verify credentials in secret store: `echo $CREDENTIAL_ENV_VAR`
2. Test credentials directly against source API
3. Check if source requires specific permissions (scopes, roles)

### Issue: "MappingError: Cannot map to canonical"

**Cause**: Source data structure doesn't match expected mapping  
**Fix**:
1. Inspect raw source data: `python -m agora.debug show-raw {source_family} --limit 1`
2. Compare against mapping rules: `configs/mappings/{source_family}/default.mapping.yaml`
3. Update mapping rules if source data format changed
4. Re-test with fixtures

### Issue: "Staleness detected: Data not updated in 48 hours"

**Cause**: Ingestion not running or source API down  
**Fix**:
1. Check refresh schedule: `grep interval configs/sources/{source_family}/*.yaml`
2. Check plugin health: `curl http://localhost:8000/admin/health/sources/{source_family}`
3. Check logs for errors: `docker logs agora-ingestion | grep {source_family}`
4. Try manual ingestion: `python -m agora.ingest --source-family {source_family}`

## Sign-Off Checklist

When all items complete, request sign-off:

```markdown
## Source Onboarding Complete

**Source**: {source_family} ({instance_name})  
**Date**: {date}  
**Operator**: {name}  

All checklist items verified. Source is healthy and ready for production use.

**Signed**: {name}, {date}
```
