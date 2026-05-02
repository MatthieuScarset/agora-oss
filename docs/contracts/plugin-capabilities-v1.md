# Plugin Capabilities v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Data Connector  

## Overview

Capabilities define what a plugin is able and willing to do. The `discover_capabilities()` method returns a capability manifest that the framework uses to:

- Decide which entity types to request from the plugin
- Set rate limits and batch sizes
- Determine if incremental fetch is supported
- Validate configuration before initialization

## Capability Manifest

The standard return from `discover_capabilities()`:

```python
{
    # Core capabilities (required)
    "capabilities": [
        "discover_capabilities",
        "fetch_full",
        "fetch_incremental",
        "emit_raw_envelope",
        "map_to_canonical",
        "report_health"
    ],
    
    # Entity support (required)
    "entity_types": ["actor", "project", "issue"],  # Which types this plugin provides
    
    # Fetch strategy (required)
    "supports_incremental": True,
    "incremental_cursor_types": ["timestamp", "offset"],  # How to track position
    
    # Data relationships (required)
    "supports_relationships": True,
    "relationship_types": ["maintains", "contributes_to", "depends_on"],
    
    # Locale support (required)
    "supported_locales": ["en", "es"],
    "default_locale": "en",
    "translation_coverage": {  # Optional: indicate i18n support
        "en": 1.0,  # 100% coverage
        "es": 0.8   # 80% coverage
    },
    
    # Configuration requirements (required)
    "required_config_fields": ["api_key", "base_url"],
    "optional_config_fields": ["proxy_url", "timeout"],
    
    # Performance characteristics (optional)
    "max_batch_size": 100,
    "rate_limit": {
        "requests_per_second": 10,
        "burst_size": 50
    },
    "estimated_full_fetch_time_seconds": 3600,  # Rough estimate for all data
    
    # Source-specific metadata (optional)
    "source_family": "drupalorg",
    "source_version_supported": "10.x",  # e.g., Drupal version
    "connector_version": "1.0.0",
    
    # Feature flags (optional)
    "features": {
        "full_text_search": True,
        "entity_linking": True,
        "multi_language": True,
        "webhook_ingestion": False  # Future extension
    }
}
```

## Entity Type Support

Plugins declare which canonical entity types they provide:

```python
{
    "entity_types": ["actor", "project", "issue", "event", "contribution"]
}
```

**Allowed values**: Any of [actor, project, issue, event, contribution]

**Validation**: Framework validates that the plugin can actually map these entity types via `map_to_canonical()`.

## Incremental Fetch Support

If `supports_incremental: true`, the plugin declares cursor types:

```python
{
    "supports_incremental": True,
    "incremental_cursor_types": ["timestamp"],  # How we track progress
}
```

### Cursor Types

| Type        | Description               | Example                       |
| ----------- | ------------------------- | ----------------------------- |
| `timestamp` | Last modified timestamp   | `"2025-11-28T16:45:00Z"`      |
| `offset`    | Record offset/position    | `{"page": 3, "offset": 200}`  |
| `id`        | Last processed entity ID  | `{"last_id": 12345}`          |
| `token`     | Opaque cursor from source | `{"next_token": "abc123xyz"}` |

Plugins may support multiple cursor types; framework chooses based on source efficiency.

## Relationship Support

If `supports_relationships: true`, plugin declares which relation types it can extract:

```python
{
    "supports_relationships": True,
    "relationship_types": [
        "maintains",
        "contributes_to",
        "depends_on",
        "authored"
    ]
}
```

See [canonical-relations-v1.md](canonical-relations-v1.md) for the full list of allowed types.

## Locale & i18n Support

Every plugin declares its locale support:

```python
{
    "supported_locales": ["en", "es", "fr"],
    "default_locale": "en",
    "translation_coverage": {
        "en": 1.0,  # All data available in English
        "es": 0.5   # ~50% of data translated to Spanish
    }
}
```

**Validation**: 
- All locales must be valid BCP 47 codes (e.g., "en", "en-US", "pt-BR")
- `default_locale` must be in `supported_locales`
- `translation_coverage` scores must be 0.0-1.0

If a locale is not 100% covered, framework falls back to `default_locale`.

## Configuration Requirements

Plugins declare required and optional config fields:

```python
{
    "required_config_fields": ["api_key", "base_url"],
    "optional_config_fields": ["proxy_url", "connection_timeout", "retry_attempts"],
    "config_schema": {...}  # Optional: JSON Schema for full validation
}
```

Framework validates source config against these fields before calling `initialize()`.

**Example valid config**:
```yaml
name: drupal.org community
source_family: drupalorg
connector:
  plugin_name: drupalorg
  plugin_version: 1.0.0
endpoints:
  - url: https://www.drupal.org/api-d7/node.json
    entity_type: project
authentication:
  type: none
```

## Performance Characteristics

Plugins may declare performance hints:

```python
{
    "max_batch_size": 100,  # Max records per API call
    "rate_limit": {
        "requests_per_second": 10,
        "burst_size": 50
    },
    "estimated_full_fetch_time_seconds": 3600
}
```

Framework uses these to:
- Batch records for processing
- Throttle requests to avoid rate limits
- Estimate total ingestion time
- Alert if fetch takes much longer than expected

## Feature Flags

Optional feature support:

```python
{
    "features": {
        "full_text_search": True,
        "entity_linking": True,
        "multi_language": True,
        "incremental_updates": True,
        "webhook_ingestion": False,
        "custom_queries": False
    }
}
```

These are informational; framework may use them to enable/disable UI features or API endpoints.

## Source Version Compatibility

If the plugin targets a specific version of the source:

```python
{
    "source_family": "drupalorg",
    "source_version_supported": "10.x",  # Drupal 10.0-10.999
    "connector_version": "1.0.0"
}
```

Useful for operators to know which source versions are compatible.

## Error Handling Capabilities

Plugins may declare error handling strategies:

```python
{
    "error_handling": {
        "supports_partial_failures": True,  # Can continue on some errors
        "supports_retry": True,
        "max_retries": 3,
        "retry_backoff": "exponential"  # exponential, linear, fixed
    }
}
```

## Validation Rules

Framework validates capability manifest:

1. **Required fields**: `capabilities`, `entity_types`, `supports_incremental`, `supports_relationships`, `supported_locales`, `default_locale`, `required_config_fields`
2. **Type consistency**: All fields must match expected types (strings, arrays, numbers, etc.)
3. **No contradictions**: If `supports_incremental: false`, cursor types may not be provided
4. **Entity type validation**: All declared entity_types must be valid (from canonical-entities-v1.md)
5. **Relation type validation**: All declared relationship_types must be valid (from canonical-relations-v1.md)
6. **Locale validation**: All locales must be valid BCP 47 codes

If manifest is invalid, framework logs an error and does not load the plugin.

## Runtime Capability Caching

Framework caches the capability manifest:

- Plugins must not change capabilities between `initialize()` and `shutdown()`
- If capabilities are truly dynamic (rare), plugin can override cache behavior
- Capability queries are cached for 24 hours by default

## Example: Drupal.org Plugin Capabilities

```python
async def discover_capabilities(self):
    return {
        "capabilities": [
            "discover_capabilities",
            "fetch_full",
            "fetch_incremental",
            "emit_raw_envelope",
            "map_to_canonical",
            "report_health"
        ],
        "entity_types": ["actor", "project", "issue", "contribution", "event"],
        "supports_incremental": True,
        "incremental_cursor_types": ["timestamp"],
        "supports_relationships": True,
        "relationship_types": [
            "maintains",
            "contributes_to",
            "reported",
            "assigned_to",
            "participated_in"
        ],
        "supported_locales": ["en"],
        "default_locale": "en",
        "required_config_fields": ["base_url"],
        "optional_config_fields": [],
        "max_batch_size": 100,
        "rate_limit": {
            "requests_per_second": 5,
            "burst_size": 20
        },
        "estimated_full_fetch_time_seconds": 7200,
        "features": {
            "full_text_search": False,
            "entity_linking": True,
            "multi_language": False,
            "incremental_updates": True,
            "webhook_ingestion": False
        },
        "source_family": "drupalorg",
        "connector_version": "1.0.0"
    }
```

## Versioning & Deprecation

- **v1.0.0** (current): Manifest structure as above
- **Future enhancements** (→ v1.x.0):
  - Streaming/partial capability updates
  - Conditional capabilities (e.g., "supports X only if Y is configured")
  - Capability usage statistics
- **Breaking changes** (→ v2.0.0):
  - Changes to manifest structure
  - Removal/renaming of standard capability fields
