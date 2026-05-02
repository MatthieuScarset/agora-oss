# Plugin Interface v1

**Version**: 1.0.0  
**Last Updated**: 2026-05-02  
**Owner**: Data Connector  

## Overview

Plugins are Python modules that implement the `IConnectorPlugin` interface. They act as adapters between external data sources and Agora's canonical model. The plugin interface defines:

- **Lifecycle methods**: How plugins are discovered, initialized, and torn down
- **Data extraction methods**: How to fetch data from sources
- **Health reporting**: How plugins communicate status
- **Error handling**: How plugins signal problems

## Core Interface: IConnectorPlugin

All plugins must implement the following interface (Python abstract base class):

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RawEnvelope:
    """Container for raw source data"""
    envelope_id: str
    source_family: str
    source_name: str
    connector_version: str
    entity_type: str  # actor, project, issue, event, contribution
    source_native_id: str
    extraction_timestamp: str  # ISO 8601
    cursor_state: Optional[Dict[str, Any]]  # For incremental fetches
    payload_hash: str  # SHA256 of payload
    payload: Dict[str, Any]  # Raw source data


class IConnectorPlugin(ABC):
    """Base interface for all data connectors"""
    
    @abstractmethod
    async def discover_capabilities(self) -> Dict[str, Any]:
        """
        Return capabilities of this plugin.
        
        Returns:
            {
                "capabilities": ["discover_capabilities", "fetch_full", "fetch_incremental", ...],
                "entity_types": ["actor", "project", "issue"],
                "supports_incremental": True,
                "supports_relationships": True,
                "supported_locales": ["en", "es", "fr"],
                "default_locale": "en",
                "required_config_fields": ["api_key", "base_url"],
                "max_batch_size": 100,
                "rate_limit": {"requests_per_second": 10}
            }
        """
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Configuration dict from source-config.yaml
        
        Raises:
            ConfigError: If required config is missing or invalid
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources (close connections, etc.)"""
        pass
    
    @abstractmethod
    async def fetch_full(self, entity_type: str) -> AsyncIterator[RawEnvelope]:
        """
        Fetch all data for a given entity type.
        
        Args:
            entity_type: One of [actor, project, issue, event, contribution]
        
        Yields:
            RawEnvelope objects
        
        Raises:
            FetchError: If fetch fails
        """
        pass
    
    @abstractmethod
    async def fetch_incremental(
        self,
        entity_type: str,
        cursor_state: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[RawEnvelope]:
        """
        Fetch only changed data since last cursor.
        
        Args:
            entity_type: One of [actor, project, issue, event, contribution]
            cursor_state: Previous cursor from last fetch (can be None for initial)
        
        Yields:
            RawEnvelope objects
        
        Raises:
            FetchError: If fetch fails
        """
        pass
    
    @abstractmethod
    async def emit_raw_envelope(self, raw_data: Dict[str, Any]) -> RawEnvelope:
        """
        Transform raw source data into a RawEnvelope.
        
        Args:
            raw_data: Data from source API/export
        
        Returns:
            RawEnvelope with envelope_id, payload, cursor_state, etc.
        
        Raises:
            TransformError: If raw_data cannot be transformed
        """
        pass
    
    @abstractmethod
    async def map_to_canonical(self, raw_envelope: RawEnvelope) -> Dict[str, Any]:
        """
        Map a RawEnvelope to a canonical entity.
        
        Args:
            raw_envelope: RawEnvelope from emit_raw_envelope
        
        Returns:
            Dict matching canonical-entities-v1.md schema
        
        Raises:
            MappingError: If mapping fails
        """
        pass
    
    @abstractmethod
    async def report_health(self) -> Dict[str, Any]:
        """
        Report plugin and source health status.
        
        Returns:
            {
                "status": "healthy" | "degraded" | "error",
                "last_check_timestamp": "2026-05-02T08:00:00Z",
                "messages": ["API responding normally"],
                "metrics": {
                    "requests_today": 5000,
                    "errors_today": 2,
                    "uptime_percent": 99.98
                }
            }
        """
        pass
```

## Plugin Lifecycle

1. **Discovery Phase**:
   - Framework discovers plugin modules in `plugins/` directory
   - Calls `discover_capabilities()`
   - Validates that plugin declares required capabilities

2. **Initialization Phase**:
   - Framework passes source config to `initialize(config)`
   - Plugin validates config, caches credentials, opens connections
   - Plugin ready for data fetch

3. **Fetch Phase**:
   - Framework calls `fetch_full()` or `fetch_incremental()`
   - Plugin streams RawEnvelopeobjects
   - Framework passes envelopes to normalization layer

4. **Health Monitoring Phase**:
   - Framework periodically calls `report_health()`
   - Plugin reports API status, error rates, etc.

5. **Shutdown Phase**:
   - Framework calls `shutdown()` on graceful termination
   - Plugin closes connections, releases resources

## RawEnvelope Contract

Every raw envelope must include:

```python
{
    "envelope_id": "envelope:drupalorg:2026-05-02T08:00:00Z:user:12345",
    "source_family": "drupalorg",
    "source_name": "drupal.org community",
    "connector_version": "1.0.0",
    "entity_type": "actor",  # Which canonical entity type this data will become
    "source_native_id": "12345",  # Original ID in source
    "extraction_timestamp": "2026-05-02T08:15:30Z",  # When fetched from source
    "cursor_state": {"page": 2, "last_id": 12345},  # For incremental continues
    "payload_hash": "abc123def456...",  # SHA256(json.dumps(payload, sort_keys=True))
    "payload": {  # Raw, unmodified source data
        "uid": 12345,
        "name": "Alice Developer",
        "mail": "alice@example.com",
        # ... all source-native fields
    }
}
```

## Error Handling

Plugins must raise specific exception types:

```python
class PluginError(Exception):
    """Base exception for all plugin errors"""
    pass

class ConfigError(PluginError):
    """Configuration is invalid or incomplete"""
    pass

class AuthError(PluginError):
    """Authentication/authorization failed"""
    pass

class FetchError(PluginError):
    """Data fetch failed (network, timeout, etc.)"""
    pass

class TransformError(PluginError):
    """Cannot transform raw data to envelope"""
    pass

class MappingError(PluginError):
    """Cannot map envelope to canonical entity"""
    pass
```

Framework catches these and logs appropriately.

## Plugin Discovery

Plugins are discovered via:

1. **Module name convention**: Files in `plugins/{source_family}/connector.py`
2. **Class name convention**: Class named `Connector` that implements `IConnectorPlugin`
3. **Registration**: Plugin registers via `discover_capabilities()` declaration

Example:
```
plugins/
  drupalorg/
    connector.py        # Must contain class Connector(IConnectorPlugin)
    requirements.txt    # Optional dependencies
    __init__.py
  wordpressorg/
    connector.py
  github/
    connector.py
```

## Async/Await Pattern

All plugin methods are async. This allows:

- Non-blocking HTTP requests (aiohttp)
- Concurrent processing of multiple data sources
- Better resource utilization in high-throughput scenarios

Framework runs plugins in an event loop:

```python
asyncio.run(plugin.fetch_full("actor"))
```

## Testing Requirements

Every plugin must include:

1. **Unit tests** for each method
2. **Integration tests** that fetch from actual source (with fixtures/mocks)
3. **Schema validation** that output validates against canonical-entities-v1.md

Test files:
```
plugins/drupalorg/
  connector.py
  test_connector.py
  fixtures/
    actors_sample.json
    projects_sample.json
```

## Versioning & Deprecation

- **v1.0.0** (current): Basic interface with fetch_full, fetch_incremental, mapping
- **Future enhancements** (→ v1.x.0):
  - Partial fetch (query by date range, entity subset)
  - Webhook support for real-time updates
  - Compression/streaming for large payloads
- **Breaking changes** (→ v2.0.0):
  - Changes to method signatures
  - Changes to exception model
