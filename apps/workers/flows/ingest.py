from __future__ import annotations

from typing import Any

from prefect import flow, task
from prefect.logging import get_run_logger
from sqlmodel import Session

from packages.providers.factory import get_provider
from packages.shared.database import ensure_schema, get_engine, upsert_entities
from packages.shared.storage import enqueue_embedding_jobs


@task(
    retries=3,
    retry_delay_seconds=[60, 120, 240],
    tags=["fetch"],
    description="Fetch raw data from provider",
)
def fetch_task(provider_name: str) -> dict[str, list[dict[str, Any]]]:
    """Fetch raw data from the specified provider.

    Args:
        provider_name: Name of the provider (e.g., 'drupal')

    Returns:
        Dictionary mapping dataset names to lists of raw records

    Raises:
        Exception: If fetch fails after all retries
    """
    provider = get_provider(provider_name)
    raw_data = provider.fetch()

    # Log summary statistics
    total_records = sum(len(records) for records in raw_data.values())
    logger = get_run_logger()
    logger.info(
        f"Fetched {total_records} total records across {len(raw_data)} datasets",
        extra={
            "provider": provider_name,
            "datasets": list(raw_data.keys()),
            "total_records": total_records,
        },
    )

    return raw_data


@task(
    retries=2,
    retry_delay_seconds=[30, 60],
    tags=["normalize"],
    description="Normalize raw data to entity models",
)
def normalize_task(
    provider_name: str, raw_data: dict[str, list[dict[str, Any]]]
) -> dict[str, list[Any]]:
    """Normalize raw data to canonical entity models.

    Args:
        provider_name: Name of the provider
        raw_data: Raw data fetched from provider

    Returns:
        Dictionary mapping dataset names to lists of normalized entities

    Raises:
        ValidationError: If normalization fails
    """
    provider = get_provider(provider_name)
    normalized_data = provider.normalize(raw_data)

    # Log normalization statistics
    total_entities = sum(len(entities) for entities in normalized_data.values())
    logger = get_run_logger()
    logger.info(
        f"Normalized {total_entities} entities",
        extra={
            "provider": provider_name,
            "datasets": list(normalized_data.keys()),
            "total_entities": total_entities,
            "dataset_counts": {k: len(v) for k, v in normalized_data.items()},
        },
    )

    return normalized_data


@task(
    retries=2,
    retry_delay_seconds=[60, 120],
    tags=["persist"],
    description="Persist normalized entities to database",
)
def persist_task(
    provider_name: str, normalized_data: dict[str, list[Any]], batch_size: int | None = None
) -> list[dict[str, str]]:
    """Persist normalized entities to database with change detection.

    Performs bulk upsert with automatic change detection via payload hashing.
    Supports batching for large datasets.

    Args:
        provider_name: Name of the provider
        normalized_data: Normalized entities from normalize_task
        batch_size: Optional batch size for processing large datasets

    Returns:
        List of changed jobs (ready for embedding queue)
    """
    source = provider_name
    engine = get_engine()
    ensure_schema(engine)

    # Get batch size from config if not provided
    if batch_size is None:
        provider = get_provider(provider_name)
        batch_size = provider.config.get("batch_size", 100)

    changed_jobs: list[dict[str, str]] = []
    logger = get_run_logger()

    with Session(engine) as session:
        for entity_type, entities in normalized_data.items():
            if not entities:
                continue

            # Process in batches
            total_batches = (len(entities) + batch_size - 1) // batch_size
            logger.info(
                f"Persisting {len(entities)} {entity_type} in {total_batches} batch(es)",
                extra={
                    "provider": provider_name,
                    "entity_type": entity_type,
                    "total_entities": len(entities),
                    "batch_size": batch_size,
                    "total_batches": total_batches,
                },
            )

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(entities))
                batch_entities = entities[start_idx:end_idx]

                try:
                    jobs = upsert_entities(
                        source=source,
                        entity_type=entity_type,
                        entities=batch_entities,
                        session=session,
                    )
                    changed_jobs.extend(jobs)

                    logger.info(
                        f"Batch {batch_idx + 1}/{total_batches}: "
                        f"Persisted {len(batch_entities)} entities, "
                        f"{len(jobs)} changed",
                        extra={
                            "batch_idx": batch_idx + 1,
                            "batch_total": total_batches,
                            "entities_in_batch": len(batch_entities),
                            "changed_count": len(jobs),
                        },
                    )
                except Exception as e:
                    logger.error(
                        f"Error persisting batch {batch_idx + 1} for {entity_type}",
                        extra={
                            "batch_idx": batch_idx + 1,
                            "entity_type": entity_type,
                            "error": str(e),
                        },
                    )
                    raise

    logger.info(
        f"Persistence complete: {len(changed_jobs)} total changed entities",
        extra={
            "provider": provider_name,
            "total_changed": len(changed_jobs),
        },
    )

    return changed_jobs


@task(
    retries=1,
    retry_delay_seconds=[30],
    tags=["queue"],
    description="Queue changed entities for embedding",
)
def queue_for_embeddings_task(changed_jobs: list[dict[str, str]]) -> int:
    """Queue changed entities for embeddings generation.

    Args:
        changed_jobs: List of changed jobs from persist_task

    Returns:
        Number of jobs successfully queued
    """
    if not changed_jobs:
        logger = get_run_logger()
        logger.info("No changes to queue for embeddings")
        return 0

    queued_count = enqueue_embedding_jobs(changed_jobs)

    logger = get_run_logger()
    logger.info(
        f"Queued {queued_count} entities for embedding",
        extra={
            "queued_count": queued_count,
            "jobs_attempted": len(changed_jobs),
        },
    )

    return queued_count


@flow(
    name="provider-ingest-flow",
    description="Complete ingest pipeline: fetch → normalize → persist → queue embeddings",
)
def provider_ingest_flow(
    provider_name: str = "drupal",
) -> dict[str, Any]:
    """End-to-end data ingestion flow.

    Orchestrates the complete pipeline:
    1. Fetch raw data from provider
    2. Normalize to canonical entity models
    3. Persist to database with change detection
    4. Queue changed entities for embedding

    Args:
        provider_name: Name of the provider (default: 'drupal')

    Returns:
        Dictionary with flow results and statistics

    Example:
        >>> result = provider_ingest_flow(provider_name="drupal")
        >>> print(result["changed_jobs"])  # Number of changed entities
        >>> print(result["queued_jobs"])   # Number of queued for embeddings
    """
    logger = get_run_logger()
    logger.info(
        f"Starting ingest flow for provider: {provider_name}", extra={"provider": provider_name}
    )

    # Fetch phase
    raw_data = fetch_task(provider_name=provider_name)

    # Normalize phase
    normalized_data = normalize_task(provider_name=provider_name, raw_data=raw_data)

    # Persist phase
    changed_jobs = persist_task(provider_name=provider_name, normalized_data=normalized_data)

    # Queue for embeddings phase
    queued_count = queue_for_embeddings_task(changed_jobs)

    result = {
        "provider": provider_name,
        "datasets": sorted(normalized_data.keys()),
        "changed_jobs": len(changed_jobs),
        "queued_jobs": queued_count,
        "status": "success",
    }

    logger.info("Ingest flow completed successfully", extra=result)

    return result
