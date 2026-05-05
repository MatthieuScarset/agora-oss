from __future__ import annotations

import hashlib
from typing import Any

from sqlmodel import Session

from packages.shared.database import ensure_schema, get_engine, upsert_embedding
from packages.shared.storage import dequeue_embedding_job


class StubEmbeddingModel:
    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < self.dimension:
            seed = hashlib.sha256(seed).digest()
            for byte in seed:
                values.append((byte / 255.0) * 2 - 1)
                if len(values) >= self.dimension:
                    break
        return values


def process_embedding_job(job: dict[str, Any], model: StubEmbeddingModel | None = None) -> bool:
    embedding_model = model or StubEmbeddingModel()
    text = str(job.get("text", "")).strip()
    if not text:
        return False

    engine = get_engine()
    ensure_schema(engine)
    vector = embedding_model.embed(text)

    with Session(engine) as session:
        upsert_embedding(
            source=str(job["source"]),
            entity_type=str(job["entity_type"]),
            external_id=str(job["external_id"]),
            embedding=vector,
            session=session,
        )

    return True


def run_embedding_worker_once() -> bool:
    job = dequeue_embedding_job()
    if job is None:
        return False
    return process_embedding_job(job)
