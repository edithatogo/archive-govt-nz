"""Bounded, reproducible scope definitions for health discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

HEALTH_SCOPE_SCHEMA = "archive-govt-nz.health-scope/v1"
CATALOGUE_URL = "https://catalogue.data.govt.nz"

DEFAULT_SCOPES: tuple[dict[str, object], ...] = (
    {"id": "text-health", "q": "health", "sort": "score desc, metadata_modified desc"},
    {
        "id": "group-health",
        "groups": "health",
        "sort": "score desc, metadata_modified desc",
    },
)


def scope_manifest(*, observed_at: str, page_size: int = 100) -> dict[str, object]:
    """Return the stable query contract; it never includes resource payloads."""
    if page_size < 1:
        raise ValueError
    return {
        "schema_version": HEALTH_SCOPE_SCHEMA,
        "catalogue": CATALOGUE_URL,
        "observed_at": observed_at,
        "mode": "metadata_only",
        "page_size": page_size,
        "max_pages_per_scope": 1000,
        "scopes": [dict(scope) for scope in DEFAULT_SCOPES],
        "organisation_facets": {
            "enabled": True,
            "include": "all matching organisations",
        },
        "payload_capture": "prohibited",
    }


def deduplicate_dataset_ids(groups: Mapping[str, object]) -> tuple[str, ...]:
    """Stable first-seen union of IDs returned by independent CKAN scopes."""
    result: list[str] = []
    seen: set[str] = set()
    for value in groups.values():
        if not isinstance(value, (list, tuple)):
            raise TypeError
        for identifier in cast("list[object] | tuple[object, ...]", value):
            if not isinstance(identifier, str) or not identifier:
                raise ValueError
            if identifier not in seen:
                seen.add(identifier)
                result.append(identifier)
    return tuple(result)
