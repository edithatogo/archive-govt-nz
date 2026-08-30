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


def _load_manifest(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        message = f"invalid_manifest:{path.name}"
        raise HealthAppropriationsStateError(message) from error
    if not isinstance(value, dict) or not isinstance(value.get("schema_version"), str):
        message = f"invalid_manifest:{path.name}"
        raise HealthAppropriationsStateError(message)
    return cast("dict[str, Any]", value)


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

    donor = _load_manifest(donor_path)
    capture = _load_manifest(capture_path)
    silver = _load_manifest(silver_path)
    gold = _load_manifest(gold_path)
    candidate = _load_manifest(candidate_path)

    bronze_ready = donor is not None and capture is not None
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
        candidate_sha256 = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

    return {
        "archive_root": str(archive_root),
        "status": status,
        "layers": layers,
        "manifest_count": present,
        "donor_file_count": _nonnegative_integer(
            donor, "file_count", donor_path.name if donor_path else "donor"
        ),
        "captured_resources": _nonnegative_integer(
            capture, "captured", capture_path.name if capture_path else "capture"
        ),
        "silver_records": _nonnegative_integer(
            silver, "record_count", silver_path.name if silver_path else "silver"
        ),
        "candidate_manifest_sha256": candidate_sha256,
        "dataset": dataset,
    }
