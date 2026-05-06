from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    compose_project_name: str = "agora"
    tz: str = "UTC"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "agora"
    postgres_user: str = "agora"
    postgres_password: str = "agora_local_password"

    database_url: str = "postgresql+psycopg://agora:agora_local_password@postgres:5432/agora"

    vector_store_backend: str = "pgvector"
    vector_store_table: str = "document_embeddings"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = "redis://redis:6379/0"

    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_api_port: int = 9000
    minio_console_port: int = 9001

    s3_bucket: str = "agora-raw"
    s3_region: str = "us-east-1"
    s3_endpoint: str = "http://minio:9000"
    s3_public_endpoint: str = "http://localhost:9000"
    s3_use_ssl: bool = False

    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    aws_default_region: str = "us-east-1"

    prefect_api_port: int = 4200
    prefect_api_url: str = "http://localhost:4200/api"
    prefect_ui_url: str = "http://localhost:4200"
    prefect_work_pool: str = "agora-local-pool"
    prefect_log_level: str = "INFO"
    prefect_server_database_connection_url: str = (
        "postgresql+asyncpg://agora:agora_local_password@postgres:5432/agora"
    )
    prefect_server_database_sqlalchemy_connect_args_search_path: str = "prefect, public"

    node_env: str = "development"
    frontend_port: int = 3000

    drupal_token: str | None = None
    drupal_api_key: str | None = None
    drupal_username: str | None = None
    drupal_password: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
