# Mapping Rules v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Data Connector  

## Overview

Mapping rules transform source-native data into canonical entities. A mapping pack is a YAML/JSON file that defines:

- **Field mappings**: Which source fields map to which canonical fields
- **ID generation**: How to compute the canonical_id
- **Relationships**: Which relationships to extract
- **Transformations**: How to normalize values
- **Stitching rules**: How to identify the same entity across sources
- **Conditionals**: Conditional mappings based on data content

Each source family has one or more mapping packs (e.g., `drupalorg/default.mapping.yaml`).

## Mapping Pack Structure

```yaml
# configs/mappings/drupalorg/default.mapping.yaml

version: "1.0.0"
source_family: "drupalorg"
description: "Default mapping for Drupal.org ecosystem"

entity_mappings:
  actor:
    source_entity_name: "user"
    
    identity:
      template: "actor:{source_family}:{source_name}:{id}"
      fields:
        - "id"
    
    field_map:
      canonical_id: null  # Computed by identity template
      display_name: "name"
      email: "mail"
      created_at: "created"
      updated_at: "changed"
      primary_locale: "'en'"  # Literal value
      roles: 
        source_field: "roles"
        transform: "split_comma"
    
    relationships:
      - relation_type: "maintains"
        target_entity: "project"
        source_field: "project_ids"
        confidence: 1.0
      
      - relation_type: "contributes_to"
        target_entity: "project"
        source_field: "contributions"
        confidence: 0.8
    
    conditional_mappings:
      - condition: "status == 'active'"
        field_map:
          activity_marker: "'active'"
      
      - condition: "status == 'blocked'"
        field_map:
          activity_marker: "'inactive'"

  project:
    source_entity_name: "node"
    
    identity:
      template: "project:{source_family}:{source_name}:{nid}"
      fields:
        - "nid"
    
    field_map:
      display_name: "title"
      description: "body"
      ecosystem: "'Drupal'"
      status:
        source_field: "status"
        transform: |
          case(status == 1, 'active', status == 0, 'archived', 'unknown')
      created_at: "created"
      updated_at: "changed"
    
    relationships:
      - relation_type: "part_of"
        target_entity: "project"
        source_field: "parent_nid"
        confidence: 1.0

id_strategy:
  actor: "user.uid"
  project: "node.nid"
  issue: "issue.iid"

stitching_rules:
  - name: "email_exact_match"
    entity_type: "actor"
    match_fields:
      - "email"
    confidence: 1.0
    cross_source: true
  
  - name: "name_domain_match"
    entity_type: "actor"
    match_fields:
      - "name"
      - "email_domain"
    confidence: 0.7
    cross_source: false

field_transformations:
  created_at:
    expression: "timestamp_to_iso8601(created_at)"
  
  updated_at:
    expression: "timestamp_to_iso8601(updated_at)"
  
  email:
    expression: "lower(trim(email))"
    required: false
    default: null

constants:
  source_family: "drupalorg"
  source_name: "drupal.org community"
```

## Top-Level Fields

### version

**Type**: string (semantic version)  
**Required**: yes  
**Description**: Version of this mapping pack

### source_family

**Type**: string  
**Required**: yes  
**Description**: Which source family this maps (must match source config)

**Example**: `"drupalorg"`

### description

**Type**: string  
**Required**: no  
**Description**: Human-readable description

## entity_mappings

**Type**: object  
**Required**: yes  
**Description**: Mapping rules for each canonical entity type

Each key is a canonical entity type: `actor`, `project`, `issue`, `event`, `contribution`

### Entity Mapping Fields

#### source_entity_name

**Type**: string  
**Required**: yes  
**Description**: Name of the entity type in the source system

**Examples**: `"user"` (Drupal), `"post"` (WordPress), `"user"` (GitHub)

#### identity

**Type**: object  
**Required**: yes  
**Description**: How to compute the canonical_id

**Fields**:
- `template`: String template for ID generation
- `fields`: Array of source fields used in template

**Template syntax**: `{field_name}` or literals

**Examples**:
```yaml
identity:
  template: "actor:{source_family}:{source_name}:{uid}"
  fields: [uid]
```

Results in: `actor:drupalorg:drupalorg:12345`

#### field_map

**Type**: object  
**Required**: yes  
**Description**: Maps canonical fields to source fields

Each key is a canonical field name; value can be:
- **String**: Source field path (dot-notation for nested)
- **Object**: Complex transformation

**String examples**:
```yaml
field_map:
  display_name: "name"
  email: "mail"
  created_at: "created"
```

**Object examples**:
```yaml
field_map:
  roles:
    source_field: "roles"
    transform: "split_comma"
  
  status:
    source_field: "status_code"
    transform: |
      case(status_code == 1, 'active', status_code == 0, 'archived', 'unknown')
  
  primary_locale:
    source_field: null
    default: "en"
```

#### relationships

**Type**: array of objects  
**Required**: no  
**Description**: Relationships to extract from this entity type

Each relationship specifies:
- `relation_type`: Type of relationship (must be valid from canonical-relations-v1.md)
- `target_entity`: Entity type of the target
- `source_field`: Field in source data containing target IDs
- `confidence`: Confidence score (0.0-1.0)

**Examples**:
```yaml
relationships:
  - relation_type: "maintains"
    target_entity: "project"
    source_field: "maintained_projects"
    confidence: 1.0
  
  - relation_type: "contributes_to"
    target_entity: "project"
    source_field: "contributed_projects"
    confidence: 0.8
```

#### conditional_mappings

**Type**: array of objects  
**Required**: no  
**Description**: Conditional field mappings based on entity content

Each conditional has:
- `condition`: Boolean expression to evaluate
- `field_map`: Field mappings if condition is true

**Examples**:
```yaml
conditional_mappings:
  - condition: "status == 'published'"
    field_map:
      state: "'open'"
      published: "true"
  
  - condition: "status == 'draft'"
    field_map:
      state: "'draft'"
  
  - condition: "created > '2025-01-01'"
    field_map:
      vintage: "'recent'"
```

## id_strategy

**Type**: object  
**Required**: no  
**Description**: Simplified ID generation expressions

Alternative to complex templates; provides shorthand:

```yaml
id_strategy:
  actor: "user.uid"  # Use user.uid field directly as the ID
  project: "node.nid"
```

## stitching_rules

**Type**: array of objects  
**Required**: no  
**Description**: Rules for identifying the same entity across sources

Each rule specifies:
- `name`: Descriptive name for the rule
- `entity_type`: Which entity type this applies to
- `match_fields`: Which fields must match for stitching
- `confidence`: Confidence score (0.0-1.0)
- `cross_source`: Whether to allow cross-source stitching

**Examples**:
```yaml
stitching_rules:
  - name: "email_exact_match"
    entity_type: "actor"
    match_fields: [email]
    confidence: 1.0
    cross_source: true
  
  - name: "name_domain_match"
    entity_type: "actor"
    match_fields: [name, email_domain]
    confidence: 0.7
    cross_source: false
  
  - name: "project_name_match"
    entity_type: "project"
    match_fields: [name, ecosystem]
    confidence: 0.5
    cross_source: false  # Don't stitch projects across ecosystems
```

## field_transformations

**Type**: object  
**Required**: no  
**Description**: Custom transformations for specific fields

Each key is a field name; value specifies:
- `expression`: Transformation expression (see below)
- `required`: Whether field is required (default: false)
- `default`: Default value if source field is missing

**Examples**:
```yaml
field_transformations:
  created_at:
    expression: "timestamp_to_iso8601(created_at)"
    required: true
  
  email:
    expression: "lower(trim(email))"
    required: false
    default: null
  
  roles:
    expression: "split_comma(roles)"
    required: false
    default: []
```

### Transformation Expressions

#### Built-in Functions

| Function                                  | Description            | Example                                        |
| ----------------------------------------- | ---------------------- | ---------------------------------------------- |
| `lower(s)`                                | Lowercase string       | `lower('HELLO')` → `'hello'`                   |
| `upper(s)`                                | Uppercase string       | `upper('hello')` → `'HELLO'`                   |
| `trim(s)`                                 | Remove whitespace      | `trim(' hello ')` → `'hello'`                  |
| `split(s, delim)`                         | Split string           | `split('a,b,c', ',')` → `['a', 'b', 'c']`      |
| `join(arr, delim)`                        | Join array             | `join(['a', 'b'], ',')` → `'a,b'`              |
| `case(cond1, val1, cond2, val2, default)` | Conditional            | `case(x==1, 'one', 'other')`                   |
| `timestamp_to_iso8601(ts)`                | Convert timestamp      | `timestamp_to_iso8601(1234567890)`             |
| `iso8601_to_timestamp(iso)`               | Convert ISO date       | `iso8601_to_timestamp('2025-05-02T08:00:00Z')` |
| `length(s)`                               | String or array length | `length('hello')` → 5                          |
| `contains(s, substr)`                     | Substring check        | `contains('hello', 'ell')` → true              |
| `replace(s, old, new)`                    | String replace         | `replace('hello', 'l', 'L')` → `'heLLo'`       |
| `map_dict(d, keys)`                       | Extract dict keys      | `map_dict(data, ['name', 'email'])`            |

#### Expression Syntax

- **Field references**: `{field_name}` or `field_name`
- **Nested references**: `{user.name}` or `user.name` (dot notation)
- **String literals**: `'string'`
- **Number literals**: `42`, `3.14`
- **Arrays**: `[1, 2, 3]`
- **Objects**: Not supported in expressions
- **Operators**: `==`, `!=`, `>`, `<`, `>=`, `<=`, `and`, `or`, `not`

**Examples**:
```yaml
# If/then
"case(status == 'published', 'open', 'closed')"

# Function call
"timestamp_to_iso8601(created_at)"

# Chaining
"lower(trim(email))"

# Conditional field reference
"case(hasProperty(user, 'email'), user.email, null)"
```

## constants

**Type**: object  
**Required**: no  
**Description**: Constant values injected into all mapped entities

**Examples**:
```yaml
constants:
  source_family: "drupalorg"
  source_name: "drupal.org community"
```

These values are available in field mappings as: `"{constants.source_family}"`

## Validation Rules

Framework validates mapping packs:

1. **Schema validation**: Must match `mapping-pack.schema.json`
2. **Entity types valid**: All entity types must be from canonical-entities-v1.md
3. **Field names valid**: All canonical field names must be valid
4. **Relation types valid**: All relation_type values must be valid
5. **Expressions valid**: All expressions must parse without errors
6. **No circular references**: Expressions cannot reference fields being defined
7. **Stitching confidence**: Values must be 0.0-1.0

## Example: WordPress Plugin Mapping

```yaml
version: "1.0.0"
source_family: "wordpressorg"
description: "Default mapping for WordPress.org plugins"

entity_mappings:
  project:
    source_entity_name: "plugin"
    
    identity:
      template: "project:{source_family}:{source_name}:{slug}"
      fields: [slug]
    
    field_map:
      name: "name"
      description: "description"
      ecosystem: "'WordPress'"
      status: "'active'"
      created_at: "added"
      updated_at: "last_updated"
    
    relationships:
      - relation_type: "depends_on"
        target_entity: "project"
        source_field: "requires_plugins"
        confidence: 1.0

constants:
  source_family: "wordpressorg"
  source_name: "wordpress.org plugins"
```

## Versioning & Deprecation

- **v1.0.0** (current): Mapping structure as defined above
- **Future enhancements** (→ v1.x.0):
  - More built-in transformation functions
  - Template inheritance (extends field)
  - Reusable transformation libraries
- **Breaking changes** (→ v2.0.0):
  - Changes to template syntax
  - Changes to expression language
  - Removal of field_map format
