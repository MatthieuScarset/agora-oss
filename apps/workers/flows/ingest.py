from __future__ import annotations

from typing import Any

from prefect import flow, task
from sqlmodel import Session

from packages.providers.factory import get_provider
from packages.shared.database import ensure_schema, get_engine, upsert_entities
from packages.shared.storage import enqueue_embedding_jobs


@task(retries=3, retry_delay_seconds=[60, 120, 240])
def fetch_task(provider_name: str) -> dict[str, list[dict[str, Any]]]:
    provider = get_provider(provider_name)
    return provider.fetch()


@task
def normalize_task(
    provider_name: str, raw_data: dict[str, list[dict[str, Any]]]
) -> dict[str, list[Any]]:
    provider = get_provider(provider_name)
    return provider.normalize(raw_data)


@task
def persist_task(provider_name: str, normalized_data: dict[str, list[Any]]) -> list[dict[str, str]]:
    source = provider_name
    engine = get_engine()
    ensure_schema(engine)

    changed_jobs: list[dict[str, str]] = []
    with Session(engine) as session:
        for entity_type, entities in normalized_data.items():
            jobs = upsert_entities(
                source=source,
                entity_type=entity_type,
                entities=entities,
                session=session,
            )
            changed_jobs.extend(jobs)

    return changed_jobs


@task
def queue_for_embeddings_task(changed_jobs: list[dict[str, str]]) -> int:
    return enqueue_embedding_jobs(changed_jobs)


@flow(name="provider-ingest-flow")
def provider_ingest_flow(
    provider_name: str = "drupal",
) -> dict[str, Any]:
    raw_data = fetch_task(provider_name=provider_name)
    normalized_data = normalize_task(provider_name=provider_name, raw_data=raw_data)
    changed_jobs = persist_task(provider_name=provider_name, normalized_data=normalized_data)
    queued_count = queue_for_embeddings_task(changed_jobs)

    return {
        "provider": provider_name,
        "datasets": sorted(normalized_data.keys()),
        "changed_jobs": len(changed_jobs),
        "queued_jobs": queued_count,
    }
