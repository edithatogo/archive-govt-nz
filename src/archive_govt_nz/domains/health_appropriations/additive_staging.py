"""Exclusive local staging copies; no active publication manifest or approval."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.candidate_inventory import (
    PinnedInput,
    plan_additive_inventory,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

MAX_BYTES = 64 * 1024 * 1024
_CARD = b"""# Local health staging bundle

This is not a publication candidate and grants no publication approval.
Only staging copy integrity is verified; semantic validation and rights
assessment are not performed. New derivative rights remain not_evaluated.
The base-history directory preserves the old candidate and card as historical
bytes, not current claims about the additions. No old approval is inherited.
Do not configure a publisher against this local staging directory.
"""


@dataclass(frozen=True)
class StagingInputs:
    """Explicit reviewed inputs, including a pinned serialized inventory."""

    base: PinnedInput
    capture: PinnedInput
    rights: PinnedInput
    packages: Mapping[str, PinnedInput]
    inventory: PinnedInput


def _require(condition: object) -> None:
    if not condition:
        message = "additive_staging_contract"
        raise ValueError(message)


def _encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _snapshot(pin: PinnedInput) -> bytes:
    _require(not pin.path.is_symlink() and not pin.path.parent.is_symlink())
    return verified_snapshot(pin.path, pin.sha256, max_bytes=MAX_BYTES)


def _preflight(
    inputs: StagingInputs, output: Path, forbidden: tuple[Path, ...]
) -> tuple[dict[str, Any], bytes]:
    _require(bool(forbidden))
    _require(not output.exists() and not output.is_symlink())
    _require(output.parent.is_dir() and not output.parent.is_symlink())
    roots = [
        pin.path.parent
        for pin in (
            inputs.base,
            inputs.capture,
            inputs.rights,
            inputs.inventory,
            *inputs.packages.values(),
        )
    ]
    destination = output.resolve()
    for root in (*roots, *forbidden):
        resolved = root.resolve()
        _require(
            not destination.is_relative_to(resolved)
            and not resolved.is_relative_to(destination)
        )
    plan = plan_additive_inventory(
        base=inputs.base,
        capture=inputs.capture,
        rights=inputs.rights,
        packages=inputs.packages,
    )
    payload = _snapshot(inputs.inventory)
    _require(payload == _encoded(plan))
    return plan, payload


def _write(root: Path, relative: str, payload: bytes, role: str) -> dict[str, Any]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
    return {
        "path": relative,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "role": role,
    }


def _copy_inputs(
    inputs: StagingInputs, root: Path, plan: dict[str, Any]
) -> list[dict[str, Any]]:
    manifest_payload = _snapshot(inputs.base)
    manifest = json.loads(manifest_payload)
    history = f"base-history/{inputs.base.sha256}"
    files = [_write(root, f"{history}/MANIFEST.json", manifest_payload, "base_history")]
    for row in sorted(manifest["files"], key=lambda row: row["path"]):
        payload = _snapshot(
            PinnedInput(inputs.base.path.parent / row["path"], row["sha256"])
        )
        files.append(_write(root, f"{history}/{row['path']}", payload, "base_history"))
    for package in plan["packages"]:
        pin = inputs.packages[package["profile"]]
        prefix = package["namespace"] + "/"
        for row in plan["additions"]:
            if row["path"].startswith(prefix):
                payload = _snapshot(
                    PinnedInput(
                        pin.path.parent / row["path"].removeprefix(prefix),
                        row["sha256"],
                    )
                )
                files.append(
                    _write(root, "additions/" + row["path"], payload, "addition")
                )
    return files


def _readback(root: Path, files: list[dict[str, Any]]) -> None:
    observed = set()
    for path in root.rglob("*"):
        _require(not path.is_symlink())
        if path.is_file():
            observed.add(path.relative_to(root).as_posix())
    _require(observed == {row["path"] for row in files})
    for row in files:
        payload = _snapshot(PinnedInput(root / row["path"], row["sha256"]))
        _require(len(payload) == row["bytes"])


def stage_additive_bundle(
    inputs: StagingInputs, output_dir: Path, *, forbidden_roots: tuple[Path, ...]
) -> dict[str, Any]:
    """Copy pinned history/additions into one exclusively created local bundle.

    Callers must enumerate candidate and publisher-configured roots; the nonempty
    list is not discovery of global publisher configuration or protection from
    arbitrary manual upload. Reviewed roots are not a hostile filesystem sandbox.
    A failure retains partial bytes and attempts a redacted failure receipt.
    Completion requires full copy readback. No v1 active MANIFEST is emitted.
    """
    plan, inventory_payload = _preflight(inputs, output_dir, forbidden_roots)
    output_dir.mkdir(exist_ok=False)
    try:
        files = _copy_inputs(inputs, output_dir, plan)
        files.append(
            _write(output_dir, "INVENTORY.json", inventory_payload, "inventory")
        )
        files.append(_write(output_dir, "README.md", _CARD, "local_staging_notice"))
        _readback(output_dir, files)
        result = {
            "schema_version": "archive-govt-nz.health-additive-staging/v1",
            "status": "local_staging_complete",
            "scope": "staging_copy_integrity_only",
            "publication_approval": "not_granted",
            "semantic_validation": "not_performed",
            "new_derivative_rights_state": "not_evaluated",
            "base_approval_inherited": False,
            "inventory_sha256": inputs.inventory.sha256,
            "base_manifest_sha256": inputs.base.sha256,
            "files": sorted(files, key=lambda row: row["path"]),
        }
        _write(output_dir, "LOCAL_STAGING.json", _encoded(result), "completion")
    except Exception as error:
        # Preserve the original exception even if the filesystem rejects receipts.
        with suppress(OSError):
            (output_dir / "LOCAL_STAGING.json").rename(
                output_dir / "INCOMPLETE_LOCAL_STAGING.json"
            )
        with suppress(OSError), (output_dir / "FAILURE.json").open("xb") as handle:
            handle.write(
                _encoded(
                    {
                        "schema_version": (
                            "archive-govt-nz.health-additive-staging-failure/v1"
                        ),
                        "status": "incomplete",
                        "error_class": type(error).__name__,
                    }
                )
            )
        raise
    return result
