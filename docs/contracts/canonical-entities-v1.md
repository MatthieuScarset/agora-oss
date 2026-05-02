# Canonical Entities v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Architecture  

## Overview

The canonical entity model defines the core abstractions that Agora uses to represent community data. Every entity from every source is normalized to one of these types. This contract ensures that dashboard, agents, and API consumers do not branch on source-native structures.

## Core Entities

### Actor

A person, bot, or organization in the ecosystem.

```python
{
    # Canonical Identity
    "canonical_id": "actor:drupalorg:user:12345",  # stable UUID-like identifier
    "entity_type": "actor",
    "source_family": "drupalorg",  # drupalorg, wordpressorg, github, gitlab, etc.
    "source_name": "drupal.org community",  # friendly display name
    "source_native_id": "12345",  # original ID in source system
    
    # Display
    "display_name": "Alice Developer",
    "email": "alice@example.com",  # optional, privacy-dependent
    "avatar_url": "https://drupal.org/files/user.jpg",  # optional
    
    # Role & Status
    "roles": ["maintainer", "contributor", "reviewer"],  # tags, not a strict enum
    "activity_marker": "active",  # active, inactive, archived
    "reputation_score": 42,  # optional, source-dependent
    
    # Timestamps
    "created_at": "2015-03-10T14:30:00Z",  # when actor first appeared in source
    "updated_at": "2025-12-01T09:15:00Z",  # last change in source
    "last_active_at": "2025-11-28T16:45:00Z",  # last action
    
    # Lineage & Provenance
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "raw_payload_ref": "s3://agora-raw/drupalorg/users/12345/20260502_080000.json",
    
    # Locale & Language
    "primary_locale": "en",
    "localized_display_name": {"en": "Alice Developer", "es": "Alicia Desarrolladora"},
    
    # Metadata
    "metadata": {
        "source_last_updated": "2025-11-28T16:45:00Z",
        "extraction_method": "api_v2",
        "external_profile_url": "https://drupal.org/u/alice"
    }
}
```

### Project

A software project, module, issue tracker, or related organizational unit.

```python
{
    # Canonical Identity
    "canonical_id": "project:drupalorg:module:views",
    "entity_type": "project",
    "source_family": "drupalorg",
    "source_name": "drupal.org community",
    "source_native_id": "views",
    
    # Display
    "name": "Views",
    "description": "A flexible tool that makes it easy to create the perfect display of your data.",
    "ecosystem": "Drupal",  # Drupal, WordPress, Django, Rails, etc.
    "status": "active",  # active, archived, deprecated, beta
    
    # Organization
    "maintainers": ["actor:drupalorg:user:12345"],  # array of actor canonical_ids
    "homepage_url": "https://www.drupal.org/project/views",
    
    # Timestamps
    "created_at": "2006-04-15T00:00:00Z",
    "updated_at": "2025-11-20T12:00:00Z",
    
    # Lineage & Provenance
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "raw_payload_ref": "s3://agora-raw/drupalorg/projects/views/20260502_080000.json",
    
    # Locale & Language
    "primary_locale": "en",
    "localized_name": {"en": "Views", "es": "Vistas"},
    
    # Metadata
    "metadata": {
        "download_count": 5000000,
        "star_count": 1234,
        "last_release_date": "2025-11-15T00:00:00Z"
    }
}
```

### Issue

A tracked problem, feature request, or task.

```python
{
    # Canonical Identity
    "canonical_id": "issue:drupalorg:project-views:issue:456789",
    "entity_type": "issue",
    "source_family": "drupalorg",
    "source_name": "drupal.org community",
    "source_native_id": "456789",
    
    # Content
    "title": "Improve Views performance with complex filters",
    "description": "When using multiple filters, Views queries become slow...",
    "state": "open",  # open, closed, merged, duplicate, wontfix
    "type": "feature",  # bug, feature, task, documentation, chore
    
    # Relationships
    "project_id": "project:drupalorg:module:views",
    "reporter_id": "actor:drupalorg:user:12345",
    "assignee_ids": ["actor:drupalorg:user:67890"],
    
    # Timestamps
    "created_at": "2024-06-10T10:30:00Z",
    "updated_at": "2025-11-25T14:15:00Z",
    "closed_at": null,  # null if still open
    
    # Lineage & Provenance
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "raw_payload_ref": "s3://agora-raw/drupalorg/issues/456789/20260502_080000.json",
    
    # Locale & Language
    "primary_locale": "en",
    "localized_title": {"en": "Improve Views performance...", "es": "Mejorar rendimiento..."},
    
    # Metadata
    "metadata": {
        "priority": "normal",
        "tags": ["performance", "filters"],
        "comment_count": 15,
        "external_issue_url": "https://drupal.org/project/views/issues/456789"
    }
}
```

### Event

A time-bound occurrence: release, meeting, conference, sprint, deployment.

```python
{
    # Canonical Identity
    "canonical_id": "event:drupalorg:release:drupal-10.2",
    "entity_type": "event",
    "source_family": "drupalorg",
    "source_name": "drupal.org community",
    "source_native_id": "drupal-10.2",
    
    # Display
    "title": "Drupal 10.2 Released",
    "description": "Drupal 10.2.0 is now available with bug fixes and security updates.",
    "event_type": "release",  # release, meeting, conference, sprint, deployment
    
    # Timing
    "start_time": "2025-10-16T00:00:00Z",
    "end_time": null,  # null if single-point-in-time event
    "time_zone": "UTC",
    
    # Participants
    "participants": ["actor:drupalorg:user:12345", "actor:drupalorg:user:67890"],
    "organizers": ["actor:drupalorg:user:12345"],
    
    # Location (optional)
    "location": null,  # null if virtual; otherwise string or geo object
    
    # Relationships
    "project_id": "project:drupalorg:core:drupal",
    
    # Timestamps
    "created_at": "2025-10-01T00:00:00Z",
    "updated_at": "2025-10-16T00:00:00Z",
    
    # Lineage & Provenance
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "raw_payload_ref": "s3://agora-raw/drupalorg/events/drupal-10.2/20260502_080000.json",
    
    # Locale & Language
    "primary_locale": "en",
    "localized_title": {"en": "Drupal 10.2 Released", "es": "Drupal 10.2 Lanzado"},
    
    # Metadata
    "metadata": {
        "external_event_url": "https://www.drupal.org/project/drupal/releases/10.2",
        "attendance_count": 5000  # optional estimate
    }
}
```

### Contribution

An action by an actor on a target: commit, comment, review, vote.

```python
{
    # Canonical Identity
    "canonical_id": "contribution:drupalorg:commit:abc123def456",
    "entity_type": "contribution",
    "source_family": "drupalorg",
    "source_name": "drupal.org community",
    "source_native_id": "abc123def456",
    
    # Type & Content
    "contribution_type": "commit",  # commit, comment, code-review, issue-report, documentation, translation
    "title": "Optimize Views query builder",
    "description": "Refactored the query builder to reduce complexity",
    
    # Relationships
    "actor_id": "actor:drupalorg:user:12345",
    "target_id": "issue:drupalorg:project-views:issue:456789",  # issue, project, or pull-request
    "target_type": "issue",
    
    # Timestamps
    "created_at": "2025-11-20T15:30:00Z",
    "updated_at": "2025-11-20T15:30:00Z",
    
    # Status
    "state": "accepted",  # proposed, accepted, rejected, merged, closed
    
    # Lineage & Provenance
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "raw_payload_ref": "s3://agora-raw/drupalorg/contributions/abc123def456/20260502_080000.json",
    
    # Locale & Language
    "primary_locale": "en",
    "localized_title": {"en": "Optimize Views query builder", "es": "Optimizar constructor de consultas"},
    
    # Metadata
    "metadata": {
        "impact": "high",  # high, medium, low
        "lines_changed": 142,
        "external_url": "https://drupal.org/project/views/issues/456789#comment-123"
    }
}
```

### Relation

A typed link between two entities.

```python
{
    # Canonical Identity
    "canonical_id": "relation:drupalorg:maintains:project-views:actor-12345",
    "entity_type": "relation",
    "source_family": "drupalorg",
    "source_name": "drupal.org community",
    
    # Endpoints
    "from_id": "actor:drupalorg:user:12345",
    "from_type": "actor",
    "to_id": "project:drupalorg:module:views",
    "to_type": "project",
    
    # Semantics
    "relation_type": "maintains",  # maintains, contributes_to, depends_on, authored, reviewed, reported, assigned_to
    
    # Confidence & Source
    "confidence": 1.0,  # 0.0-1.0; 1.0 = explicit in source, <1.0 = inferred
    "inferred": false,  # whether this relation was derived vs. explicit
    
    # Timestamps
    "created_at": "2006-04-15T00:00:00Z",
    "updated_at": "2025-11-20T12:00:00Z",
    "ended_at": null,  # null if active; set when relationship ends
    
    # Lineage & Provenance
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "raw_payload_ref": "s3://agora-raw/drupalorg/relations/20260502_080000.json",
    
    # Metadata
    "metadata": {
        "external_source": "project maintainer list"
    }
}
```

## Required Global Fields

Every entity must include:

| Field              | Type     | Required          | Description                                                                                           |
| ------------------ | -------- | ----------------- | ----------------------------------------------------------------------------------------------------- |
| `canonical_id`     | string   | ✓                 | Stable, globally unique ID (format: `{entity_type}:{source_family}:{source_name}:{source_native_id}`) |
| `entity_type`      | string   | ✓                 | One of: actor, project, issue, event, contribution, relation                                          |
| `source_family`    | string   | ✓                 | drupalorg, wordpressorg, github, gitlab, etc.                                                         |
| `source_name`      | string   | ✓                 | Human-readable name of the source instance                                                            |
| `source_native_id` | string   | ✓                 | Original ID in the source system                                                                      |
| `created_at`       | ISO 8601 | ✓                 | When entity first appeared                                                                            |
| `updated_at`       | ISO 8601 | ✓                 | Last change in source                                                                                 |
| `ingestion_run_id` | string   | ✓                 | Identifier of the ingestion batch                                                                     |
| `raw_payload_ref`  | string   | ✓                 | Pointer to raw source data (S3, filesystem)                                                           |
| `primary_locale`   | BCP 47   | ✓                 | Primary language of the entity (e.g., "en", "es")                                                     |
| `localized_*`      | object   | ✓ for text fields | Map of locale → translated text (must include primary_locale)                                         |

## Schema Validation

All canonical entities must validate against the Pydantic schema defined in `packages/canonical-schema/entities.py`.

## Versioning & Deprecation

- **v1.0.0** (current): Core entities Actor, Project, Issue, Event, Contribution, Relation.
- **Breaking changes** (→ v2.0.0): Removal of required fields, changes to `entity_type` enum.
- **Additive changes** (→ v1.x.0): New optional fields in metadata, new relation types.

## Migration Path for Breaking Changes

When a breaking change is needed:

1. Propose v2.0 with new field names and deprecation notices in v1 docs.
2. Support both v1 and v2 in the API for 2 minor versions.
3. Publish migration guide and timeline (minimum 6 weeks notice).
4. Remove v1 support in the next major release.
