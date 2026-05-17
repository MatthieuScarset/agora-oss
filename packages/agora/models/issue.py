from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Issue(BaseModel):
    nid: int | None = Field(None)
    title: str | None = Field(None)
    body: str | None = Field(None)
    created: int | None = Field(None)
    changed: int | None = Field(None)
    author_id: int | None = Field(None)
    status: int | None = Field(None)
    priority: str | None = Field(None)
    component: str | None = Field(None)
    url: str | None = Field(None)
    comments: int | None = Field(None)
    tags: List[str] | None = Field(default_factory=list)

    model_config = {"extra": "ignore"}
