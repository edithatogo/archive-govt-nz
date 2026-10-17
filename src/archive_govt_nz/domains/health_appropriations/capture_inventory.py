"""Observation-preserving inventory across independently captured source cohorts.

This projection pins metadata inputs. It neither rewrites the original census
nor replays CAS/WARC fixity, evaluates rights, or admits analytical measures.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, NoReturn

_SHA256_LENGTH = 64


@dataclass(frozen=True)
class InventorySnapshot:
    """Exact serialized evidence and its stable logical name."""

    name: str
    data: bytes


@dataclass(frozen=True)
class CaptureSnapshot:
    """A capture receipt with its original request, when that binding exists."""

    manifest: InventorySnapshot
    request: InventorySnapshot | None = None


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fail(code: str) -> NoReturn:
    raise ValueError(code)


def _document(snapshot: InventorySnapshot, schema: str) -> dict[str, Any]:
    doc = json.loads(snapshot.data)
    if not isinstance(doc, dict) or doc.get("schema_version") != schema:
        _fail("inventory_input_schema_invalid")
    return doc


def _rows(doc: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = doc.get(key)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        _fail("inventory_rows_invalid")
    seen: set[str] = set()
    for row in rows:
        identity = row.get("source_id")
        if not isinstance(identity, str) or not identity or identity in seen:
            _fail("inventory_source_id_missing_or_duplicate")
        seen.add(identity)
        url = row.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            _fail("inventory_source_url_invalid")
    return rows


def _digest(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != _SHA256_LENGTH
        or any(c not in "0123456789abcdef" for c in value)
    ):
        _fail("capture_digest_invalid")
    return value


def _register(snapshot: InventorySnapshot, inputs: dict[str, dict[str, Any]]) -> None:
    if not snapshot.name:
        _fail("inventory_input_name_missing")
    pin = {"sha256": _sha(snapshot.data), "bytes": len(snapshot.data)}
    if snapshot.name in inputs and inputs[snapshot.name] != pin:
        _fail("input_name_conflict")
    inputs[snapshot.name] = pin


def _request_binding(capture: CaptureSnapshot, manifest: dict[str, Any]) -> str:
    context = manifest.get("capture_context", {})
    if not isinstance(context, dict):
        _fail("capture_context_invalid")
    if context.get("contract") != "health-capture-resume/v1":
        return "not_verified_legacy_request_context_unavailable"
    if capture.request is None:
        _fail("capture_request_missing")
    if context.get("census_sha256") != _sha(capture.request.data):
        _fail("capture_request_hash_mismatch")
    return "capture_time_request_hash_verified"


def _capture_request_rows(
    capture: CaptureSnapshot,
    manifest: dict[str, Any],
    inputs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]] | None:
    request_rows = None
    if capture.request is not None:
        _register(capture.request, inputs)
        # Early capture requests were {cutoff, records}, not versioned censuses.
        # Accept that original request shape only after its exact hash binds.
        request_doc = json.loads(capture.request.data)
        if not isinstance(request_doc, dict) or request_doc.get(
            "schema_version"
        ) not in (None, "archive-govt-nz.health-source-census/v1"):
            _fail("capture_request_shape_invalid")
        request_rows = _rows(request_doc, "records")
        if manifest.get("cutoff") != request_doc.get("cutoff"):
            _fail("capture_request_cutoff_mismatch")
    return request_rows


def _add_capture(
    capture: CaptureSnapshot,
    resources: dict[str, dict[str, Any]],
    identities: set[tuple[str, str]],
    inputs: dict[str, dict[str, Any]],
) -> None:
    _register(capture.manifest, inputs)
    manifest = _document(capture.manifest, "archive-govt-nz.health-capture-manifest/v1")
    binding = _request_binding(capture, manifest)
    request_rows = _capture_request_rows(capture, manifest, inputs)
    for row in _rows(manifest, "results"):
        identity = (row["source_id"], row["url"])
        if identity not in identities:
            _fail("capture_source_not_in_census")
        if request_rows is not None:
            if identity not in {(r["source_id"], r["url"]) for r in request_rows}:
                _fail("capture_source_not_in_request")
            if row.get("request_url_sha256") != _sha(row["url"].encode()):
                _fail("capture_request_url_mismatch")
        resource = resources[row["url"]]
        if row.get("state") == "captured":
            digest = _digest(row.get("sha256"))
            size = row.get("bytes")
            if type(size) is not int or size < 0:
                _fail("capture_size_invalid")
            resource["versions"].add(digest)
            resource["recorded_captured"] = True
        resource["capture_observations"].append(
            {
                "manifest": capture.manifest.name,
                "request": capture.request.name if capture.request else None,
                "request_binding": binding,
                "record": row,
            }
        )


def _add_census(
    census: InventorySnapshot,
    resources: dict[str, dict[str, Any]],
    identities: set[tuple[str, str]],
    inputs: dict[str, dict[str, Any]],
) -> None:
    _register(census, inputs)
    doc = _document(census, "archive-govt-nz.health-source-census/v1")
    rows = _rows(doc, "records")
    if doc.get("record_count") != len(rows):
        _fail("inventory_census_count_mismatch")
    for row in rows:
        url = row["url"]
        identities.add((row["source_id"], url))
        resource = resources.setdefault(
            url,
            {
                "url": url,
                "source_ids": set(),
                "versions": set(),
                "recorded_captured": False,
                "census_observations": [],
                "capture_observations": [],
                "fixity_state": "not_replayed_by_inventory",
                "rights_state": "not_evaluated_by_inventory",
            },
        )
        resource["source_ids"].add(row["source_id"])
        digest = row.get("object_sha256")
        if digest is not None:
            resource["versions"].add(_digest(digest))
        if row.get("disposition") == "captured":
            _digest(digest)
            resource["recorded_captured"] = True
        resource["census_observations"].append({"census": census.name, "record": row})


def build_capture_inventory(
    censuses: tuple[InventorySnapshot, ...],
    captures: tuple[CaptureSnapshot, ...],
) -> dict[str, Any]:
    """Group exact URLs, retaining every edition/alias/version observation."""
    inputs: dict[str, dict[str, Any]] = {}
    resources: dict[str, dict[str, Any]] = {}
    identities: set[tuple[str, str]] = set()
    if len({c.name for c in censuses}) != len(censuses):
        # Still diagnose conflicting bytes before rejecting an exact duplicate.
        for census in censuses:
            _register(census, inputs)
        _fail("inventory_census_duplicate")
    if len({c.manifest.name for c in captures}) != len(captures):
        _fail("inventory_capture_duplicate")
    for census in sorted(censuses, key=lambda c: c.name):
        _add_census(census, resources, identities, inputs)
    for capture in sorted(captures, key=lambda c: c.manifest.name):
        _add_capture(capture, resources, identities, inputs)
    for resource in resources.values():
        resource["source_ids"] = sorted(resource["source_ids"])
        resource["versions"] = sorted(resource["versions"])
    return {
        "schema_version": "archive-govt-nz.health-capture-inventory/v1",
        "scope": "supplied_cohorts_only_not_whole_corpus_or_publication_completeness",
        "inputs": dict(sorted(inputs.items())),
        "summary": {
            "resource_count": len(resources),
            "recorded_captured_resource_count": sum(
                r["recorded_captured"] for r in resources.values()
            ),
            "census_observation_count": sum(
                len(r["census_observations"]) for r in resources.values()
            ),
            "capture_observation_count": sum(
                len(r["capture_observations"]) for r in resources.values()
            ),
        },
        "resources": [resources[url] for url in sorted(resources)],
    }
