from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, UniqueConstraint, create_engine, text
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlmodel import Field, Session, SQLModel

from packages.shared.models import BaseEntity


class SourceRecord(SQLModel, table=True):
    __tablename__ = "source_records"
    __table_args__ = (UniqueConstraint("source", "entity_type", "external_id"),)

    id: int | None = Field(default=None, primary_key=True)
    source: str = Field(index=True, min_length=1)
    entity_type: str = Field(index=True, min_length=1)
    external_id: str = Field(index=True, min_length=1)
    payload: dict[str, Any] = Field(sa_type=JSONB)
    payload_hash: str = Field(index=True, min_length=64, max_length=64)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )


def get_engine() -> Any:
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://agora:agora_local_password@postgres:5432/agora"
    )
    return create_engine(database_url, future=True)


def ensure_schema(engine: Any | None = None) -> None:
    target_engine = engine or get_engine()
    SQLModel.metadata.create_all(target_engine)

    # pgvector extension/table are managed explicitly because SQLModel has no native Vector type.
    with target_engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(
            text(
                """
				CREATE TABLE IF NOT EXISTS document_embeddings (
					source TEXT NOT NULL,
					entity_type TEXT NOT NULL,
					external_id TEXT NOT NULL,
					embedding VECTOR(64) NOT NULL,
					updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
					PRIMARY KEY (source, entity_type, external_id)
				)
				"""
            )
        )


def hash_payload(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def upsert_entities(
    source: str,
    entity_type: str,
    entities: list[BaseEntity],
    session: Session,
) -> list[dict[str, str]]:
    changed_jobs: list[dict[str, str]] = []

    for entity in entities:
        payload = entity.model_dump(mode="json")
        external_id = str(entity.id)
        payload_hash = hash_payload(payload)

        existing_stmt = text(
            """
			SELECT payload_hash
			FROM source_records
			WHERE source = :source
                AND entity_type = :entity_type
                AND external_id = :external_id
			"""
        )
        existing = session.exec(
            existing_stmt,
            {
                "source": source,
                "entity_type": entity_type,
                "external_id": external_id,
            },
        ).first()
        previous_hash = existing[0] if existing else None

        stmt = insert(SourceRecord).values(
            source=source,
            entity_type=entity_type,
            external_id=external_id,
            payload=payload,
            payload_hash=payload_hash,
            updated_at=datetime.now(UTC),
        )
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["source", "entity_type", "external_id"],
            set_={
                "payload": stmt.excluded.payload,
                "payload_hash": stmt.excluded.payload_hash,
                "updated_at": datetime.now(UTC),
            },
        )
        session.exec(upsert_stmt)

        if previous_hash != payload_hash:
            changed_jobs.append(
                {
                    "source": source,
                    "entity_type": entity_type,
                    "external_id": external_id,
                    "text": build_embedding_text(payload),
                }
            )

    session.commit()
    return changed_jobs


def build_embedding_text(payload: dict[str, Any]) -> str:
    preferred_fields = ["title", "name", "description", "body"]
    parts: list[str] = []

    for field in preferred_fields:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())

    if not parts:
        parts.append(json.dumps(payload, sort_keys=True))

    return "\n".join(parts)


def upsert_embedding(
    source: str,
    entity_type: str,
    external_id: str,
    embedding: list[float],
    session: Session,
) -> None:
    vector_value = "[" + ",".join(str(value) for value in embedding) + "]"
    stmt = text(
        """
		INSERT INTO document_embeddings (source, entity_type, external_id, embedding, updated_at)
		VALUES (:source, :entity_type, :external_id, CAST(:embedding AS vector), NOW())
		ON CONFLICT (source, entity_type, external_id)
		DO UPDATE SET embedding = EXCLUDED.embedding, updated_at = NOW()
		"""
    )
    session.exec(
        stmt,
        {
            "source": source,
            "entity_type": entity_type,
            "external_id": external_id,
            "embedding": vector_value,
        },
    )
    session.commit()
