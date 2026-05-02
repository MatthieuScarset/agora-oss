# Plugin Error Model v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Data Connector  

## Overview

Plugins signal errors via structured exception types. Framework catches these exceptions, logs them with context, and decides whether to retry, quarantine, or propagate the error.

## Exception Hierarchy

```
PluginError (base)
├── ConfigError
├── AuthError
├── FetchError
│   ├── NetworkError
│   ├── TimeoutError
│   └── RateLimitError
├── TransformError
├── MappingError
└── HealthError
```

All plugin exceptions inherit from `PluginError` and include:
- `error_code`: Machine-readable code (e.g., "AUTH_INVALID_CREDENTIALS")
- `message`: Human-readable message
- `details`: Optional dict with additional context
- `retryable`: Boolean indicating if framework should retry
- `timestamp`: When the error occurred

## Exception Types

### ConfigError

Configuration is invalid, incomplete, or unrecognized.

```python
raise ConfigError(
    error_code="CONFIG_MISSING_REQUIRED_FIELD",
    message="Missing required config field: api_key",
    details={"required_fields": ["api_key", "base_url"]},
    retryable=False
)
```

**Error Codes**:
- `CONFIG_MISSING_REQUIRED_FIELD`
- `CONFIG_INVALID_VALUE`
- `CONFIG_SCHEMA_VALIDATION_FAILED`
- `CONFIG_INCOMPATIBLE_OPTIONS`

**Retryable**: No (indicates operator error; requires manual intervention)

**Framework Action**: Log error, don't load plugin, alert operator

### AuthError

Authentication or authorization failed.

```python
raise AuthError(
    error_code="AUTH_INVALID_CREDENTIALS",
    message="API key is invalid or expired",
    details={"key_age_days": 90},
    retryable=True
)
```

**Error Codes**:
- `AUTH_INVALID_CREDENTIALS`
- `AUTH_EXPIRED_TOKEN`
- `AUTH_INSUFFICIENT_PERMISSIONS`
- `AUTH_CERTIFICATE_ERROR`

**Retryable**: Yes (may be transient; credentials may be rotated)

**Framework Action**: Retry with exponential backoff; after N failures, quarantine source

### FetchError

Data fetch failed (network issue, timeout, API error, etc.).

```python
raise FetchError(
    error_code="FETCH_HTTP_ERROR",
    message="HTTP 503 Service Unavailable",
    details={"status_code": 503, "endpoint": "/api/v2/users"},
    retryable=True
)
```

#### NetworkError (subtype)

```python
raise FetchError(
    error_code="FETCH_CONNECTION_REFUSED",
    message="Connection refused at 203.0.113.42:443",
    details={"host": "api.drupal.org", "port": 443},
    retryable=True
)
```

#### TimeoutError (subtype)

```python
raise FetchError(
    error_code="FETCH_TIMEOUT",
    message="Request timed out after 30 seconds",
    details={"timeout_seconds": 30, "endpoint": "/api/v2/projects"},
    retryable=True
)
```

#### RateLimitError (subtype)

```python
raise FetchError(
    error_code="FETCH_RATE_LIMITED",
    message="Rate limit exceeded: 100 requests per minute",
    details={
        "limit": 100,
        "window_seconds": 60,
        "retry_after_seconds": 45
    },
    retryable=True
)
```

**Error Codes**:
- `FETCH_CONNECTION_ERROR`
- `FETCH_TIMEOUT`
- `FETCH_RATE_LIMITED`
- `FETCH_HTTP_ERROR` (for 4xx, 5xx)
- `FETCH_INVALID_RESPONSE` (unparseable JSON, etc.)

**Retryable**: Yes (transient infrastructure issues)

**Framework Action**: Retry with exponential backoff; respect `retry_after_seconds` for rate limits

### TransformError

Raw source data cannot be transformed into a RawEnvelope.

```python
raise TransformError(
    error_code="TRANSFORM_INVALID_PAYLOAD",
    message="Source payload missing required 'id' field",
    details={"payload": {...}, "missing_fields": ["id"]},
    retryable=False
)
```

**Error Codes**:
- `TRANSFORM_INVALID_PAYLOAD`
- `TRANSFORM_MISSING_REQUIRED_FIELD`
- `TRANSFORM_SCHEMA_VALIDATION_FAILED`
- `TRANSFORM_TYPE_MISMATCH`

**Retryable**: No (indicates data quality issue in source)

**Framework Action**: Log error, quarantine record, continue fetching remaining records

### MappingError

Envelope cannot be mapped to a canonical entity.

```python
raise MappingError(
    error_code="MAPPING_SCHEMA_MISMATCH",
    message="Mapped value for 'created_at' is not ISO 8601 date",
    details={"field": "created_at", "value": "2025-13-45", "expected_format": "ISO 8601"},
    retryable=False
)
```

**Error Codes**:
- `MAPPING_SCHEMA_MISMATCH`
- `MAPPING_MISSING_REQUIRED_FIELD`
- `MAPPING_TYPE_CONVERSION_FAILED`
- `MAPPING_CIRCULAR_REFERENCE`

**Retryable**: No (indicates mapping rule error)

**Framework Action**: Log error, quarantine record, alert operator to fix mapping

### HealthError

Plugin health check failed.

```python
raise HealthError(
    error_code="HEALTH_API_DEGRADED",
    message="Source API responding slowly (avg response time: 5s)",
    details={"avg_response_time_ms": 5000, "error_rate_percent": 2.5},
    retryable=True
)
```

**Error Codes**:
- `HEALTH_API_UNREACHABLE`
- `HEALTH_API_DEGRADED`
- `HEALTH_AUTHENTICATION_FAILING`
- `HEALTH_DATABASE_ERROR`

**Retryable**: Yes (monitoring and alerting, not ingestion blocking)

**Framework Action**: Alert operator, but continue ingestion (downgrade data freshness score)

## Exception Structure

All exceptions inherit from `PluginError`:

```python
class PluginError(Exception):
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
        timestamp: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.retryable = retryable
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
            "timestamp": self.timestamp
        }
```

## Retry Strategy

Framework implements exponential backoff with jitter:

```python
max_retries = 3
initial_delay_seconds = 1

for attempt in range(max_retries):
    try:
        result = await plugin.fetch_full(entity_type)
        break
    except PluginError as e:
        if not e.retryable:
            raise
        
        if "retry_after_seconds" in e.details:
            delay = e.details["retry_after_seconds"]
        else:
            delay = initial_delay_seconds * (2 ** attempt) + random.uniform(0, 1)
        
        await asyncio.sleep(delay)
        continue
    except Exception as e:
        # Unexpected exception; don't retry
        raise
```

## Quarantine & Manual Review

When a plugin or data source encounters repeated errors:

1. **After 3 consecutive FetchErrors**: Source marked as `status: degraded`
2. **After 10 consecutive errors**: Source marked as `status: error`, ingestion paused
3. **Manual review required**: Operator must investigate and update config or source status

Error logs include:
- Full exception traceback
- Plugin name and version
- Source config used
- Last successful ingestion timestamp
- Suggested next steps

Example error log:
```json
{
    "level": "ERROR",
    "timestamp": "2026-05-02T08:30:00Z",
    "plugin": "drupalorg:1.0.0",
    "source_family": "drupalorg",
    "entity_type": "actor",
    "error_code": "FETCH_RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retryable": true,
    "retry_count": 2,
    "next_retry_seconds": 45,
    "details": {
        "limit": 100,
        "window_seconds": 60,
        "retry_after_seconds": 45
    }
}
```

## Error Metrics & Monitoring

Framework tracks error metrics per plugin:

```python
{
    "plugin": "drupalorg:1.0.0",
    "time_window": "24h",
    "errors_by_code": {
        "FETCH_RATE_LIMITED": 12,
        "FETCH_TIMEOUT": 3,
        "TRANSFORM_INVALID_PAYLOAD": 5
    },
    "retryable_errors": 15,
    "non_retryable_errors": 5,
    "error_rate_percent": 0.2  # Of all fetches
}
```

Alerts triggered if:
- Error rate > 5% in 1 hour
- Consecutive non-retryable errors > 10
- Health check fails 3 times in a row

## Testing Error Scenarios

Plugins must test error handling:

```python
# test_connector.py

async def test_auth_error():
    plugin = Connector()
    with pytest.raises(AuthError) as exc_info:
        await plugin.initialize({"api_key": "invalid"})
    
    assert exc_info.value.error_code == "AUTH_INVALID_CREDENTIALS"
    assert not exc_info.value.retryable

async def test_fetch_timeout():
    plugin = Connector()
    await plugin.initialize(config)
    
    with pytest.raises(FetchError) as exc_info:
        # Mock slow response
        await plugin.fetch_full("actor")
    
    assert exc_info.value.error_code == "FETCH_TIMEOUT"
    assert exc_info.value.retryable
```

## Versioning & Deprecation

- **v1.0.0** (current): Exception hierarchy and error codes above
- **Future enhancements** (→ v1.x.0):
  - Custom error codes per plugin (with registry)
  - Error categorization (data quality vs. infrastructure)
  - Machine-learning based error prediction and recovery
- **Breaking changes** (→ v2.0.0):
  - Changes to exception hierarchy
  - Removal/renaming of standard error codes
