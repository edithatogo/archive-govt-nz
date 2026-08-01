"""Fail-closed resolution of secure source alternatives before tombstoning."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003
from dataclasses import dataclass
from typing import cast
from urllib.parse import urlencode, urlparse, urlunparse


@dataclass(frozen=True, slots=True)
class SourceResolution:
    """Auditable secure candidates and terminal fallback state."""

    resource_id: str
    candidates: tuple[str, ...]
    state: str
    reason: str


def derive_ckan_api_candidates(resource: Mapping[str, object]) -> tuple[str, ...]:
    """Return read-only CKAN API endpoints for metadata/DataStore diagnostics.

    These endpoints are deliberately separate from payload candidates: a reachable
    ``package_show`` or ``datastore_search`` response never makes the original
    resource eligible for capture.  They provide evidence that CKAN metadata or a
    tabular DataStore representation is available when a download URL is not.
    """
    dataset_id = resource.get("dataset_id")
    resource_id = resource.get("resource_id")
    candidates: list[str] = []
    if isinstance(dataset_id, str) and dataset_id:
        candidates.append(
            "https://catalogue.data.govt.nz/api/3/action/package_show?"
            + urlencode({"id": dataset_id})
        )
    if isinstance(resource_id, str) and resource_id:
        candidates.append(
            "https://catalogue.data.govt.nz/api/3/action/datastore_search?"
            + urlencode({"resource_id": resource_id, "limit": 0})
        )
    return tuple(candidates)


def resolve_secure_sources(resource: Mapping[str, object]) -> SourceResolution:
    """Order explicit secure alternatives and never promote HTTP as eligible."""
    resource_id = str(resource.get("resource_id", ""))
    raw_values: list[object] = [resource.get("source_url")]
    alternatives = resource.get("secure_alternatives", ())
    if isinstance(alternatives, (list, tuple)):
        typed_alternatives = cast("list[object] | tuple[object, ...]", alternatives)
        raw_values.extend(list(typed_alternatives))
    candidates: list[str] = []
    for value in raw_values:
        if not isinstance(value, str):
            continue
        parsed = urlparse(value)
        if parsed.scheme == "https" and parsed.netloc and value not in candidates:
            candidates.append(value)
        elif parsed.scheme == "http" and parsed.netloc:
            upgraded = urlunparse(
                (
                    "https",
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
            if upgraded not in candidates:
                candidates.append(upgraded)
    if candidates:
        return SourceResolution(
            resource_id,
            tuple(candidates),
            "secure-candidates",
            "secure alternatives available for bounded probing",
        )
    return SourceResolution(
        resource_id,
        (),
        "tombstone-required",
        "no authoritative HTTPS source alternative",
    )
