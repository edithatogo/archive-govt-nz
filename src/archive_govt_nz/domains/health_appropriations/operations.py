"""Read-only operational state for the health-appropriations archive."""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pathlib import Path


class HealthAppropriationsStateError(ValueError):
    """Raised when local operational evidence is malformed or inconsistent."""


def _latest(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _latest_donor_manifest(root: Path) -> Path | None:
    matches = sorted(
        path
        for path in root.glob("donor-*.json")
        if re.fullmatch(r"donor-[0-9a-f]{7,40}\.json", path.name)
    )
    return matches[-1] if matches else None


def _load_manifest(
    path: Path | None, root: Path
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    if path is None:
        return None, None
    try:
        payload = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        value = json.loads(payload.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        message = f"invalid_manifest:{path.name}"
        raise HealthAppropriationsStateError(message) from error
    if not isinstance(value, dict) or not isinstance(value.get("schema_version"), str):
        message = f"invalid_manifest:{path.name}"
        raise HealthAppropriationsStateError(message)
    return cast("dict[str, Any]", value), {
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _nonnegative_integer(
    manifest: dict[str, Any] | None, field: str, manifest_name: str
) -> int:
    if manifest is None:
        return 0
    value = manifest.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = f"invalid_manifest:{manifest_name}"
        raise HealthAppropriationsStateError(message)
    return value


def inspect_archive_status(archive_root: Path) -> dict[str, object]:
    """Inspect stable layer manifests without mutating archive state."""
    manifests_root = archive_root / "manifests"
    donor_path = _latest_donor_manifest(manifests_root)
    capture_path = _latest(manifests_root, "official-capture-*-complete.json")
    silver_path = _latest(manifests_root, "silver-donor-*.json")
    gold_path = _latest(manifests_root, "gold-donor-*.json")
    candidate_path = _latest(archive_root / "candidates", "*/MANIFEST.json")

    donor, donor_provenance = _load_manifest(donor_path, archive_root)
    capture, capture_provenance = _load_manifest(capture_path, archive_root)
    silver, silver_provenance = _load_manifest(silver_path, archive_root)
    gold, gold_provenance = _load_manifest(gold_path, archive_root)
    candidate, candidate_provenance = _load_manifest(candidate_path, archive_root)
    provenance = {
        name: entry
        for name, entry in (
            ("donor", donor_provenance),
            ("capture", capture_provenance),
            ("silver", silver_provenance),
            ("gold", gold_provenance),
            ("platinum", candidate_provenance),
        )
        if entry is not None
    }

    captured = _nonnegative_integer(
        capture, "captured", capture_path.name if capture_path else "capture"
    )
    selected = _nonnegative_integer(
        capture, "selected", capture_path.name if capture_path else "capture"
    )
    results = capture.get("results") if capture is not None else None
    complete_results = (
        isinstance(results, list)
        and len(results) == selected
        and all(
            isinstance(result, dict) and result.get("state") == "captured"
            for result in results
        )
    )
    bronze_ready = (
        donor is not None
        and capture is not None
        and complete_results
        and captured == selected
    )
    layers = {
        "bronze": bronze_ready,
        "silver": silver is not None,
        "gold": gold is not None,
        "platinum": candidate is not None,
    }
    manifests = (donor, capture, silver, gold, candidate)
    present = sum(layer is not None for layer in manifests)
    status = (
        "no_state" if present == 0 else "ready" if all(layers.values()) else "partial"
    )

    dataset = ""
    candidate_sha256 = ""
    if candidate is not None and candidate_path is not None:
        dataset_value = candidate.get("dataset")
        if not isinstance(dataset_value, str) or not dataset_value:
            message = f"invalid_manifest:{candidate_path.name}"
            raise HealthAppropriationsStateError(message)
        dataset = dataset_value
        candidate_sha256 = cast("dict[str, str]", candidate_provenance)["sha256"]

    return {
        "archive_root": str(archive_root),
        "status": status,
        "layers": layers,
        "manifest_count": present,
        "donor_file_count": _nonnegative_integer(
            donor, "file_count", donor_path.name if donor_path else "donor"
        ),
        "captured_resources": captured,
        "silver_records": _nonnegative_integer(
            silver, "record_count", silver_path.name if silver_path else "silver"
        ),
        "candidate_manifest_sha256": candidate_sha256,
        "dataset": dataset,
        "manifest_provenance": provenance,
    }
