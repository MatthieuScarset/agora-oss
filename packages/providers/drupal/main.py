from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DrupalRecordBase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def to_entity(self, source: str) -> dict[str, Any]:
        raise NotImplementedError
