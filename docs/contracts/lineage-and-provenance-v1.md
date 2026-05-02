# Lineage & Provenance v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Architecture  

## Overview

Every entity in the canonical model carries provenance metadata: where it came from, how it was transformed, and which source data it represents. This enables:

- **Audit trails**: Trace any fact back to its source
- **Data quality assessment**: Identify stale or unreliable entities
- **Change tracking**: Detect which fields changed between ingestion runs
- **Root-cause analysis**: Debug data anomalies or discrepancies

## Provenance Fields

Every canonical entity includes the following provenance fields:

### Ingestion Run ID

```python
"ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg"
```

**Format**: `ingest:{timestamp}:{source_family}`

**Purpose**: Uniquely identifies an ingestion batch. All entities ingested in the same run share the same `ingestion_run_id`.

**Usage**: Query all entities updated in a specific run; detect stale data if not refreshed.

### Raw Payload Reference

```python
"raw_payload_ref": "s3://agora-raw/drupalorg/users/12345/20260502_080000.json"
```

**Format**: Pointer to object storage (S3-compatible, filesystem URI, or other)

**Purpose**: Enables retrieval of the original, unmodified source data for a given entity. Supports:
- Manual inspection if canonical data seems wrong
- Replay of normalization logic if schema changes
- Compliance with data retention policies

**Storage**: Raw payloads are stored with content-addressable paths:
- `s3://agora-raw/{source_family}/{entity_type}/{source_native_id}/{ingestion_timestamp}.json`
- Retention: Configurable (default: 90 days; can be extended per compliance needs)

## Audit Trail

Every change to a canonical entity is logged in an immutable audit table:

```python
{
    "audit_id": "audit:2026-05-02T08:15:00Z:00001",
    "canonical_id": "actor:drupalorg:drupalorg:user:12345",
    "action": "created",  # created, updated, merged, deduped, stitched
    "old_value": null,
    "new_value": {
        "display_name": "Alice Developer",
        "email": "alice@example.com",
        # ... full entity
    },
    "changed_fields": ["display_name", "email"],
    "reason": "ingestion_run",
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "timestamp": "2026-05-02T08:15:00Z",
    "created_by": "connector:drupal.org:v1.2"
}
```

### Audit Actions

| Action     | Meaning                                            |
| ---------- | -------------------------------------------------- |
| `created`  | Entity first appeared in canonical model           |
| `updated`  | Fields changed due to new ingestion data           |
| `merged`   | Two canonical IDs merged due to identity stitching |
| `deduped`  | Duplicate entity removed; data consolidated        |
| `stitched` | Entity linked to another entity via identity map   |
| `archived` | Entity marked as inactive/deleted in source        |

## Data Lineage Example

**Scenario**: Drupal.org user Alice is stitched to GitHub user alice-dev.

1. **Ingestion Run 1** (Drupal.org):
   ```
   audit_id: audit:2026-05-02T08:00:00Z:00001
   canonical_id: actor:drupalorg:drupalorg:user:12345
   action: created
   new_value: {display_name: "Alice Developer", email: "alice@example.com"}
   ingestion_run_id: ingest:2026-05-02T08:00:00Z:drupalorg
   ```

2. **Ingestion Run 2** (GitHub):
   ```
   audit_id: audit:2026-05-02T08:05:00Z:00001
   canonical_id: actor:github:github:user/alice-dev
   action: created
   new_value: {display_name: "Alice Developer", email: "alice@example.com"}
   ingestion_run_id: ingest:2026-05-02T08:05:00Z:github
   ```

3. **Identity Stitching** (Automatic):
   ```
   audit_id: audit:2026-05-02T08:10:00Z:00001
   canonical_id: actor:drupalorg:drupalorg:user:12345
   action: stitched
   new_value: {linked_ids: ["actor:github:github:user/alice-dev"]}
   reason: identity_stitching_email_match
   ```

**Query**: What is the complete provenance of Alice's Drupal.org account?
```sql
SELECT * FROM audit_trail
WHERE canonical_id = 'actor:drupalorg:drupalorg:user:12345'
ORDER BY timestamp ASC
```

**Result**: Full timeline of all changes, including when GitHub linkage was added.

## Change Tracking

When an entity's data changes between ingestion runs, the audit trail records:

```python
{
    "audit_id": "audit:2026-05-02T09:00:00Z:00001",
    "canonical_id": "actor:drupalorg:drupalorg:user:12345",
    "action": "updated",
    "old_value": {
        "display_name": "Alice Developer",
        "updated_at": "2025-11-01T12:00:00Z"
    },
    "new_value": {
        "display_name": "Alice D.",  # Name shortened
        "updated_at": "2025-11-28T09:15:00Z"
    },
    "changed_fields": ["display_name", "updated_at"],
    "ingestion_run_id": "ingest:2026-05-02T09:00:00Z:drupalorg",
    "timestamp": "2026-05-02T09:00:00Z"
}
```

### Change Detection Algorithm

1. Fetch the canonical entity from the previous ingestion run (if it exists).
2. Compute a diff between old and new payloads.
3. Log all changed fields in the audit trail.
4. Update the entity's `updated_at` timestamp.
5. Preserve `created_at` (immutable).

## Freshness & Staleness

Entities are marked as potentially stale if not updated within a configurable window:

```python
# Config: quality-policy.yaml
staleness_window:
  actor: 180 days
  project: 365 days
  issue: 30 days
  event: 1 day
  contribution: 365 days
```

Query to find stale actors:
```sql
SELECT canonical_id, updated_at
FROM canonical_entities
WHERE entity_type = 'actor'
  AND updated_at < NOW() - INTERVAL '180 days'
  AND source_family = 'drupalorg'
ORDER BY updated_at ASC
```

## Data Transformation Chain

Entities undergo a multi-step transformation; each step is logged:

```python
{
    "transformation_chain": [
        {
            "step": 1,
            "stage": "extract",
            "source": "drupal.org/api/v2/users/12345",
            "timestamp": "2026-05-02T08:00:00Z",
            "status": "success"
        },
        {
            "step": 2,
            "stage": "normalize",
            "rule_set": "drupalorg/default.mapping.yaml",
            "timestamp": "2026-05-02T08:01:00Z",
            "status": "success"
        },
        {
            "step": 3,
            "stage": "enrich",
            "enrichment": "detect_language",
            "timestamp": "2026-05-02T08:02:00Z",
            "status": "success"
        },
        {
            "step": 4,
            "stage": "validate",
            "schema": "canonical-entities-v1.schema.json",
            "timestamp": "2026-05-02T08:03:00Z",
            "status": "success"
        },
        {
            "step": 5,
            "stage": "store",
            "destination": "postgresql://canonical_entities",
            "timestamp": "2026-05-02T08:04:00Z",
            "status": "success"
        }
    ]
}
```

If any step fails, the entity is quarantined and logged for manual review.

## Metadata Object

Every entity includes a metadata object for source-specific and operational information:

```python
"metadata": {
    # Source-specific
    "source_last_updated": "2025-11-28T16:45:00Z",
    "extraction_method": "api_v2",
    "external_profile_url": "https://drupal.org/u/alice",
    "avatar_hash": "abc123def456",
    
    # Operational
    "normalized_via_version": "default.mapping.yaml:v1.2",
    "last_validation_timestamp": "2026-05-02T08:03:00Z",
    "validation_status": "passed",
    
    # Enrichment
    "language_detected": "en",
    "language_confidence": 0.98,
    
    # Quality
    "missing_fields": [],
    "warnings": []
}
```

## Compliance & Data Retention

### GDPR Considerations

If an actor's personal data (email, name) is requested to be deleted:

1. The canonical entity is **soft-deleted** (marked with `deleted_at` timestamp)
2. PII fields are anonymized (email → hash, name → "Deleted User")
3. All audit trail entries are retained (for compliance audit)
4. Raw payloads are purged if retention policy allows
5. Relations involving the deleted actor are also marked as deleted

### Data Retention Policy

- **Raw payloads**: 90 days (configurable per source)
- **Canonical entities**: Indefinite (soft-delete when removed from source)
- **Audit trail**: Indefinite (immutable)
- **Deduplication logs**: 365 days
- **Identity map**: Indefinite

## Version History Query Pattern

To query the state of an entity as of a specific date:

```python
# Query: What was Alice's data on 2025-11-01?
SELECT canonical_id, new_value
FROM audit_trail
WHERE canonical_id = 'actor:drupalorg:drupalorg:user:12345'
  AND timestamp <= '2025-11-01T23:59:59Z'
ORDER BY timestamp DESC
LIMIT 1
```

## Versioning & Deprecation

- **v1.0.0** (current):
  - Ingestion run ID tracking
  - Raw payload references
  - Audit trail with action logging
  - Staleness detection
- **Future enhancements** (→ v1.x.0):
  - Automated transformation-step tracing
  - Integration with OpenTelemetry for distributed tracing
  - Graph-based lineage visualization
- **Breaking changes** (→ v2.0.0):
  - Changes to audit trail schema
  - Changes to retention policies
