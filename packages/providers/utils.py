"""Credential and configuration management utilities for providers.

Provides secure credential loading from environment variables and
runtime configuration override capabilities.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from packages.shared.settings import get_settings


@lru_cache(maxsize=32)
def get_provider_credentials(provider_name: str) -> dict[str, str]:
    """Get credentials for a provider from environment variables.

    Looks for environment variables in the following order:
    - {PROVIDER}_TOKEN (for bearer tokens)
    - {PROVIDER}_API_KEY (for API key auth)
    - {PROVIDER}_USERNAME and {PROVIDER}_PASSWORD (for basic auth)

    Args:
        provider_name: Name of the provider (e.g., 'drupal')

    Returns:
        Dictionary with available credentials. May contain:
        - 'token': Bearer token for Authorization header
        - 'api_key': API key for X-API-Key header
        - 'username', 'password': For basic auth

    Example:
        >>> creds = get_provider_credentials('drupal')
        >>> if creds.get('token'):
        ...     headers['Authorization'] = f"Bearer {creds['token']}"
    """
    prefix = provider_name.upper()
    settings = get_settings()
    credentials = {}

    # Check for bearer token (highest priority)
    if token := getattr(settings, f"{prefix.lower()}_token", None):
        credentials["token"] = token

    # Check for API key
    if api_key := getattr(settings, f"{prefix.lower()}_api_key", None):
        credentials["api_key"] = api_key

    # Check for basic auth
    username = getattr(settings, f"{prefix.lower()}_username", None)
    password = getattr(settings, f"{prefix.lower()}_password", None)
    if username and password:
        credentials["username"] = username
        credentials["password"] = password

    return credentials


def deep_merge_config(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Deep merge configuration dictionaries.

    Recursively merges overrides into base config, preserving nested structures.

    Args:
        base: Base configuration dictionary
        overrides: Configuration overrides to apply

    Returns:
        Merged configuration

    Example:
        >>> base = {
        ...     "fetch_config": {"timeout": 30, "endpoints": ["/users"]},
        ...     "batch_size": 100,
        ... }
        >>> overrides = {
        ...     "fetch_config": {"timeout": 60},
        ... }
        >>> merged = deep_merge_config(base, overrides)
        >>> assert merged["fetch_config"]["timeout"] == 60
        >>> assert merged["fetch_config"]["endpoints"] == ["/users"]
    """
    result = base.copy()

    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge_config(result[key], value)
        else:
            # Override or add new key
            result[key] = value

    return result


def build_http_headers(
    credentials: dict[str, str],
    additional_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build HTTP headers with authentication.

    Constructs headers based on available credentials. Supports:
    - Bearer token: Authorization: Bearer <token>
    - API key: X-API-Key: <key>
    - Basic auth: Authorization: Basic <base64>

    Args:
        credentials: Credentials dict from get_provider_credentials()
        additional_headers: Additional headers to include

    Returns:
        Dictionary of HTTP headers

    Example:
        >>> creds = {'token': 'ghp_xyz'}
        >>> headers = build_http_headers(creds)
        >>> assert headers['Authorization'] == 'Bearer ghp_xyz'
    """
    import base64

    headers = {
        "User-Agent": "Agora-OSS/1.0",
        "Accept": "application/json",
    }

    # Add authentication
    if credentials.get("token"):
        headers["Authorization"] = f"Bearer {credentials['token']}"
    elif credentials.get("api_key"):
        headers["X-API-Key"] = credentials["api_key"]
    elif credentials.get("username") and credentials.get("password"):
        auth_str = base64.b64encode(
            f"{credentials['username']}:{credentials['password']}".encode()
        ).decode()
        headers["Authorization"] = f"Basic {auth_str}"

    # Add any additional headers
    if additional_headers:
        headers.update(additional_headers)

    return headers


def validate_config(config: dict[str, Any], required_keys: list[str] | None = None) -> bool:
    """Validate provider configuration.

    Args:
        config: Configuration to validate
        required_keys: List of required top-level keys

    Returns:
        True if valid, raises ValueError otherwise

    Raises:
        ValueError: If required keys are missing

    Example:
        >>> config = {"source": "drupal", "fetch_config": {...}}
        >>> validate_config(config, required_keys=["source", "fetch_config"])
    """
    if required_keys is None:
        required_keys = ["source"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    return True


def mask_sensitive_values(obj: Any, depth: int = 0, max_depth: int = 10) -> Any:
    """Recursively mask sensitive values in config for logging.

    Replaces values of sensitive keys with '***' to avoid exposing secrets.

    Args:
        obj: Object to mask (dict, list, or scalar)
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        Object with sensitive values masked

    Example:
        >>> config = {"token": "secret123", "nested": {"api_key": "key456"}}
        >>> masked = mask_sensitive_values(config)
        >>> assert masked["token"] == "***"
        >>> assert masked["nested"]["api_key"] == "***"
    """
    if depth >= max_depth:
        return obj

    sensitive_keys = {
        "token",
        "api_key",
        "password",
        "secret",
        "credentials",
        "auth",
        "key",
    }

    if isinstance(obj, dict):
        return {
            k: (
                "***"
                if any(sensitive in k.lower() for sensitive in sensitive_keys)
                else mask_sensitive_values(v, depth + 1, max_depth)
            )
            for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return type(obj)(mask_sensitive_values(item, depth + 1, max_depth) for item in obj)
    else:
        return obj
