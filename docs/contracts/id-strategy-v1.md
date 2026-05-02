# ID Strategy v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Architecture  

## Overview

Canonical IDs uniquely identify entities across all sources and ingestion runs. This contract defines the ID format, generation strategy, identity stitching rules, and deduplication semantics.

## Canonical ID Format

All canonical IDs follow a hierarchical, URL-safe format:

```
{entity_type}:{source_family}:{source_instance}:{source_native_id}
```

### Components

| Component          | Description                                                                      | Example                                            |
| ------------------ | -------------------------------------------------------------------------------- | -------------------------------------------------- |
| `entity_type`      | actor, project, issue, event, contribution, relation                             | actor                                              |
| `source_family`    | Ecosystem or platform family                                                     | drupalorg, wordpressorg, github, gitlab            |
| `source_instance`  | Named instance of the source (may be same as family for single-instance sources) | drupalorg, wordpress-acme, github, github-internal |
| `source_native_id` | Original ID in the source system; URL-encoded if necessary                       | user:12345, project/views, abc123def456            |

### Examples

- `actor:drupalorg:drupalorg:user:12345`
- `project:wordpressorg:wordpress-acme:plugin:advanced-custom-fields`
- `issue:github:github:repo/django/django/issues/45678`
- `event:drupalorg:drupalorg:release:drupal-10.2`
- `contribution:gitlab:gitlab:commit:abc123def456`
- `relation:drupalorg:drupalorg:maintains:project-views:user-12345`

## Identity Stitching

Identity stitching is the process of recognizing that an entity from one source is the same as (or related to) an entity from another source.

### Stitching Rules

1. **Exact Email Match** (Actors):
   - If two actors have the same email address (normalized: lowercase, whitespace removed), they are the same person.
   - Priority: Email > external_profile_url > name similarity

2. **External Profile URL Match**:
   - If two actors have the same GitHub profile URL (or other external links), they are likely the same person.
   - Confidence: 0.9

3. **Name + Domain Heuristic**:
   - If two actors have the same display name and both are from the same domain (e.g., both @example.com emails), assume same person.
   - Confidence: 0.7

4. **Project Name Standardization**:
   - Project canonical IDs are based on source-native project slugs, which are unique within a source.
   - Cross-source project stitching is **not** attempted; Drupal Views != WordPress Advanced Custom Fields even if they have similar names.

5. **Issue Stitching**:
   - Issues are tied to their project; no cross-project stitching.
   - If the same issue is filed in multiple sources (e.g., dual-tracked Drupal.org and GitHub), map via configuration, not automatic inference.

### Stitching Artifacts

Stitching results are stored in the **Identity Map**, a separate table/collection:

```python
{
    "canonical_id": "actor:drupalorg:drupalorg:user:12345",
    "linked_canonical_ids": [
        "actor:github:github:user/alice-dev",
        "actor:wordpressorg:wordpress-acme:user:alice"
    ],
    "stitching_rules": [
        {"rule": "email_match", "confidence": 1.0, "matched_id": "actor:github:github:user/alice-dev"},
        {"rule": "external_url_match", "confidence": 0.9, "matched_id": "actor:wordpressorg:wordpress-acme:user:alice"}
    ],
    "created_at": "2026-05-02T08:00:00Z",
    "updated_at": "2026-05-02T08:00:00Z"
}
```

### Stitching Quality & Confidence

- **1.0**: Exact match (email, verified account linking)
- **0.9**: High confidence (URL match, profile metadata)
- **0.7**: Medium confidence (name + domain heuristic)
- **0.5**: Low confidence (name similarity alone, requires human review)

Only stitches with confidence >= 0.8 are applied automatically. Lower confidence matches are flagged for manual review.

## Deduplication Strategy

Deduplication detects when the same entity appears multiple times in the canonical model (e.g., due to multiple ingestion runs, API pagination issues, or data model bugs).

### Deduplication Rules

1. **Exact Canonical ID Match**:
   - If `canonical_id` is identical, use the newest `updated_at` version and discard the older.

2. **Content Hash Collision**:
   - Compute a content hash (SHA256 of normalized key fields) for each entity.
   - If two entities with different `canonical_id` have the same content hash and are from the same source, they are duplicates.
   - Keep the one with the earliest `created_at` timestamp; discard the newer one.

3. **Actor Dedup by Email**:
   - If two actors have the same email and are from the same source, they are duplicates.
   - Merge into a single entity, preserving the earlier `created_at`.

4. **Project Dedup by Name + Ecosystem**:
   - If two projects have the same name and ecosystem, manually review (usually indicates a data quality issue).

### Deduplication Artifacts

Deduplication decisions are logged in an **audit trail**:

```python
{
    "dedup_event_id": "dedup:2026-05-02T08:00:00Z:00001",
    "action": "merged",  # merged, discarded, flagged
    "canonical_id_kept": "actor:drupalorg:drupalorg:user:12345",
    "canonical_ids_discarded": ["actor:drupalorg:drupalorg:user:12345-duplicate"],
    "reason": "content_hash_collision",
    "confidence": 1.0,
    "timestamp": "2026-05-02T08:15:00Z"
}
```

## Source Native ID Encoding

Source-native IDs may contain special characters (/, :, etc.). They must be URL-encoded in the canonical ID:

| Character | Encoded |
| --------- | ------- |
| /         | %2F     |
| :         | %3A     |
| #         | %23     |
| @         | %40     |
| space     | %20     |

**Example**:
- Source: `user:alice@example.com/profile`
- Canonical ID: `actor:drupalorg:drupalorg:user%3Aalice%40example.com%2Fprofile`

## ID Stability Guarantee

Once a canonical ID is published (in an API response or stored in the database), it must **never change**. This ensures:

- External systems can store and reference canonical IDs reliably
- Links/relations remain valid across schema versions
- Audit trails and lineage are queryable by canonical ID

### Consequences of ID Changes

If a canonical ID must be changed due to a schema bug or discovery of incorrect stitching:

1. The old ID is marked as **deprecated** (not deleted)
2. A **redirect mapping** is created: `old_id → new_id`
3. APIs return both old and new IDs for a transition period (minimum 2 weeks)
4. A migration guide is published
5. After the grace period, the old ID is archived (soft-deleted)

## Version Lineage

Every entity tracks its version history via `ingestion_run_id`. This allows querying "what was the state of entity X as of date Y":

```python
# Query: Get all versions of actor canonical_id as of 2025-11-01
SELECT * FROM canonical_entities
WHERE canonical_id = 'actor:drupalorg:drupalorg:user:12345'
  AND ingestion_run_id <= 'ingest:2025-11-01T23:59:59Z:drupalorg'
ORDER BY ingestion_run_id DESC
LIMIT 1
```

## Cross-Source Canonical ID Collision

In the unlikely event that two different entities from different sources have identical `source_native_id` and `entity_type`, the canonical IDs will naturally differ by `source_family` and `source_instance`, preventing collision:

- `issue:drupalorg:drupalorg:issue:12345` (Drupal.org issue #12345)
- `issue:github:github:issue:12345` (GitHub issue #12345)

These are distinct entities and remain distinct in the canonical model.

## Versioning & Deprecation

- **v1.0.0** (current): Hierarchical ID format, email-based stitching, content-hash deduplication.
- **Future enhancements** (→ v1.x.0):
  - UUID-based canonical IDs as an option (for shorter URLs)
  - Configurable stitching rules per source family
  - Machine-learning based entity resolution
- **Breaking changes** (→ v2.0.0):
  - Removal of hierarchical format
  - Changes to stitching confidence thresholds

## Examples

### Actor Stitching Example

**Input**: Ingestion run brings in data from Drupal.org and GitHub

Drupal.org user:
```json
{
    "source_native_id": "user:12345",
    "display_name": "Alice Developer",
    "email": "alice@example.com"
}
```

GitHub user (if available via API):
```json
{
    "source_native_id": "user/alice-dev",
    "display_name": "Alice Developer",
    "email": "alice@example.com",
    "external_profile_url": "https://github.com/alice-dev"
}
```

**Stitching Decision**:
- Email match: `alice@example.com` (confidence 1.0) → canonical_id: `actor:drupalorg:drupalorg:user:12345`
- GitHub user linked via identity map
- Reverse link: When querying by canonical_id, both source references are returned

### Project (No Cross-Source Stitching)

Drupal Views (Module):
- `canonical_id`: `project:drupalorg:drupalorg:views`

WordPress Advanced Custom Fields (Plugin):
- `canonical_id`: `project:wordpressorg:wordpress-acme:advanced-custom-fields`

These are **never** stitched together, even though both provide "field management" functionality. They remain distinct.
