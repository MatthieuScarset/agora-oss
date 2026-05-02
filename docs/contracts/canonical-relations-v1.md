# Canonical Relations v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Architecture  

## Overview

Relations represent typed, directional links between canonical entities. This contract defines the complete ontology of allowed relations, their semantics, and cardinality constraints.

## Relation Ontology

All relations follow the pattern `from_type → relation_type → to_type`.

### Actor Relations

#### `actor --maintains--> project`
An actor maintains (is a primary maintainer of) a project.

- **Cardinality**: Many-to-many
- **Semantics**: Active leadership role; responsible for project governance
- **Confidence**: 1.0 if explicit in source maintainer list; <1.0 if inferred from commit frequency
- **Examples**: Alice maintains Views module, Bob maintains Symfony Framework
- **Reverse**: `project --maintained_by--> actor` (inverse, not stored separately)

#### `actor --contributes_to--> project`
An actor has contributed code, documentation, or other valuable work to a project.

- **Cardinality**: Many-to-many
- **Semantics**: Broader than maintains; includes non-maintainers
- **Confidence**: 1.0 if commit history or explicit credit; <1.0 if inferred from event participation
- **Examples**: Charlie contributed to Django, Diana has contributed patches to Kubernetes
- **Reverse**: `project --contributed_by--> actor`

#### `actor --reports--> issue`
An actor reported (opened/filed) an issue.

- **Cardinality**: Many-to-one (one actor per issue initially, though collaborative filing possible)
- **Semantics**: First author/reporter of the problem
- **Confidence**: 1.0 (explicit in issue metadata)
- **Examples**: Eva reported issue #456789 in Views
- **Reverse**: `issue --reported_by--> actor`

#### `actor --assigned_to--> issue`
An actor is assigned to work on an issue.

- **Cardinality**: Many-to-many
- **Semantics**: Current responsibility to resolve the issue
- **Confidence**: 1.0 (explicit assignment)
- **Examples**: Frank is assigned to issue #456789
- **Reverse**: `issue --assigned_to--> actor`

#### `actor --authored--> contribution`
An actor authored a contribution (commit, comment, review, etc.).

- **Cardinality**: Many-to-one
- **Semantics**: Unique author of a contribution
- **Confidence**: 1.0 (explicit in contribution metadata)
- **Examples**: Grace authored commit abc123def456
- **Reverse**: `contribution --authored_by--> actor`

#### `actor --participated_in--> event`
An actor participated in an event (conference, release party, sprint, etc.).

- **Cardinality**: Many-to-many
- **Semantics**: Attendee or participant
- **Confidence**: 1.0 if RSVP/checkin; <1.0 if inferred from event announcements
- **Examples**: Henry participated in DrupalCamp 2025
- **Reverse**: `event --had_participant--> actor`

#### `actor --organized--> event`
An actor organized/led an event.

- **Cardinality**: Many-to-many
- **Semantics**: Event coordinator or facilitator
- **Confidence**: 1.0 (explicit in event metadata)
- **Examples**: Iris organized the Paris Drupal meetup
- **Reverse**: `event --organized_by--> actor`

### Project Relations

#### `project --depends_on--> project`
A project depends on another project (library, framework, module, etc.).

- **Cardinality**: Many-to-many
- **Semantics**: Hard or soft dependency
- **Confidence**: 1.0 if explicit in package manifest; <1.0 if inferred
- **Examples**: Symfony HTTP foundation depends on Symfony Component
- **Reverse**: `project --depended_on_by--> project`

#### `project --part_of--> project`
A project is part of a larger ecosystem or meta-project.

- **Cardinality**: Many-to-one (a module belongs to one core)
- **Semantics**: Hierarchical containment or bundle relationship
- **Confidence**: 1.0 (explicit in source structure)
- **Examples**: Views module is part of Drupal core ecosystem
- **Reverse**: `project --has_subproject--> project`

#### `project --created--> issue` (implicit)
A project has issues (tracked problems). This is typically not materialized as a separate relation; instead, issues have a `project_id` field.

### Issue Relations

#### `issue --depends_on--> issue`
An issue depends on the resolution of another issue (blocking, prerequisite).

- **Cardinality**: Many-to-many
- **Semantics**: One issue cannot be resolved until another is
- **Confidence**: 1.0 (explicit in issue tracker)
- **Examples**: Issue #500 blocks issue #501
- **Reverse**: `issue --blocks--> issue`

#### `issue --related_to--> issue`
An issue is related to another (same root cause, similar scope, duplicate).

- **Cardinality**: Many-to-many
- **Semantics**: Connected but not strictly dependent
- **Confidence**: Usually <1.0 (inferred or manually curated)
- **Examples**: Issue #456 is a duplicate of issue #123
- **Reverse**: `issue --related_to--> issue` (symmetric)

#### `issue --belongs_to--> project` (implicit)
An issue belongs to a project. This is typically not materialized; instead, issues have a `project_id` field.

### Contribution Relations

#### `contribution --addresses--> issue`
A contribution (commit, PR, comment) addresses/resolves an issue.

- **Cardinality**: Many-to-one
- **Semantics**: The contribution is a direct response to the issue
- **Confidence**: 1.0 if explicit linking (e.g., "Fixes #456"); <1.0 if inferred from metadata
- **Examples**: Commit abc123 addresses issue #456
- **Reverse**: `issue --addressed_by--> contribution`

#### `contribution --cites--> contribution`
A contribution references or builds on another contribution.

- **Cardinality**: Many-to-many
- **Semantics**: Related work, follow-up, or inspired-by
- **Confidence**: Usually <1.0 (inferred from commit messages or code comments)
- **Examples**: PR #200 cites PR #150
- **Reverse**: `contribution --cited_by--> contribution`

### Event Relations

#### `event --announces--> project`
An event announces or introduces a project (release event, product launch, new feature).

- **Cardinality**: Many-to-many
- **Semantics**: The event is a public unveiling or major milestone communication
- **Confidence**: 1.0 (explicit event description)
- **Examples**: DrupalCamp announces new Views features
- **Reverse**: `project --announced_at--> event`

#### `event --features--> contribution`
An event highlights or features a contribution (award, recognition, keynote topic).

- **Cardinality**: Many-to-many
- **Semantics**: Notable mention or recognition
- **Confidence**: Usually 1.0
- **Examples**: Paris Drupal Meetup features 5 recent performance improvements
- **Reverse**: `contribution --featured_in--> event`

## Canonical Relation Types

**Summary table** of all allowed `relation_type` values:

| From Type    | Relation Type   | To Type      | Cardinality | Confidence     |
| ------------ | --------------- | ------------ | ----------- | -------------- |
| actor        | maintains       | project      | N:M         | 1.0 (explicit) |
| actor        | contributes_to  | project      | N:M         | 1.0 or <1.0    |
| actor        | reports         | issue        | N:1         | 1.0            |
| actor        | assigned_to     | issue        | N:M         | 1.0            |
| actor        | authored        | contribution | N:1         | 1.0            |
| actor        | participated_in | event        | N:M         | 1.0 or <1.0    |
| actor        | organized       | event        | N:M         | 1.0            |
| project      | depends_on      | project      | N:M         | 1.0 or <1.0    |
| project      | part_of         | project      | N:1         | 1.0            |
| issue        | depends_on      | issue        | N:M         | 1.0            |
| issue        | related_to      | issue        | N:M         | <1.0           |
| contribution | addresses       | issue        | N:1         | 1.0 or <1.0    |
| contribution | cites           | contribution | N:M         | <1.0           |
| event        | announces       | project      | N:M         | 1.0            |
| event        | features        | contribution | N:M         | 1.0            |

## Inference Rules

Some relations can be inferred from other relations or data:

1. **Transitive Contribution**:
   - If `actor --authored--> contribution` AND `contribution --addresses--> issue`, infer `actor --addressed--> issue` with lower confidence.

2. **Reverse Relations**:
   - All forward relations have implicit reverses (listed as "Reverse" in relation definitions above). Reverses are not stored separately but are computed on query.

3. **Project Dependency Chains**:
   - If `project_a --depends_on--> project_b` AND `project_b --depends_on--> project_c`, infer `project_a --transitively_depends_on--> project_c` for reachability analysis.

## Relation Metadata

Every relation includes:

- **confidence**: 0.0-1.0 confidence score
- **inferred**: boolean flag (true if derived vs. explicit)
- **created_at**: timestamp when relation first detected
- **updated_at**: timestamp when relation last changed
- **ended_at**: nullable; set if the relation is no longer active (e.g., actor left a project)
- **source_family** and **source_native_id**: trace back to source

## Constraints & Validation

1. **No self-loops**: `from_id != to_id` (an entity cannot relate to itself)
2. **Type consistency**: Relation type must be valid for the given `from_type` and `to_type`
3. **Cardinality**: Validate that enforced cardinality rules are respected (e.g., "reports" is N:1)
4. **Stability**: Once a relation canonical_id is published, it must remain stable across ingestion runs

## Versioning & Deprecation

- **v1.0.0** (current): Core relation types listed above.
- **Additive changes** (→ v1.x.0): New relation types can be added without breaking existing consumers.
- **Breaking changes** (→ v2.0.0): Removal or renaming of relation types; changes to cardinality constraints.

### Adding New Relation Types

To add a new relation type in a future version:

1. Propose the new type with clear semantics and examples.
2. Validate that it does not conflict with existing types.
3. Update the relation ontology table.
4. Publish migration guide if existing queries need to adapt.
