from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pydantic_core import InitErrorDetails


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_optional_text(value: Any) -> str | None:
    text = normalize_text(value)
    return text or None


def normalize_lower(value: Any) -> str:
    return normalize_text(value).lower()


def normalize_url(value: Any) -> str | None:
    text = normalize_optional_text(value)
    if text is None:
        return None

    if text.startswith("http://") or text.startswith("https://"):
        return text.rstrip("/")

    raise ValueError("URL must start with http:// or https://")


def parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    if isinstance(value, (int, float)):
        if value < 0:
            raise ValueError("timestamp must be >= 0")
        return datetime.fromtimestamp(value, tz=UTC)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("datetime value cannot be empty")

        if text.isdigit():
            return datetime.fromtimestamp(int(text), tz=UTC)

        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid datetime format") from exc
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    raise ValueError("unsupported datetime value")


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("must be a string or list")

    normalized = [normalize_text(item) for item in items if normalize_text(item)]
    return sorted(set(normalized))


class DrupalRole(StrEnum):
    MAINTAINER = "maintainer"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"


class BaseEntity(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        text = normalize_text(value)
        if not text:
            raise ValueError("id cannot be empty")
        return text

    @field_validator("source", mode="before")
    @classmethod
    def normalize_source(cls, value: Any) -> str:
        text = normalize_lower(value)
        if not text:
            raise ValueError("source cannot be empty")
        return text

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def normalize_datetimes(cls, value: Any) -> datetime:
        return parse_datetime(value)


class Actor(BaseEntity):
    name: str
    email: str | None = None
    picture_url: str | None = None
    status: int = Field(ge=0)
    roles: list[DrupalRole] = Field(default_factory=list)
    maintained_projects: list[str] = Field(default_factory=list)
    contributed_projects: list[str] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Any) -> str:
        text = normalize_text(value)
        if not text:
            raise ValueError("name cannot be empty")
        return text

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: Any) -> str | None:
        text = normalize_optional_text(value)
        return text.lower() if text else None

    @field_validator("picture_url", mode="before")
    @classmethod
    def normalize_picture_url(cls, value: Any) -> str | None:
        return normalize_url(value)

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles(cls, value: Any) -> list[DrupalRole]:
        role_aliases = {
            "maintainer": DrupalRole.MAINTAINER,
            "contributor": DrupalRole.CONTRIBUTOR,
            "reviewer": DrupalRole.REVIEWER,
        }
        normalized_roles = normalize_string_list(value)
        roles: list[DrupalRole] = []
        for role in normalized_roles:
            canonical = role_aliases.get(role.lower())
            if canonical is None:
                raise ValueError(f"unknown drupal role: {role}")
            roles.append(canonical)
        return sorted(set(roles), key=lambda item: item.value)

    @field_validator("maintained_projects", "contributed_projects", mode="before")
    @classmethod
    def normalize_projects(cls, value: Any) -> list[str]:
        return normalize_string_list(value)


class Project(BaseEntity):
    title: str
    body: str | None = None
    status: int = Field(ge=0)
    project_type: str
    maintainer_uid: str
    parent_id: str | None = None
    dependency_ids: list[str] = Field(default_factory=list)
    license_title: str | None = None
    license_url: str | None = None
    components: list[str] = Field(default_factory=list)

    @field_validator("title", "project_type", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any) -> str:
        text = normalize_text(value)
        if not text:
            raise ValueError("field cannot be empty")
        return text

    @field_validator("body", mode="before")
    @classmethod
    def normalize_body(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("maintainer_uid", "parent_id", mode="before")
    @classmethod
    def normalize_optional_ids(cls, value: Any) -> str | None:
        text = normalize_optional_text(value)
        return text

    @field_validator("maintainer_uid")
    @classmethod
    def validate_maintainer_uid(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("maintainer_uid is required")
        return value

    @field_validator("dependency_ids", "components", mode="before")
    @classmethod
    def normalize_multi_values(cls, value: Any) -> list[str]:
        return normalize_string_list(value)

    @field_validator("license_url", mode="before")
    @classmethod
    def normalize_license_url(cls, value: Any) -> str | None:
        return normalize_url(value)

    @field_validator("license_title", mode="before")
    @classmethod
    def normalize_license_title(cls, value: Any) -> str | None:
        return normalize_optional_text(value)


class Issue(BaseEntity):
    title: str
    description: str | None = None
    status: str
    issue_type: str
    project_id: str
    reporter_uid: str
    reporter_name: str | None = None
    assigned_to_uid: str | None = None
    closed_at: datetime | None = None

    @field_validator("title", "status", "issue_type", "project_id", "reporter_uid", mode="before")
    @classmethod
    def normalize_required(cls, value: Any) -> str:
        text = normalize_text(value)
        if not text:
            raise ValueError("field cannot be empty")
        return text

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: Any) -> str:
        normalized = normalize_lower(value)
        if normalized not in {"open", "closed"}:
            raise ValueError("status must be open or closed")
        return normalized

    @field_validator("issue_type", mode="before")
    @classmethod
    def normalize_issue_type(cls, value: Any) -> str:
        normalized = normalize_lower(value)
        if normalized not in {"bug", "feature", "task", "support"}:
            raise ValueError("issue_type must be bug|feature|task|support")
        return normalized

    @field_validator("description", "reporter_name", "assigned_to_uid", mode="before")
    @classmethod
    def normalize_optionals(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("closed_at", mode="before")
    @classmethod
    def normalize_closed_at(cls, value: Any) -> datetime | None:
        if value is None or value == "":
            return None
        return parse_datetime(value)


class Author(BaseEntity):
    name: str
    url: str | None = None
    description: str | None = None
    profile_link: str | None = None
    slug: str
    avatar_urls: dict[str, str] = Field(default_factory=dict)

    @field_validator("name", "slug", mode="before")
    @classmethod
    def normalize_non_empty(cls, value: Any) -> str:
        text = normalize_text(value)
        if not text:
            raise ValueError("field cannot be empty")
        return text

    @field_validator("url", "profile_link", mode="before")
    @classmethod
    def normalize_links(cls, value: Any) -> str | None:
        return normalize_url(value)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: Any) -> str | None:
        return normalize_optional_text(value)


class Plugin(BaseEntity):
    slug: str
    name: str
    description: str | None = None
    status: str
    version: str | None = None
    added_at: datetime
    last_updated_at: datetime
    author_slug: str
    requires_plugins: list[str] = Field(default_factory=list)
    homepage: str | None = None
    requires_wp: str | None = None
    requires_php: str | None = None
    tested_wp: str | None = None

    @field_validator("slug", "name", "status", "author_slug", mode="before")
    @classmethod
    def normalize_required(cls, value: Any) -> str:
        text = normalize_text(value)
        if not text:
            raise ValueError("field cannot be empty")
        return text

    @field_validator(
        "description", "version", "requires_wp", "requires_php", "tested_wp", mode="before"
    )
    @classmethod
    def normalize_optional_strings(cls, value: Any) -> str | None:
        return normalize_optional_text(value)

    @field_validator("requires_plugins", mode="before")
    @classmethod
    def normalize_requires_plugins(cls, value: Any) -> list[str]:
        return normalize_string_list(value)

    @field_validator("homepage", mode="before")
    @classmethod
    def normalize_homepage(cls, value: Any) -> str | None:
        return normalize_url(value)

    @field_validator("added_at", "last_updated_at", mode="before")
    @classmethod
    def normalize_dates(cls, value: Any) -> datetime:
        return parse_datetime(value)


def aggregate_validation_errors(title: str, errors: list[ValidationError]) -> ValidationError:
    line_errors: list[InitErrorDetails] = []
    for error in errors:
        for line_error in error.errors(include_url=False):
            line_errors.append(cast(InitErrorDetails, dict(line_error)))

    return ValidationError.from_exception_data(title, line_errors=line_errors)
