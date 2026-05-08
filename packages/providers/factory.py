from __future__ import annotations

import importlib
import inspect
import pkgutil
from copy import deepcopy
from typing import Any, Callable, Type

from packages.providers.interface import ProviderBase


class ProviderRegistry:
    """Global registry for data source providers."""

    _registry: dict[str, type[ProviderBase]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[ProviderBase]) -> None:
        """Register a provider class under the given name."""
        cls._registry[name] = provider_class

    @classmethod
    def get(cls, name: str) -> type[ProviderBase]:
        """Retrieve a registered provider class by name.

        Raises:
            KeyError: If provider is not registered
        """
        if name not in cls._registry:
            raise KeyError(f"Provider '{name}' is not registered.")
        return cls._registry[name]


def register_provider(name: str) -> Callable[[Type[ProviderBase]], Type[ProviderBase]]:
    """Decorator for provider classes to register themselves at import time.

    Usage:
        @register_provider("drupal")
        class DrupalProvider(ProviderBase):
            ...
    """

    def _decorator(cls: Type[ProviderBase]) -> Type[ProviderBase]:
        ProviderRegistry.register(name, cls)
        return cls

    return _decorator


class ProviderFactory:
    """Factory for creating provider instances with automatic discovery and registration.

    Provides a simple interface for instantiating data source providers with config merging.
    Automatically discovers and registers providers via:
      1. Decorator-based registration (@register_provider) when modules are imported
      2. Fallback discovery if no modules are registered
    """

    def __init__(self) -> None:
        self._initialized = False

    def get_provider(self, name: str, config: dict[str, Any] | None = None) -> ProviderBase:
        """Create and return a provider instance by name.

        Args:
            name: Provider name (e.g., "drupal")
            config: Optional runtime config overrides

        Returns:
            Instantiated provider with merged config

        Raises:
            KeyError: If provider is not registered
        """
        self._ensure_providers_loaded()
        provider_cls = ProviderRegistry.get(name)
        return self._instantiate(provider_cls, name, config)

    def _ensure_providers_loaded(self) -> None:
        """Load providers if not already loaded. Tries decorator-based discovery first."""
        if self._initialized or ProviderRegistry._registry:
            return

        try:
            self._load_provider_modules()
        except Exception:
            self._load_via_discovery()

        self._initialized = True

    def _load_module_for_provider(self, module_info: pkgutil.ModuleInfo) -> Any:
        """Load a provider module, handling both packages and modules.

        Args:
            module_info: Module info from pkgutil.iter_modules

        Returns:
            The imported module
        """
        if module_info.ispkg:
            # Provider is a package, import its main.py
            return importlib.import_module(f"providers.{module_info.name}.main")
        else:
            # Provider is a module, import directly
            return importlib.import_module(f"providers.{module_info.name}")

    def _load_provider_modules(self) -> None:
        """Import all provider modules to trigger @register_provider decorators."""
        module = importlib.import_module("providers")
        for module_info in pkgutil.iter_modules(module.__path__):
            self._load_module_for_provider(module_info)

    def _load_via_discovery(self) -> None:
        """Fallback: scan modules and find ProviderBase subclasses."""
        module = importlib.import_module("providers")
        for module_info in pkgutil.iter_modules(module.__path__):
            provider_module = self._load_module_for_provider(module_info)
            for attribute_name in dir(provider_module):
                attribute = getattr(provider_module, attribute_name)
                if (
                    inspect.isclass(attribute)
                    and issubclass(attribute, ProviderBase)
                    and attribute is not ProviderBase
                    and not inspect.isabstract(attribute)
                ):
                    provider_name = getattr(attribute, "provider_name", module_info.name)
                    ProviderRegistry.register(str(provider_name), attribute)

    def _instantiate(
        self,
        provider_cls: type[ProviderBase],
        name: str,
        config: dict[str, Any] | None = None,
    ) -> ProviderBase:
        """Instantiate a provider with merged config."""
        provider_config = deepcopy(getattr(provider_cls, "default_config", {}))
        if config:
            provider_config = self._merge_dicts(provider_config, config)
        return provider_cls(name=name, config=provider_config)

    @staticmethod
    def _merge_dicts(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """Deep merge overrides into base dict."""
        merged = deepcopy(base)
        for key, value in overrides.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = ProviderFactory._merge_dicts(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged


# Singleton factory instance
_factory: ProviderFactory = ProviderFactory()


def get_provider(name: str, config: dict[str, Any] | None = None) -> ProviderBase:
    """Get a provider instance by name.

    Args:
        name: Provider name (e.g., "drupal")
        config: Optional runtime config overrides

    Returns:
        Instantiated provider instance

    Example:
        provider = get_provider("drupal", config={"api_url": "https://custom.example.com"})
    """
    return _factory.get_provider(name, config)
