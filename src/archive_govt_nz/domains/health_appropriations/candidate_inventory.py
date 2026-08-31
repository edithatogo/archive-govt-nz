"""Read-only additive inventories; never build, approve or publish a candidate."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

MAX_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
PROFILES = MappingProxyType(
    {
        "budget-2026": ("budget", "Budget-2026", "budget_facts", "row_dispositions"),
        "cpi-2026-q2": ("cpi", "Stats-NZ-CPI-2026-Q2", "cpi_facts", "row_dispositions"),
        "befu-2026": ("forecast", "BEFU-2026", "forecast_facts", "cell_dispositions"),
        "hyefu-2025": ("forecast", "HYEFU-2025", "forecast_facts", "cell_dispositions"),
    }
)
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}


@dataclass(frozen=True)
class PinnedInput:
    """One explicitly reviewed local file identity, not an approval token."""

    path: Path
    sha256: str


def _require(condition: object) -> None:
    if not condition:
        message = "candidate_inventory_contract"
        raise ValueError(message)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _snapshot(pin: PinnedInput) -> bytes:
    _require(re.fullmatch(r"[0-9a-f]{64}", pin.sha256) is not None)
    _require(not pin.path.is_symlink() and not pin.path.parent.is_symlink())
    return verified_snapshot(pin.path, pin.sha256, max_bytes=MAX_BYTES)


def _json(payload: bytes) -> dict[str, Any]:
    result = json.loads(payload, object_pairs_hook=_pairs)
    _require(isinstance(result, dict))
    return result


def _relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    _require(path.as_posix() == value and not path.is_absolute())
    for part in path.parts:
        _require(
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", part) is not None
            and not part.endswith(".")
            and part.split(".")[0].upper() not in _RESERVED
        )
    _require(bool(path.parts))
    return path


def _unique(paths: list[str]) -> None:
    seen: set[str] = set()
    for value in paths:
        key = _relative(value).as_posix().casefold()
        _require(key not in seen)
        seen.add(key)
    for key in seen:
        _require(
            not any(parent.as_posix() in seen for parent in PurePosixPath(key).parents)
        )


def _inventory(root: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _require(not root.is_symlink() and root.is_dir())
    paths = [row["path"] for row in entries]
    _unique([*paths, "MANIFEST.json"])
    observed = set()
    for path in root.rglob("*"):
        _require(not path.is_symlink())
        if path.is_file():
            observed.add(path.relative_to(root).as_posix())
    _require(observed == set(paths) | {"MANIFEST.json"})
    result, total = [], 0
    for row in sorted(entries, key=lambda row: row["path"]):
        payload = _snapshot(PinnedInput(root / row["path"], row["sha256"]))
        total += len(payload)
        _require(total <= MAX_TOTAL_BYTES)
        _require(type(row["bytes"]) is int and row["bytes"] == len(payload))
        result.append(
            {"path": row["path"], "sha256": row["sha256"], "bytes": len(payload)}
        )
    return result


def _join(
    manifest: dict[str, Any],
    captures: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    base_files: list[dict[str, Any]],
) -> dict[str, Any]:
    source = manifest["source_object_sha256"]
    matches = [row for row in captures if row["sha256"] == source]
    _require(len(matches) == 1)
    capture = matches[0]
    _require(
        isinstance(capture["source_id"], str) and bool(capture["source_id"].strip())
    )
    _require(type(capture["bytes"]) is int)
    _require(
        capture["state"] == "captured" and capture["object_id"] == "sha256:" + source
    )
    _require(capture["url"] == manifest["source_locator"])
    rights = capture["rights"]
    _require(rights["state"] == "eligible")
    for field in ("license", "evidence", "attribution"):
        _require(isinstance(rights[field], str) and bool(rights[field].strip()))
    matches = [row for row in resources if row["source_sha256"] == source]
    _require(len(matches) == 1)
    resource = matches[0]
    _require(
        resource["source_url"] == capture["url"]
        and resource["license"] == rights["license"]
        and resource["rights_evidence"] == rights["evidence"]
        and resource["attribution"] == rights["attribution"]
    )
    originals = [
        row
        for row in base_files
        if row["path"].startswith("original/") and row["sha256"] == source
    ]
    _require(len(originals) == 1)
    original = originals[0]
    _require(
        original["path"] == resource["path"] and original["bytes"] == capture["bytes"]
    )
    return {
        "source_id": capture["source_id"],
        "source_sha256": source,
        "original_path": original["path"],
        "source_url": capture["url"],
        "recorded_source_rights": dict(rights),
    }


def plan_additive_inventory(
    *,
    base: PinnedInput,
    capture: PinnedInput,
    rights: PinnedInput,
    packages: Mapping[str, PinnedInput],
) -> dict[str, Any]:
    """Verify retained bytes and exact recorded rights joins without writing.

    All four fixed profiles must be explicitly pinned. This is fixity and
    metadata reconciliation, not Parquet semantic validation or legal review.
    Reviewed local roots are not a sandbox against concurrent hostile changes.
    No candidate is created and no existing publication approval is inherited.
    """
    base_manifest = _json(_snapshot(base))
    capture_manifest = _json(_snapshot(capture))
    rights_manifest = _json(_snapshot(rights))
    _require(base.path.name == "MANIFEST.json")
    _require(
        base_manifest["schema_version"] == "archive-govt-nz.health-hf-candidate/v1"
    )
    _require(base_manifest["dataset"] == "edithatogo/nz-health-appropriations")
    base_files = _inventory(base.path.parent, base_manifest["files"])
    _require(rights.path == base.path.parent / "metadata/rights.json")
    _require(
        any(
            row["path"] == "metadata/rights.json" and row["sha256"] == rights.sha256
            for row in base_files
        )
    )
    _require(set(packages) == set(PROFILES))
    additions, summaries = [], []
    for name, pin in sorted(packages.items()):
        payload = _snapshot(pin)
        manifest = _json(payload)
        family, vintage, facts, dispositions = PROFILES[name]
        _require(pin.path.name == "MANIFEST.json")
        _require(
            manifest["schema_version"]
            == f"archive-govt-nz.health-{family}-extraction/v1"
        )
        _require(
            manifest["status"] == "passed"
            and manifest["rights_state"] == "not_evaluated"
        )
        _require(manifest["source_vintage"] == vintage)
        outputs = manifest["output_sha256"]
        _require(
            set(outputs)
            == {f"{stem}.parquet" for stem in (facts, dispositions, "field_lineage")}
        )
        entries = []
        for filename, digest in outputs.items():
            snapshot = _snapshot(PinnedInput(pin.path.parent / filename, digest))
            entries.append({"path": filename, "sha256": digest, "bytes": len(snapshot)})
        inventory = _inventory(pin.path.parent, entries)
        inventory.append(
            {"path": "MANIFEST.json", "sha256": pin.sha256, "bytes": len(payload)}
        )
        namespace = f"data/silver/raw-{name}/v1"
        additions.extend(
            {**row, "path": f"{namespace}/{row['path']}"} for row in inventory
        )
        summaries.append(
            {
                "profile": name,
                "manifest_sha256": pin.sha256,
                "namespace": namespace,
                "source_vintage": vintage,
                "derivative_rights_state": manifest["rights_state"],
                "rights_join": _join(
                    manifest,
                    capture_manifest["results"],
                    rights_manifest["resources"],
                    base_files,
                ),
            }
        )
    _unique(
        [
            "MANIFEST.json",
            *[row["path"] for row in base_files],
            *[row["path"] for row in additions],
        ]
    )
    return {
        "schema_version": "archive-govt-nz.health-additive-inventory/v1",
        "status": "local_inventory_verified",
        "publication_approval": "not_granted",
        "semantic_validation": "not_performed",
        "candidate_build": "not_performed",
        "metadata_overhead": "not_planned",
        "change_scope": "payload_inventory_only",
        "base_manifest_handling": (
            "retain_pinned_provenance_new_root_manifest_not_planned"
        ),
        "base_manifest_sha256": base.sha256,
        "capture_manifest_sha256": capture.sha256,
        "rights_manifest_sha256": rights.sha256,
        "base_files": len(base_files),
        "base_bytes": sum(row["bytes"] for row in base_files),
        "additions": sorted(additions, key=lambda row: row["path"]),
        "added_bytes": sum(row["bytes"] for row in additions),
        "packages": summaries,
        "replaced_files": [],
        "removed_files": [],
    }
