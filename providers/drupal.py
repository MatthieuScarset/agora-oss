from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from packages.providers.base import DataSourceProvider
from packages.providers.utils import build_http_headers, get_provider_credentials
from packages.shared.models import Actor, Issue, Project, aggregate_validation_errors


def _normalize_issue_status(row: dict[str, Any]) -> str:
    value = row.get("field_issue_status", row.get("status"))
    if str(value) in {"0", "closed", "fixed", "resolved", "postponed"}:
        return "closed"
    return "open"


def _infer_issue_type(row: dict[str, Any]) -> str:
    category = row.get("field_issue_category")
    category_mapping = {
        "1": "bug",
        "2": "feature",
        "3": "task",
        "4": "support",
    }
    if category is not None:
        mapped = category_mapping.get(str(category))
        if mapped:
            return mapped

    title = str(row.get("title", "")).lower()
    if "bug" in title or "fix" in title:
        return "bug"
    if "support" in title:
        return "support"
    if "task" in title:
        return "task"
    return "feature"


def _extract_text_summary(body: Any) -> str | None:
    if isinstance(body, dict):
        value = body.get("summary") or body.get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()
    if isinstance(body, str) and body.strip():
        return body.strip()
    return None


def _load_incremental_state(state_file: str | None) -> dict[str, Any]:
    """Load incremental fetch state (ETags, cursors, timestamps)."""
    if not state_file:
        return {}
    try:
        path = Path(state_file)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return cast(dict[str, Any], json.loads(f.read()))
    except (OSError, json.JSONDecodeError):
        # Log warning but don't fail - treat as fresh fetch
        pass
    return {}


def _save_incremental_state(state: dict[str, Any], state_file: str | None) -> None:
    """Persist incremental fetch state."""
    if not state_file:
        return
    try:
        path = Path(state_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
    except OSError:
        # Log warning but don't fail - graceful degradation
        pass


class DrupalRecordBase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def to_entity(self, source: str) -> dict[str, Any]:
        raise NotImplementedError


class DrupalActorRecord(DrupalRecordBase):
    uid: Any
    created: Any
    changed: Any | None = None
    name: Any
    mail: Any | None = None
    picture: Any | None = None
    status: Any = 1
    roles: Any = Field(default_factory=list)
    maintained_projects: Any = Field(default_factory=list)
    contributed_projects: Any = Field(default_factory=list)

    def to_entity(self, source: str) -> dict[str, Any]:
        return {
            "id": self.uid,
            "source": source,
            "created_at": self.created,
            "updated_at": self.changed or self.created,
            "name": self.name,
            "email": self.mail,
            "picture_url": self.picture,
            "status": self.status,
            "roles": self.roles,
            "maintained_projects": self.maintained_projects,
            "contributed_projects": self.contributed_projects,
        }


class DrupalProjectRecord(DrupalRecordBase):
    nid: Any
    created: Any
    changed: Any | None = None
    title: Any
    body: Any | None = None
    status: Any = 0
    field_project_type: Any | None = None
    type: Any | None = None
    maintainer_uid: Any | None = None
    parent_nid: Any | None = None
    dependency_nids: Any = Field(default_factory=list)
    field_project_license: Any | None = None
    field_project_components: Any = Field(default_factory=list)
    author: Any | None = None

    def to_entity(self, source: str) -> dict[str, Any]:
        license_field = self.field_project_license or {}
        author = self.author or {}
        project_type = self.field_project_type or self.type or "project_module"
        return {
            "id": self.nid,
            "source": source,
            "created_at": self.created,
            "updated_at": self.changed,
            "title": self.title,
            "body": _extract_text_summary(self.body),
            "status": self.status,
            "project_type": project_type,
            "maintainer_uid": self.maintainer_uid or author.get("id"),
            "parent_id": self.parent_nid,
            "dependency_ids": self.dependency_nids,
            "license_title": license_field.get("title"),
            "license_url": license_field.get("url"),
            "components": self.field_project_components,
        }


class DrupalIssueRecord(DrupalRecordBase):
    iid: Any | None = None
    nid: Any | None = None
    created: Any
    changed: Any | None = None
    title: Any
    description: Any | None = None
    body: Any | None = None
    field_issue_status: Any | None = None
    status: Any | None = None
    field_issue_category: Any | None = None
    project_nid: Any | None = None
    field_project: Any | None = None
    reporter_uid: Any | None = None
    reporter_name: Any | None = None
    assigned_to_uid: Any | None = None
    closed_at: Any | None = None
    author: Any | None = None

    def to_entity(self, source: str) -> dict[str, Any]:
        field_project = self.field_project or {}
        author = self.author or {}
        row = self.model_dump()
        issue_status = _normalize_issue_status(row)
        return {
            "id": self.iid or self.nid,
            "source": source,
            "created_at": self.created,
            "updated_at": self.changed,
            "title": self.title,
            "description": self.description or _extract_text_summary(self.body),
            "status": issue_status,
            "issue_type": _infer_issue_type(row),
            "project_id": self.project_nid or field_project.get("id"),
            "reporter_uid": self.reporter_uid or author.get("id"),
            "reporter_name": self.reporter_name or author.get("name"),
            "assigned_to_uid": self.assigned_to_uid,
            "closed_at": self.closed_at if issue_status == "closed" else None,
        }


class DrupalProvider(DataSourceProvider):
    provider_name = "drupal"
    record_models: dict[str, type[DrupalRecordBase]] = {
        "actors": DrupalActorRecord,
        "projects": DrupalProjectRecord,
        "issues": DrupalIssueRecord,
    }
    default_config = {
        "source": "drupal",
        "fetch_config": {
            "base_url": "https://drupal.org",
            "use_http": False,  # Set to True to enable HTTP fetching instead of files
            "endpoints": [
                "/api-d7/user",
                "/api-d7/node?type=project_module",
                "/api-d7/node?type=project_issue",
            ],
            "files": {
                "actors": "data/mock/drupalorg/user.json",
                "projects": "data/mock/drupalorg/project_module.json",
                "issues": "data/mock/drupalorg/project_issue.json",
            },
            "timeout_seconds": 30,
            "per_page": 50,  # 50 is the max unfortunately for Drupal's REST API.
        },
        "batch_size": 100,
        "retry_policy": "exponential",
        "incremental_fetch": {
            "enabled": False,
            "state_file": ".incremental_state.json",  # Relative path for state
        },
    }

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        super().__init__(name, config)
        self._incremental_state: dict[str, Any] = {}
        self._initialize_state()

    def _initialize_state(self) -> None:
        """Load incremental fetch state if enabled."""
        inc_config = self.config.get("incremental_fetch", self.default_config["incremental_fetch"])
        if inc_config.get("enabled"):
            state_file = inc_config.get("state_file")
            if state_file:
                self._incremental_state = _load_incremental_state(state_file)

    def _fetch_from_http(
        self, base_url: str, endpoints: list[str], credentials: dict[str, str], timeout_seconds: int
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch data from HTTP endpoints with pagination, caching, and incremental support."""
        result: dict[str, list[dict[str, Any]]] = {}
        headers = build_http_headers(credentials)

        inc_config = cast(dict[str, Any], self.config.get("incremental_fetch", {}))
        default_incremental_config = cast(dict[str, Any], self.default_config["incremental_fetch"])
        if not inc_config:
            inc_config = default_incremental_config
        use_incremental = inc_config.get("enabled", False)

        with httpx.Client(timeout=timeout_seconds) as client:
            for endpoint_key, endpoint_path in enumerate(endpoints):
                self.logger.info(f"Fetching from HTTP endpoint: {endpoint_path}")

                full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
                records: list[dict[str, Any]] = []

                # Build headers with incremental support
                request_headers = headers.copy()
                if use_incremental:
                    etag = self._incremental_state.get(f"etag_{endpoint_key}")
                    if etag:
                        request_headers["If-None-Match"] = etag

                try:
                    response = client.get(full_url, headers=request_headers)

                    if response.status_code == 304:
                        # Not modified - use cached data
                        self.logger.info(f"Cache hit (304) for {endpoint_path}")
                        continue

                    response.raise_for_status()

                    # Store ETag for next time
                    if use_incremental and "etag" in response.headers:
                        self._incremental_state[f"etag_{endpoint_key}"] = response.headers["etag"]

                    payload = response.json()

                    # Parse response (support both list and Drupal envelope)
                    if isinstance(payload, list):
                        records = [item for item in payload if isinstance(item, dict)]
                    elif isinstance(payload, dict):
                        list_payload = payload.get("list")
                        if isinstance(list_payload, list):
                            records = [item for item in list_payload if isinstance(item, dict)]
                        else:
                            raise ValueError(f"Unexpected response format from {full_url}")
                    else:
                        raise ValueError(f"Unexpected response format from {full_url}")

                    # Guess dataset name from endpoint
                    dataset_name = self._infer_dataset_name(endpoint_path)
                    result[dataset_name] = records

                    self.logger.info(f"Fetched {len(records)} records from {endpoint_path}")

                except httpx.HTTPError as e:
                    self._handle_error("http_fetch", e)
                    raise

        # Persist state if incremental fetching is enabled
        if use_incremental:
            state_file = inc_config.get("state_file")
            if state_file:
                self._incremental_state["last_fetch"] = datetime.utcnow().isoformat()
                _save_incremental_state(self._incremental_state, state_file)

        return result

    def _infer_dataset_name(self, endpoint_path: str) -> str:
        """Infer dataset name from endpoint path."""
        path_lower = endpoint_path.lower()
        if "user" in path_lower:
            return "actors"
        if "project" in path_lower:
            return "projects"
        if "issue" in path_lower:
            return "issues"
        # Default: use last path segment
        return path_lower.split("/")[-1].split("?")[0]

    def _fetch_from_files(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch data from local files (original implementation)."""
        fetch_config = cast(dict[str, Any], self.config.get("fetch_config", {}))
        if not fetch_config:
            fetch_config = cast(dict[str, Any], self.default_config["fetch_config"])
        files = cast(
            dict[str, Any],
            fetch_config.get(
                "files",
                cast(dict[str, Any], self.default_config["fetch_config"])["files"],
            ),
        )

        result: dict[str, list[dict[str, Any]]] = {}
        for key, relative_path in files.items():
            path = Path(str(relative_path))
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            records: list[dict[str, Any]]
            if isinstance(payload, list):
                records = [item for item in payload if isinstance(item, dict)]
            elif isinstance(payload, dict):
                list_payload = payload.get("list")
                if isinstance(list_payload, list):
                    records = [item for item in list_payload if isinstance(item, dict)]
                else:
                    raise ValueError(f"Expected a list or Drupal envelope in '{path}'.")
            else:
                raise ValueError(f"Expected a list or Drupal envelope in '{path}'.")

            result[str(key)] = records

        return result

    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        self.before_fetch()
        try:
            fetch_config = cast(dict[str, Any], self.config.get("fetch_config", {}))
            if not fetch_config:
                fetch_config = cast(dict[str, Any], self.default_config["fetch_config"])

            # Check if we should use HTTP or files
            use_http = fetch_config.get("use_http", False)

            if use_http:
                # Get credentials from environment
                credentials = get_provider_credentials(self.provider_name)
                base_url = fetch_config.get(
                    "base_url",
                    cast(dict[str, Any], self.default_config["fetch_config"])["base_url"],
                )
                endpoints = fetch_config.get(
                    "endpoints",
                    cast(dict[str, Any], self.default_config["fetch_config"])["endpoints"],
                )
                timeout = fetch_config.get("timeout_seconds", 30)

                return self._fetch_from_http(base_url, endpoints, credentials, timeout)
            else:
                # Use file-based fetch (default for testing)
                return self._fetch_from_files()
        except Exception as exc:
            self._handle_error("fetch", exc)
            raise

    def schema(self) -> dict[str, type[BaseModel]]:
        """Return the canonical entity models produced by this provider."""
        return {
            "actors": Actor,
            "projects": Project,
            "issues": Issue,
        }

    def normalize(self, raw_data: dict[str, list[dict[str, Any]]]) -> dict[str, list[BaseModel]]:
        errors: list[ValidationError] = []
        normalized: dict[str, list[BaseModel]] = {}
        source = self.config.get("source", "drupal")

        for dataset_name, model in self.schema().items():
            rows = raw_data.get(dataset_name, [])
            if dataset_name not in self.record_models:
                continue

            mapped_rows = [self._map_record(dataset_name, row, source) for row in rows]

            try:
                normalized[dataset_name] = [
                    model.model_validate(mapped_row) for mapped_row in mapped_rows
                ]
            except ValidationError as exc:
                errors.append(exc)

        if errors:
            aggregate = aggregate_validation_errors("DrupalNormalizationError", errors)
            self._handle_error("normalize", aggregate)
            raise aggregate

        self.after_normalize(normalized)
        return normalized

    def _map_record(self, dataset: str, row: dict[str, Any], source: str) -> dict[str, Any]:
        record_model = self.record_models.get(dataset)
        if record_model is None:
            return row

        parsed = record_model.model_validate(row)
        return parsed.to_entity(source)
