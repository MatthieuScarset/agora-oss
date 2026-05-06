from __future__ import annotations

from apps.workers.flows.ingest import provider_ingest_flow
from packages.shared.settings import get_settings

DEFAULT_WORK_POOL = get_settings().prefect_work_pool


def deploy_ingest_deployments(work_pool_name: str = DEFAULT_WORK_POOL) -> list[str]:
    """Register the standard Agora Prefect deployments."""

    deployment_ids = [
        provider_ingest_flow.deploy(
            name="drupal-ingest",
            work_pool_name=work_pool_name,
            cron="0 2 * * *",
            parameters={"provider_name": "drupal"},
            tags=["ingest", "drupal"],
            build=False,
            push=False,
            print_next_steps=False,
        ),
        provider_ingest_flow.deploy(
            name="drupal-ingest-dev",
            work_pool_name=work_pool_name,
            parameters={"provider_name": "drupal"},
            tags=["ingest", "dev"],
            build=False,
            push=False,
            print_next_steps=False,
        ),
    ]

    return [str(deployment_id) for deployment_id in deployment_ids]


def main() -> None:
    deployment_ids = deploy_ingest_deployments()
    for deployment_id in deployment_ids:
        print(deployment_id)


if __name__ == "__main__":
    main()
