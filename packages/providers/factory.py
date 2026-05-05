from __future__ import annotations

import importlib
import inspect
import pkgutil
from copy import deepcopy
from typing import Any

from packages.providers import ProviderRegistry
from packages.providers.base import DataSourceProvider


def _merge_dicts(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def discover_provider_classes() -> dict[str, type[DataSourceProvider]]:
    module = importlib.import_module("providers")
    discovered: dict[str, type[DataSourceProvider]] = {}

    for module_info in pkgutil.iter_modules(module.__path__):
        provider_module = importlib.import_module(f"providers.{module_info.name}")
        for attribute_name in dir(provider_module):
            attribute = getattr(provider_module, attribute_name)
            if (
                inspect.isclass(attribute)
                and issubclass(attribute, DataSourceProvider)
                and attribute is not DataSourceProvider
                and not inspect.isabstract(attribute)
            ):
                provider_name = getattr(
                    attribute,
                    "provider_name",
                    module_info.name,
                )
                discovered[str(provider_name)] = attribute

    return discovered


def register_discovered_providers() -> dict[str, type[DataSourceProvider]]:
    discovered = discover_provider_classes()
    for name, provider_cls in discovered.items():
        ProviderRegistry.register(name, provider_cls)
    return discovered


def create_provider(name: str, config: dict[str, Any] | None = None) -> DataSourceProvider:
    if not ProviderRegistry._registry:
        register_discovered_providers()

    provider_cls = ProviderRegistry.get(name)
    provider_config = deepcopy(getattr(provider_cls, "default_config", {}))
    if config:
        provider_config = _merge_dicts(provider_config, config)

    return provider_cls(name=name, config=provider_config)


def get_provider(name: str) -> DataSourceProvider:
    return create_provider(name=name)
