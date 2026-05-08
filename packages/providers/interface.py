from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import Any

from pydantic import BaseModel


class ProviderBase(ABC):
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self.logger: Logger = getLogger(f"providers.{name}")

    @abstractmethod
    def schema(self) -> dict[str, type[BaseModel]]:
        raise NotImplementedError

    @abstractmethod
    def extract(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def transform(self, raw_data: dict[str, Any]) -> dict[str, list[BaseModel]]:
        raise NotImplementedError

    @abstractmethod
    def load(self, raw_data: dict[str, Any]) -> dict[str, list[BaseModel]]:
        raise NotImplementedError
