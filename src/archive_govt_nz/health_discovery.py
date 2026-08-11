"""Deterministic normalization and reconciliation for health metadata discovery."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import cast


def _identifier(record: Mapping[str, object]) -> str:
    value = record.get("id")
    if not isinstance(value, str) or not value:
        error = "invalid_dataset_id"
        raise ValueError(error)
    return value


def _canonical(record: Mapping[str, object]) -> bytes:
    return json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _result_signature(result: Mapping[str, object]) -> tuple[int, tuple[str, ...]]:
    count = result.get("count")
    rows = result.get("results")
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or not isinstance(rows, list)
    ):
        error = "invalid_action_result"
        raise TypeError(error)
    typed_rows = cast("list[object]", rows)
    identifiers = tuple(
        sorted(
            _identifier(cast("Mapping[str, object]", item))
            for item in typed_rows
            if isinstance(item, Mapping)
        )
    )
    if len(identifiers) != len(typed_rows):
        error = "invalid_action_result"
        raise TypeError(error)
    return count, identifiers


def reconcile_transport_results(
    post: Mapping[str, object] | None,
    get: Mapping[str, object],
) -> str:
    """Classify normalized POST/GET parity without hiding method divergence."""
    get_signature = _result_signature(get)
    if post is None:
        return "get-fallback"
    return "equivalent" if _result_signature(post) == get_signature else "conflict"


def classify_dataset(
    record: Mapping[str, object], *, scopes: Sequence[str]
) -> dict[str, object]:
    """Classify metadata conservatively without granting payload eligibility."""
    licence = record.get("license_id") or record.get("license_title")
    organization = record.get("organization")
    organization_id = None
    if isinstance(organization, Mapping):
        organization_id = cast("Mapping[str, object]", organization).get("id")
    resources = record.get("resources")
    resource_count = (
        len(cast("list[object]", resources)) if isinstance(resources, list) else 0
    )
    return {
        "dataset_id": _identifier(record),
        "name": record.get("name"),
        "title": record.get("title"),
        "organization_id": organization_id,
        "licence": licence,
        "metadata_modified": record.get("metadata_modified"),
        "resource_count": resource_count,
        "scopes": sorted(set(scopes)),
        "classification": (
            "candidate-metadata-only" if licence else "decision-required"
        ),
        "health_relevance": "matched-versioned-health-scope",
        "sensitivity": "decision-required",
        "payload_eligible": False,
    }


def normalize_scoped_records(
    groups: Mapping[str, Sequence[Mapping[str, object]]],
) -> list[dict[str, object]]:
    """Deduplicate complete records and reject cross-query metadata conflicts."""
    records: dict[str, Mapping[str, object]] = {}
    memberships: dict[str, list[str]] = {}
    for scope, rows in groups.items():
        for row in rows:
            identifier = _identifier(row)
            existing = records.get(identifier)
            if existing is not None and _canonical(existing) != _canonical(row):
                error = "conflicting_dataset_metadata"
                raise ValueError(error)
            records[identifier] = row
            memberships.setdefault(identifier, []).append(scope)
    return [
        classify_dataset(records[identifier], scopes=memberships[identifier])
        for identifier in sorted(records)
    ]


def reconcile_rerun(
    previous: Sequence[Mapping[str, object]],
    current: Sequence[Mapping[str, object]],
) -> dict[str, list[str]]:
    """Return deterministic change states for repeated metadata observations."""
    before = {_identifier(item): _canonical(item) for item in previous}
    after = {_identifier(item): _canonical(item) for item in current}
    shared = before.keys() & after.keys()
    return {
        "changed": sorted(item for item in shared if before[item] != after[item]),
        "new": sorted(after.keys() - before.keys()),
        "unchanged": sorted(item for item in shared if before[item] == after[item]),
        "withdrawn": sorted(before.keys() - after.keys()),
    }
