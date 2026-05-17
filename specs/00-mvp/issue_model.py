"""Pydantic v2 model example for the Agora Issue envelope.

This file is an example implementation intended for the MVP spec. Put the
production model under the package where models live (e.g., `agora_oss.models`).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class Attachment(BaseModel):
    url: str
    mime_type: Optional[str] = None
    filename: Optional[str] = None


class AgoraIssue(BaseModel):
    """A portable, agnostic issue envelope for Agora.

    - Keep `body` (original) and `body_text` (cleaned) separate.
    - `metadata.raw` must contain the original provider JSON for traceability.
    """

    agora_id: Optional[str] = Field(
        None, description="Canonical UUID for this record"
    )
    provider: str
    provider_id: Optional[str] = None
    harvest_id: Optional[str] = None
    type: str = "issue"

    title: Optional[str] = None
    body: Optional[str] = None
    body_text: Optional[str] = None
    summary: Optional[str] = None

    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    authors: Optional[List[Person]] = None
    participants: Optional[List[str]] = None
    assignees: Optional[List[str]] = None

    status: Optional[str] = None
    priority: Optional[str] = None
    component: Optional[str] = None
    labels: Optional[List[str]] = None

    comments_count: Optional[int] = None
    attachments: Optional[List[Attachment]] = None

    language: Optional[str] = None
    canonical_url: Optional[str] = None
    embeddings_path: Optional[str] = None
    extracted_actions: Optional[List[str]] = None

    metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    schema_version: str = "agora-issue-v1"

    class Config:
        frozen = False
        validate_assignment = True


__all__ = ["AgoraIssue", "Person", "Attachment"]
