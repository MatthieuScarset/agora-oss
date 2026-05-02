# Plugin Health & Observability v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Data Connector  

## Overview

Plugins emit observability signals (metrics, logs, traces) that enable operators to understand system health, debug issues, and optimize performance. This contract defines the standard formats and expectations.

## Health Reporting

Plugins implement `report_health()` to communicate current status:

```python
async def report_health(self) -> Dict[str, Any]:
    return {
        "status": "healthy",  # healthy, degraded, error
        "last_check_timestamp": "2026-05-02T08:15:00Z",
        "messages": [
            "API responding normally",
            "Last fetch completed successfully"
        ],
        "metrics": {
            "requests_today": 5000,
            "errors_today": 2,
            "uptime_percent": 99.98,
            "avg_response_time_ms": 250,
            "last_successful_fetch": "2026-05-02T08:00:00Z",
            "last_error": {
                "error_code": "FETCH_TIMEOUT",
                "timestamp": "2026-05-01T23:30:00Z"
            }
        }
    }
```

### Health Status Levels

| Status     | Meaning                                                    | Action                                                   |
| ---------- | ---------------------------------------------------------- | -------------------------------------------------------- |
| `healthy`  | Operating normally; all checks pass                        | Continue ingestion normally                              |
| `degraded` | Operating with issues; reduced performance or data quality | Continue ingestion but monitor; alert operator           |
| `error`    | Serious problems; source may be unreliable                 | Pause ingestion; require manual review before continuing |

### Required Metrics

Every plugin must report:

| Metric                  | Type              | Description                              |
| ----------------------- | ----------------- | ---------------------------------------- |
| `requests_today`        | int               | Total requests to source API in last 24h |
| `errors_today`          | int               | Total errors in last 24h                 |
| `uptime_percent`        | float (0.0-100.0) | Estimated source availability            |
| `avg_response_time_ms`  | int               | Average response time in milliseconds    |
| `last_successful_fetch` | ISO 8601 string   | Timestamp of last successful fetch       |

### Optional Metrics

```python
{
    "cache_hit_rate": 0.75,  # If plugin caches data
    "data_freshness_hours": 2.5,  # Time since last source update
    "pending_items_count": 145,  # Items waiting to be processed
    "estimated_full_sync_hours": 4.2,  # Rough time to fetch all data
    "source_version": "10.2.1",  # Source software version
}
```

## Structured Logging

Plugins use standard logging format:

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Log structured message
logger.info("Fetch started", extra={
    "plugin": "drupalorg",
    "entity_type": "actor",
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "batch_size": 100
})
```

### Log Levels

| Level    | Use Case                 | Example                                    |
| -------- | ------------------------ | ------------------------------------------ |
| DEBUG    | Detailed diagnostic info | "Fetching page 5 of 10"                    |
| INFO     | Normal operations        | "Ingestion completed: 5000 records"        |
| WARNING  | Unexpected conditions    | "Rate limit approaching (95/100 requests)" |
| ERROR    | Failed operations        | "HTTP 500 from API; retrying"              |
| CRITICAL | System-level failures    | "Auth failed; cannot proceed"              |

### Log Schema

All logs should include:

```json
{
    "timestamp": "2026-05-02T08:15:30.123Z",
    "level": "INFO",
    "logger": "plugins.drupalorg.connector",
    "message": "Fetch completed successfully",
    
    "trace_id": "abc123def456",  # For distributed tracing
    "span_id": "xyz789",
    
    "plugin": "drupalorg",
    "plugin_version": "1.0.0",
    "source_family": "drupalorg",
    "entity_type": "actor",
    
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "batch_id": "batch:001",
    
    "records_fetched": 5000,
    "records_failed": 2,
    "duration_seconds": 45.2,
    
    "error_code": null,
    "error_message": null
}
```

## Metrics & Monitoring

### Standard Prometheus Metrics

Plugins export metrics consumable by Prometheus:

```python
from prometheus_client import Counter, Histogram, Gauge

# Counter: total requests
fetch_requests_total = Counter(
    'connector_fetch_requests_total',
    'Total fetch requests',
    ['plugin', 'entity_type', 'status']
)

# Histogram: response time
fetch_duration_seconds = Histogram(
    'connector_fetch_duration_seconds',
    'Fetch duration in seconds',
    ['plugin', 'entity_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0)
)

# Gauge: current status
connector_health = Gauge(
    'connector_health',
    'Connector health status (1=healthy, 0.5=degraded, 0=error)',
    ['plugin']
)

# In plugin code:
fetch_requests_total.labels(
    plugin='drupalorg',
    entity_type='actor',
    status='success'
).inc()

with fetch_duration_seconds.labels(plugin='drupalorg', entity_type='actor').time():
    # Do fetch
    pass
```

### Recommended Metrics

Plugins should export:

| Metric                             | Type      | Labels                      | Example                |
| ---------------------------------- | --------- | --------------------------- | ---------------------- |
| `connector_fetch_requests_total`   | Counter   | plugin, entity_type, status | 5000 (status=success)  |
| `connector_fetch_duration_seconds` | Histogram | plugin, entity_type         | p50=0.25s, p99=2.0s    |
| `connector_fetch_errors_total`     | Counter   | plugin, error_code          | 2 (error_code=TIMEOUT) |
| `connector_health`                 | Gauge     | plugin                      | 1.0 (healthy)          |
| `connector_rate_limit_remaining`   | Gauge     | plugin                      | 45 (of 100/min)        |
| `connector_data_freshness_hours`   | Gauge     | plugin                      | 2.5                    |

## Distributed Tracing

Plugins participate in OpenTelemetry tracing:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def fetch_full(self, entity_type: str):
    with tracer.start_as_current_span(f"fetch_{entity_type}") as span:
        span.set_attribute("plugin", "drupalorg")
        span.set_attribute("entity_type", entity_type)
        span.set_attribute("ingestion_run_id", self.run_id)
        
        # Fetch implementation
        for page in fetch_pages():
            with tracer.start_as_current_span(f"fetch_page") as page_span:
                page_span.set_attribute("page", page.number)
                page_span.set_attribute("record_count", len(page.records))
                
                yield from page.records
```

Trace output includes:
- Operation name and duration
- Attributes (plugin, entity_type, etc.)
- Nested spans for sub-operations
- Exceptions and error details

## Event Logging

Plugins may emit structured events for important milestones:

```python
{
    "event_type": "ingestion_completed",
    "timestamp": "2026-05-02T08:15:30Z",
    "ingestion_run_id": "ingest:2026-05-02T08:00:00Z:drupalorg",
    "plugin": "drupalorg:1.0.0",
    "summary": {
        "entity_type": "actor",
        "records_fetched": 5000,
        "records_mapped": 4998,
        "records_failed": 2,
        "duration_seconds": 45.2,
        "status": "success"
    },
    "errors": [
        {
            "record_id": "user:12345",
            "error_code": "TRANSFORM_INVALID_PAYLOAD",
            "message": "Missing required field: id"
        }
    ]
}
```

## Alerting Rules

Framework defines alert rules based on plugin metrics:

```yaml
# alerts.yaml

groups:
  - name: connector_health
    rules:
      - alert: ConnectorHighErrorRate
        expr: |
          (rate(connector_fetch_errors_total[5m]) / rate(connector_fetch_requests_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "{{ $labels.plugin }} error rate > 5%"
          description: "{{ $value | humanizePercentage }} errors in last 5 minutes"
      
      - alert: ConnectorRateLimited
        expr: connector_rate_limit_remaining < 10
        for: 1m
        annotations:
          summary: "{{ $labels.plugin }} approaching rate limit"
      
      - alert: ConnectorDataStale
        expr: connector_data_freshness_hours > 24
        for: 1h
        annotations:
          summary: "{{ $labels.plugin }} data older than 24 hours"
```

## Performance Profiling

Plugins can emit performance data:

```python
{
    "profile_type": "fetch_performance",
    "timestamp": "2026-05-02T08:15:30Z",
    "plugin": "drupalorg",
    "entity_type": "actor",
    "breakdowns": {
        "api_calls": {"count": 50, "total_ms": 5000, "avg_ms": 100},
        "data_transform": {"count": 5000, "total_ms": 800, "avg_ms": 0.16},
        "validation": {"count": 5000, "total_ms": 400, "avg_ms": 0.08},
        "serialization": {"count": 5000, "total_ms": 200, "avg_ms": 0.04}
    }
}
```

## Debug Logging

Optional verbose logging for troubleshooting:

Enable with config:
```yaml
connector:
  plugin_name: drupalorg
  debug: true  # Enable debug logs
```

Debug logs include:
- Full HTTP request/response bodies (with PII redaction)
- Mapping rule execution details
- Entity validation errors
- Performance timing for each step

## Health Check Dashboard

Framework provides a dashboard showing:

- Current health status for each plugin
- Error rates and types
- Response times and throughput
- Freshness of data
- Last successful ingestion
- Pending issues and alerts

Accessible at `/admin/health` or similar.

## Versioning & Deprecation

- **v1.0.0** (current):
  - Structured health reporting
  - Standard Prometheus metrics
  - OpenTelemetry tracing support
  - Structured logging
- **Future enhancements** (→ v1.x.0):
  - Anomaly detection in metrics
  - Automated diagnostic recommendations
  - Machine-learning based alerting
  - Integration with external observability platforms
- **Breaking changes** (→ v2.0.0):
  - Changes to metric names or schema
  - Changes to health status codes
