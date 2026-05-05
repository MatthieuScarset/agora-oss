from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from packages.providers.base import DataSourceProvider
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


class DrupalActorRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

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


class DrupalProjectRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

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


class DrupalIssueRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

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
    record_models: dict[str, type[BaseModel]] = {
        "actors": DrupalActorRecord,
        "projects": DrupalProjectRecord,
        "issues": DrupalIssueRecord,
    }
    default_config = {
        "source": "drupal",
        "fetch_config": {
            "base_url": "https://drupal.org",
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
        },
        "batch_size": 100,
        "retry_policy": "exponential",
    }

    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        self.before_fetch()
        try:
            fetch_config = self.config.get("fetch_config", self.default_config["fetch_config"])
            files = fetch_config.get(
                "files",
                self.default_config["fetch_config"]["files"],
            )

            result: dict[str, list[dict[str, Any]]] = {}
            for key, relative_path in files.items():
                path = Path(str(relative_path))
                with path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                records: list[dict[str, Any]]
                if isinstance(payload, list):
                    records = [item for item in payload if isinstance(item, dict)]
                elif isinstance(payload, dict) and isinstance(payload.get("list"), list):
                    records = [item for item in payload["list"] if isinstance(item, dict)]
                else:
                    raise ValueError(f"Expected a list or Drupal envelope in '{path}'.")

                result[str(key)] = records

            return result
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
                validator = TypeAdapter(list[model])
                normalized[dataset_name] = validator.validate_python(mapped_rows)
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

        parsed = TypeAdapter(record_model).validate_python(row)
        return parsed.to_entity(source)
