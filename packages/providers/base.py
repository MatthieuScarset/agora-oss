from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import Any

from pydantic import BaseModel


class DataSourceProvider(ABC):
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self.logger: Logger = getLogger(f"providers.{name}")

    @abstractmethod
    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_data: dict[str, list[dict[str, Any]]]) -> dict[str, list[BaseModel]]:
        raise NotImplementedError

    @abstractmethod
    def schema(self) -> dict[str, type[BaseModel]]:
        raise NotImplementedError

    def before_fetch(self) -> None:
        self.logger.info("before_fetch", extra={"provider": self.name})

    def after_normalize(self, normalized: dict[str, list[BaseModel]]) -> None:
        total_items = sum(len(items) for items in normalized.values())
        self.logger.info(
            "after_normalize",
            extra={
                "provider": self.name,
                "datasets": list(normalized.keys()),
                "total_items": total_items,
            },
        )

    def _handle_error(self, phase: str, error: Exception) -> None:
        self.logger.exception(
            "provider_error",
            extra={"provider": self.name, "phase": phase, "error_type": type(error).__name__},
        )
