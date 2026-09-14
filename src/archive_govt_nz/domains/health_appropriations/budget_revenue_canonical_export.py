"""Persist only verified, local Budget revenue canonical projections."""

from __future__ import annotations

import hashlib
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import budget_canonical_export as _io
from archive_govt_nz.domains.health_appropriations.budget_revenue_projection import (
    RULE,
    project_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.budget_revenue_reader import (
    read_verified_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-local-budget-revenue/v1"
MARKER = "LOCAL_REVENUE.json"


def _require(value: object) -> None:
    if not value:
        message = "budget_revenue_canonical_export_contract"
        raise ValueError(message)


def _files(package: Path, pin: str, original: Path) -> dict[str, bytes]:
    facts, lineage, dispositions, manifest = read_verified_budget_revenue(package, pin)
    original_bytes = verified_snapshot(
        original, manifest["source_object_sha256"], max_bytes=_io.MAX_ORIGINAL_BYTES
    )
    result = project_budget_revenue(
        manifest=manifest,
        manifest_sha256=pin,
        facts=facts,
        lineage=lineage,
        dispositions=dispositions,
    )
    files: dict[str, bytes] = {}
    entries = []
    for name, table in sorted(result.tables.items()):
        payload = _io._parquet(table)  # noqa: SLF001 - shared hardened serializer.
        filename = name + ".parquet"
        files[filename] = payload
        entries.append(
            {
                **_io._entry(filename, payload),  # noqa: SLF001 - exact descriptor shape.
                "rows": table.num_rows,
                "schema_sha256": hashlib.sha256(
                    table.schema.serialize().to_pybytes()
                ).hexdigest(),
            }
        )
    receipt = _io._json(result.receipt)  # noqa: SLF001 - canonical JSON encoding.
    files["projection_receipt.json"] = receipt
    entries.append(_io._entry("projection_receipt.json", receipt))  # noqa: SLF001
    files[MARKER] = _io._json(  # noqa: SLF001
        {
            "schema_version": SCHEMA,
            "descriptor_state": "verify_all_files_before_use",
            "publication_state": "local_validation_only",
            "rights_state": "not_evaluated",
            "publication_approval": "not_granted",
            "self_contained_archive": False,
            "transformation_id": RULE,
            "input_manifest_sha256": pin,
            "input_payload_sha256": manifest["output_sha256"],
            "source_vintage": manifest["source_vintage"],
            "original_sha256": manifest["source_object_sha256"],
            "original_bytes": len(original_bytes),
            "files": sorted(entries, key=lambda item: item["path"]),
        }
    )
    _require(all(len(payload) <= _io.MAX_FILE_BYTES for payload in files.values()))
    _require(sum(map(len, files.values())) <= _io.MAX_TOTAL_BYTES)
    return files


def export_budget_revenue(
    package: Path,
    manifest_sha256: str,
    original: Path,
    output: Path,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Plan or write a deterministic local package; no publication is implied."""
    try:
        _io._validate_paths(package, original, output, dry_run=dry_run)  # noqa: SLF001
        files = _files(package, manifest_sha256, original)
    except OSError, ValueError, TypeError, KeyError, pa.ArrowException:
        message = "budget_revenue_canonical_export_input"
        raise ValueError(message) from None
    receipt = {
        "schema_version": SCHEMA,
        "status": "planned" if dry_run else "passed",
        "hash_state": "planned" if dry_run else "verified_persisted",
        "publication_state": "local_validation_only",
        "files": [_io._entry(name, payload) for name, payload in sorted(files.items())],  # noqa: SLF001
    }
    if dry_run:
        return receipt
    root = None
    try:
        output.mkdir()
        root = _io._pin(output)  # noqa: SLF001
        payloads = {name: value for name, value in files.items() if name != MARKER}
        for name, payload in payloads.items():
            _io._write(root, name, payload)  # noqa: SLF001
        _io._readback(root, payloads)  # noqa: SLF001
        _io._write(root, MARKER, files[MARKER])  # noqa: SLF001
        _io._readback(root, files)  # noqa: SLF001
    except OSError, ValueError, TypeError, KeyError, pa.ArrowException:
        if root is not None:
            with suppress(OSError, ValueError):
                _io._write(  # noqa: SLF001
                    root,
                    "FAILURE.json",
                    _io._json(  # noqa: SLF001
                        {"schema_version": SCHEMA, "status": "failed"}
                    ),
                )
        message = "budget_revenue_canonical_export_write"
        raise ValueError(message) from None
    finally:
        if root is not None and root.descriptor is not None:
            _io.os.close(root.descriptor)
    return receipt
