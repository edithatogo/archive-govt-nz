"""Bounded direct-source receipt joins; not payload or normalization approval."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, cast

MAX_BYTES = 4 * 1024 * 1024
MAX_ROWS = 1000
MAX_TEXT = 2048
MAX_COUNT = 1_000_000_000
MAX_TOTAL_BYTES = 16 * 1024 * 1024
CONTROL = 32
SCHEMA = "archive-govt-nz.health-direct-targets/v1"
PROFILES = {
    "budget": "archive-govt-nz.health-budget-extraction/v1",
    "befu": "archive-govt-nz.health-forecast-extraction/v1",
    "hyefu": "archive-govt-nz.health-forecast-extraction/v1",
    "fiscal": "archive-govt-nz.health-historical-extraction/v1",
    "ministry": "archive-govt-nz.health-moh-indicator-extraction/v1",
    "pharmac": "archive-govt-nz.health-pharmac-extraction/v1",
    "vote_health": None,
}
CAPTURE_STATES = {
    "captured",
    "unchanged",
    "unavailable",
    "withdrawn",
    "restricted",
    "corrupt",
    "retryable",
    "superseded",
    "duplicate",
    "out_of_scope",
}


@dataclass(frozen=True)
class Pinned:
    """Immutable supplied metadata bytes and an independently chosen digest."""

    payload: bytes
    sha256: str


def _require(condition: object) -> None:
    if not condition:
        message = "direct_coverage_contract"
        raise ValueError(message)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _load(item: Pinned) -> dict[str, Any]:
    _require(type(item.payload) is bytes and len(item.payload) <= MAX_BYTES)
    _require(hashlib.sha256(item.payload).hexdigest() == item.sha256)
    result = json.loads(
        item.payload.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_nonfinite,
    )
    _require(isinstance(result, dict))
    return result


def _nonfinite(_value: str) -> None:
    message = "direct_coverage_contract"
    raise ValueError(message)


def _text(value: object) -> None:
    _require(isinstance(value, str) and 0 < len(value) <= MAX_TEXT)
    _require(not any(ord(char) < CONTROL for char in cast("str", value)))


def _digest(value: object) -> None:
    _require(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value))


def _index(rows: object, key: str) -> dict[str, Any]:
    _require(isinstance(rows, list) and len(rows) <= MAX_ROWS)
    result = {}
    for row in cast("list[dict[str, Any]]", rows):
        _text(row[key])
        _require(row[key] not in result)
        result[row[key]] = row
    return result


def _capture(row: dict[str, Any], target: dict[str, Any]) -> None:
    _require(row["url"] == target["url"])
    _require(row["state"] in CAPTURE_STATES)
    digest = row.get("sha256")
    if digest is not None:
        _digest(digest)
        _require(row["object_id"] == "sha256:" + digest)
        _require(type(row["bytes"]) is int and row["bytes"] > 0)
    else:
        _require(row.get("object_id") is None)
    if row["state"] in {"captured", "unchanged", "duplicate"}:
        _require(digest is not None)
    rights = row.get("rights")
    if rights is not None:
        _require(isinstance(rights, dict))
        _text(rights["state"])
        for key in ("license", "evidence"):
            if rights.get(key) is not None:
                _text(rights[key])


def _extraction(
    item: Pinned, target: dict[str, Any], capture: dict[str, Any] | None
) -> dict[str, Any]:
    data = _load(item)
    _require(capture is not None and capture.get("sha256") is not None)
    capture = cast("dict[str, Any]", capture)
    _require(PROFILES[target["family"]] is not None)
    _require(data["schema_version"] == PROFILES[target["family"]])
    _require(data["source_object_sha256"] == capture["sha256"])
    _require(data["source_locator"] == target["url"])
    _require(
        target["vintage"] is not None and data["source_vintage"] == target["vintage"]
    )
    _require(data["status"] in {"passed", "partial", "failed"})
    _text(data["rights_state"])
    counts = data["counts"]
    _require(isinstance(counts, dict) and bool(counts))
    for key, value in counts.items():
        _text(key)
        _require(type(value) is int and 0 <= value <= MAX_COUNT)
    if data["status"] == "passed":
        _require(counts.get("rejected", 0) == 0)
    outputs = data["output_sha256"]
    _require(isinstance(outputs, dict) and bool(outputs))
    for key, digest in outputs.items():
        _text(key)
        _digest(digest)
    return data


def coverage_report(
    targets: Pinned, capture: Pinned, extractions: dict[str, Pinned]
) -> dict[str, Any]:
    """Join exact target/source/locator/vintage identities without I/O.

    Capture state may describe a later restriction of retained bytes; it does
    not erase an earlier extraction or inherit that extraction's rights state.
    Only supplied metadata fixity is verified. Unselected capture rows are not
    assessed except for source-ID uniqueness. No implicit URL normalization,
    vintage selection, supersession, rights decision or payload parsing occurs.
    """
    try:
        _require(len(extractions) <= MAX_ROWS)
        _require(
            sum(len(item.payload) for item in (targets, capture, *extractions.values()))
            <= MAX_TOTAL_BYTES
        )
        register, captures = _load(targets), _load(capture)
        _require(set(register) == {"schema_version", "cutoff", "targets"})
        _require(register["schema_version"] == SCHEMA)
        _require(
            captures["schema_version"] == "archive-govt-nz.health-capture-manifest/v1"
        )
        _text(register["cutoff"])
        _require(
            date.fromisoformat(register["cutoff"]).isoformat() == register["cutoff"]
        )
        _require(captures["cutoff"] == register["cutoff"])
        requested = _index(register["targets"], "target_id")
        _require(bool(requested))
        _index(register["targets"], "source_id")
        observed = _index(captures["results"], "source_id")
        _require(set(extractions) <= set(requested))
        rows = []
        for identity, target in sorted(requested.items()):
            _require(
                set(target)
                == {
                    "target_id",
                    "source_id",
                    "family",
                    "vintage",
                    "url",
                    "discovery_state",
                }
            )
            _require(target["family"] in PROFILES)
            _text(target["url"])
            _require(target["discovery_state"] in {"discovered", "not_enumerated"})
            if target["vintage"] is not None:
                _text(target["vintage"])
            observation = observed.get(target["source_id"])
            if observation is not None:
                _capture(observation, target)
            extraction = None
            if identity in extractions:
                extraction = _extraction(extractions[identity], target, observation)
            rows.append(
                {
                    **target,
                    "capture_state": observation["state"] if observation else None,
                    "capture_rights": observation.get("rights")
                    if observation
                    else None,
                    "source_object_sha256": observation.get("sha256")
                    if observation
                    else None,
                    "extraction_manifest_sha256": extractions[identity].sha256
                    if extraction
                    else None,
                    "extraction_state": extraction["status"] if extraction else None,
                    "extraction_rights_state": extraction["rights_state"]
                    if extraction
                    else None,
                    "counts": extraction["counts"] if extraction else None,
                    "gaps": (
                        ["capture_receipt_not_supplied"] if observation is None else []
                    )
                    + (
                        ["extraction_receipt_not_supplied"]
                        if extraction is None
                        else []
                    ),
                }
            )
        return {
            "schema_version": "archive-govt-nz.health-direct-coverage/v1",
            "target_register_sha256": targets.sha256,
            "capture_manifest_sha256": capture.sha256,
            "cutoff": register["cutoff"],
            "scope": "explicit_targets_only",
            "payload_verification": "not_performed",
            "normalization_approval": "not_granted",
            "publication_approval": "not_granted",
            "rows": rows,
        }
    except ValueError, KeyError, TypeError, AttributeError, RecursionError:
        message = "direct_coverage_contract"
        raise ValueError(message) from None
