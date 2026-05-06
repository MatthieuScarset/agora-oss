from __future__ import annotations

import json
from typing import Any, cast

from redis import Redis

from packages.shared.settings import get_settings

DEFAULT_QUEUE_NAME = "embeddings:queue"


def get_redis_client() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


def enqueue_embedding_jobs(
    jobs: list[dict[str, str]],
    queue_name: str = DEFAULT_QUEUE_NAME,
    client: Redis | None = None,
) -> int:
    if not jobs:
        return 0

    redis_client = client or get_redis_client()
    payloads = [json.dumps(job, sort_keys=True) for job in jobs]
    return cast(int, redis_client.rpush(queue_name, *payloads))


def dequeue_embedding_job(
    queue_name: str = DEFAULT_QUEUE_NAME,
    timeout_seconds: int = 1,
    client: Redis | None = None,
) -> dict[str, Any] | None:
    redis_client = client or get_redis_client()
    item = redis_client.blpop(queue_name, timeout=timeout_seconds)
    if item is None:
        return None

    _, payload = cast(tuple[str, str], item)
    return cast(dict[str, Any], json.loads(payload))
