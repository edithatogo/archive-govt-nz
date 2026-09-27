"""Bounded heartbeat receipts for the metadata-only scheduled health lane."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

SCHEMA_VERSION = "archive-govt-nz.health-discovery-heartbeat/v1"
MAX_MANIFEST_BYTES = 64 * 1024 * 1024
_OUTCOMES = frozenset({"success", "failure", "cancelled", "skipped"})
_DRIFT_FIELDS = ("new", "changed", "unchanged", "withdrawn")


def _base(workflow_outcome: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "workflow_outcome": (
            workflow_outcome if workflow_outcome in _OUTCOMES else "unknown"
        ),
        "discovery_state": "missing",
        "manifest_sha256": None,
        "dataset_count": None,
        "metadata_drift": {"state": "not_available"},
        "capture_state": "not_run",
        "silver_normalization_state": "not_run",
        "validation_state": "not_run",
        "publication_state": "not_run",
    }


def build_discovery_heartbeat(
    manifest_bytes: bytes | None, workflow_outcome: str
) -> dict[str, object]:
    """Summarize a scheduled discovery receipt without inferring later stages."""
    receipt = _base(workflow_outcome)
    if manifest_bytes is not None and len(manifest_bytes) > MAX_MANIFEST_BYTES:
        receipt["discovery_state"] = "invalid"
    elif manifest_bytes is not None:
        receipt["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
        try:
            document = json.loads(manifest_bytes)
        except UnicodeDecodeError, json.JSONDecodeError, RecursionError:
            receipt["discovery_state"] = "invalid"
        else:
            _apply_manifest(receipt, document)
    return receipt


def _apply_manifest(receipt: dict[str, object], document: object) -> None:
    if not isinstance(document, dict):
        receipt["discovery_state"] = "invalid"
        return

    schema_version = document.get("schema_version")
    status = document.get("status")
    if schema_version != "archive-govt-nz.health-discovery/v1" or status not in {
        "observed",
        "unavailable",
    }:
        receipt["discovery_state"] = "invalid"
        return
    if status == "unavailable":
        receipt["discovery_state"] = "unavailable"
        return

    count = document.get("dataset_count")
    fingerprints = document.get("metadata_fingerprints")
    rerun = document.get("rerun")
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or count < 0
        or not isinstance(fingerprints, dict)
        or not isinstance(rerun, dict)
        or any(
            not isinstance(rerun.get(field), list)
            or any(not isinstance(item, str) for item in rerun[field])
            for field in _DRIFT_FIELDS
        )
    ):
        receipt["discovery_state"] = "invalid"
        return

    receipt["discovery_state"] = "observed"
    receipt["dataset_count"] = count
    receipt["metadata_drift"] = {
        "state": "reported",
        **{field: len(cast("list[Any]", rerun[field])) for field in _DRIFT_FIELDS},
    }


def main() -> int:
    """Write a compact heartbeat for scheduled health discovery."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workflow-outcome", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.manifest.open("rb") as stream:
            manifest_bytes = stream.read(MAX_MANIFEST_BYTES + 1)
        unreadable = False
    except FileNotFoundError:
        manifest_bytes = None
        unreadable = False
    except OSError:
        manifest_bytes = None
        unreadable = True
    receipt = build_discovery_heartbeat(manifest_bytes, args.workflow_outcome)
    if unreadable:
        receipt["discovery_state"] = "unreadable"
    payload = (
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
