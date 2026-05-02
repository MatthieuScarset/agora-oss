# Source Config Schema v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Data Connector  

## Overview

Source configurations define how Agora connects to and ingests data from a specific source. Configuration is declarative (YAML/JSON) and contains no code, enabling operators to add new sources without developer involvement.

Every source config is validated against the JSON Schema defined in `configs/schemas/source-config.schema.json` before use.

## Configuration Structure

```yaml
# configs/sources/drupalorg/community-default.yaml

name: "drupal.org community"
source_family: "drupalorg"

connector:
  plugin_name: "drupalorg"
  plugin_version: "1.0.0"
  capabilities:
    - "discover_capabilities"
    - "fetch_full"
    - "fetch_incremental"
    - "emit_raw_envelope"
    - "map_to_canonical"
    - "report_health"

endpoints:
  - url: "https://www.drupal.org/api-d7/node.json"
    entity_type: "project"
    method: "GET"
    pagination:
      strategy: "offset"
      page_size: 100
    rate_limit:
      requests_per_second: 5
      burst_size: 20
  
  - url: "https://www.drupal.org/api-d7/user.json"
    entity_type: "actor"
    method: "GET"
    pagination:
      strategy: "offset"
      page_size: 100

authentication:
  type: "none"

refresh_policy:
  interval: "0 */6 * * *"  # Every 6 hours
  strategy: "incremental"
  timeout_seconds: 3600

quality_policy: "quality-policy.yaml"
mapping_pack: "drupalorg/default.mapping.yaml"

locales:
  - "en"

primary_locale: "en"

metadata:
  ecosystem: "Drupal"
  maintainer: "Drupal Community"
  contact: "security@drupal.org"
  tags:
    - "drupal-ecosystem"
    - "modules"
    - "themes"

enabled: true
```

## Configuration Fields

### name

**Type**: string  
**Required**: yes  
**Description**: Human-readable name for this source instance

**Example**: `"drupal.org community"`

### source_family

**Type**: string (enum)  
**Required**: yes  
**Description**: Which ecosystem this source belongs to  
**Allowed values**: `drupalorg`, `wordpressorg`, `github`, `gitlab`, `custom`

**Example**: `"drupalorg"`

### connector

**Type**: object  
**Required**: yes  
**Description**: Plugin/connector configuration

#### connector.plugin_name

**Type**: string  
**Required**: yes  
**Description**: Name of the plugin module (must match directory in `plugins/`)

**Example**: `"drupalorg"`

#### connector.plugin_version

**Type**: string (semantic version)  
**Required**: yes  
**Description**: Version constraint for the plugin (semver)

**Examples**: `"1.0.0"`, `"^1.0.0"`, `"~1.2"` (npm-style)

#### connector.capabilities

**Type**: array of strings  
**Required**: no  
**Description**: Explicitly request specific capabilities (optional; plugin declares all by default)

**Values**: Must be subset of plugin's `discover_capabilities()` response

### endpoints

**Type**: array of objects  
**Required**: yes  
**Description**: API endpoints or data sources to ingest

Each endpoint defines:

#### url

**Type**: string (URI)  
**Required**: yes  
**Description**: API endpoint or data source URI

**Examples**:
- `"https://www.drupal.org/api-d7/node.json"`
- `"file:///data/export.json"`
- `"s3://bucket/path/"`

#### entity_type

**Type**: string (enum)  
**Required**: yes  
**Description**: Which canonical entity type this endpoint provides  
**Allowed values**: `actor`, `project`, `issue`, `event`, `contribution`

#### method

**Type**: string (enum)  
**Required**: no  
**Default**: `"GET"`  
**Description**: HTTP method  
**Allowed values**: `GET`, `POST`

#### pagination

**Type**: object  
**Required**: no  
**Description**: How to paginate through results

**Fields**:
- `strategy`: `offset`, `cursor`, `page`, or `none`
- `page_size`: integer (1-10000)

**Example**:
```yaml
pagination:
  strategy: "offset"
  page_size: 100
```

#### rate_limit

**Type**: object  
**Required**: no  
**Description**: Rate limiting for this endpoint

**Fields**:
- `requests_per_second`: number (e.g., 5.0)
- `burst_size`: integer (e.g., 20)

**Example**:
```yaml
rate_limit:
  requests_per_second: 10
  burst_size: 50
```

### authentication

**Type**: object  
**Required**: no  
**Description**: Authentication method

#### authentication.type

**Type**: string (enum)  
**Allowed values**: `none`, `api_key`, `oauth2`, `basic`, `custom`

#### authentication.credentials_ref

**Type**: string  
**Description**: Reference to secrets store (not stored in config)

**Format**: `env:VARIABLE_NAME` or `secrets://path/to/secret`

**Examples**:
```yaml
authentication:
  type: "api_key"
  credentials_ref: "env:DRUPAL_API_KEY"
```

```yaml
authentication:
  type: "basic"
  credentials_ref: "secrets://drupal/basic_auth"
```

**Security Note**: Credentials are never stored in config files. They are resolved from environment variables or secret management systems at runtime.

### refresh_policy

**Type**: object  
**Required**: no  
**Description**: Schedule and strategy for data refresh

#### refresh_policy.interval

**Type**: string  
**Description**: When to refresh (Cron expression or ISO 8601 duration)

**Examples**:
- `"0 */6 * * *"` (cron: every 6 hours)
- `"PT6H"` (ISO 8601: every 6 hours)
- `"0 2 * * *"` (cron: daily at 2 AM)

#### refresh_policy.strategy

**Type**: string (enum)  
**Allowed values**: `full`, `incremental`, `adaptive`

- `full`: Re-fetch all data every time
- `incremental`: Fetch only changes since last run
- `adaptive`: Choose based on source behavior

#### refresh_policy.timeout_seconds

**Type**: integer  
**Default**: 3600  
**Description**: Maximum time (seconds) for a single refresh run

### quality_policy

**Type**: string (file reference)  
**Required**: no  
**Default**: `"quality-policy.yaml"`  
**Description**: Reference to quality policy file

**Example**: `"quality-policy.yaml"`

### mapping_pack

**Type**: string (file reference)  
**Required**: yes  
**Description**: Reference to mapping rules file

**Example**: `"drupalorg/default.mapping.yaml"`

See [mapping-rules-v1.md](mapping-rules-v1.md) for structure.

### locales

**Type**: array of strings (BCP 47 codes)  
**Required**: no  
**Default**: `["en"]`  
**Description**: Locales supported by this source

**Examples**: `["en", "es", "fr"]`

### primary_locale

**Type**: string (BCP 47 code)  
**Required**: no  
**Default**: `"en"`  
**Description**: Default locale if not specified

Must be in `locales` array.

### metadata

**Type**: object  
**Required**: no  
**Description**: Additional metadata for operators

**Suggested fields**:
- `ecosystem`: Name of the ecosystem (e.g., "Drupal", "WordPress")
- `maintainer`: Who maintains this source integration
- `contact`: Email or URL for issues/questions
- `tags`: Array of descriptive tags

**Example**:
```yaml
metadata:
  ecosystem: "Drupal"
  maintainer: "Drupal Community"
  contact: "security@drupal.org"
  tags:
    - "drupal-ecosystem"
    - "modules"
    - "themes"
```

### enabled

**Type**: boolean  
**Default**: `true`  
**Description**: Whether this source is active

**Example**: `enabled: false` to temporarily disable

## Example Configurations

### Minimal Configuration

```yaml
name: "github-example"
source_family: "github"
connector:
  plugin_name: "github"
  plugin_version: "1.0.0"
endpoints:
  - url: "https://api.github.com/repos/django/django"
    entity_type: "project"
mapping_pack: "github/default.mapping.yaml"
```

### Full-Featured Configuration

```yaml
name: "wordpress.org plugins"
source_family: "wordpressorg"

connector:
  plugin_name: "wordpress"
  plugin_version: "1.0.0"

endpoints:
  - url: "https://api.wordpress.org/plugins/info/1.0/"
    entity_type: "project"
    pagination:
      strategy: "page"
      page_size: 100
    rate_limit:
      requests_per_second: 2

authentication:
  type: "none"

refresh_policy:
  interval: "0 0 * * 0"  # Weekly, Sundays at midnight
  strategy: "incremental"
  timeout_seconds: 7200

quality_policy: "wordpress-quality-policy.yaml"
mapping_pack: "wordpressorg/default.mapping.yaml"

locales:
  - "en"
  - "es"
  - "fr"

primary_locale: "en"

metadata:
  ecosystem: "WordPress"
  maintainer: "WordPress Contributors"
  contact: "dev@wordpress.org"
  tags:
    - "wordpress"
    - "plugins"

enabled: true
```

## Validation Rules

Framework validates all source configs:

1. **Schema validation**: Config must match `source-config.schema.json`
2. **Required fields**: `name`, `source_family`, `connector`, `endpoints`, `mapping_pack`
3. **Plugin exists**: Plugin directory `plugins/{plugin_name}/` must exist
4. **Plugin version**: Installed plugin version must satisfy the version constraint
5. **Endpoints not empty**: At least one endpoint must be defined
6. **Entity types valid**: All entity_types must be from canonical-entities-v1.md
7. **Locales valid**: All locales must be valid BCP 47 codes
8. **File references exist**: `mapping_pack` and `quality_policy` files must exist
9. **No sensitive data**: Config must not contain passwords, API keys, or other secrets

## File Organization

Configs are organized by source family:

```
configs/
  schemas/
    source-config.schema.json
    mapping-pack.schema.json
  sources/
    drupalorg/
      community-default.yaml       # Default configuration
      enterprise-custom.yaml       # Alternative configuration
    wordpressorg/
      wordpress-default.yaml
    github/
      open-source.yaml
  mappings/
    drupalorg/
      default.mapping.yaml
    wordpressorg/
      default.mapping.yaml
  policies/
    quality-policy.yaml
```

## Configuration Hot-Reloading

When a config file is updated:

1. Framework detects change (file watcher)
2. Validates new config against schema
3. If valid, updates plugin configuration (calls `initialize()` again)
4. If invalid, logs error and continues using old config

This enables operators to tune refresh intervals, rate limits, or mappings without restarting services.

## Secrets Management

Credentials are resolved at runtime:

1. Check environment variables (e.g., `env:DRUPAL_API_KEY` → `$DRUPAL_API_KEY`)
2. Check secrets management system (e.g., `secrets://drupal/api_key`)
3. Fail with clear error if not found

Example with environment variable:
```bash
export DRUPAL_API_KEY="secret123"
export WORDPRESS_BASIC_AUTH="user:pass"

# Framework resolves at runtime
credentials_ref: "env:DRUPAL_API_KEY"
```

## Versioning & Deprecation

- **v1.0.0** (current): Schema as defined above
- **Future enhancements** (→ v1.x.0):
  - Webhook-based ingestion (future extension)
  - Template inheritance (e.g., `extends: "base.yaml"`)
  - Variable interpolation (e.g., `${ENV_VAR}`)
- **Breaking changes** (→ v2.0.0):
  - Changes to required fields
  - Changes to endpoint structure
