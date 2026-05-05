from __future__ import annotations

from typing import Type

from packages.providers.base import DataSourceProvider


class ProviderRegistry:
    _registry: dict[str, type[DataSourceProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[DataSourceProvider]) -> None:
        cls._registry[name] = provider_class

    @classmethod
    def get(cls, name: str) -> type[DataSourceProvider]:
        if name not in cls._registry:
            raise KeyError(f"Provider '{name}' is not registered.")
        return cls._registry[name]


__all__ = [
    "DataSourceProvider",
    "ProviderRegistry",
]
