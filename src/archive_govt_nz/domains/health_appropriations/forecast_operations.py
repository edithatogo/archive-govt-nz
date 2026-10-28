"""Common forecast operations with explicit native metadata projection.

The compact public operation receipt does not authenticate this manifest.
Readback requires a separately retained manifest pin and trusted source context.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import forecast as native
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    DispatchResult,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.context_dimensions import (
    context_source_dimensions,
)
from archive_govt_nz.domains.health_appropriations.forecast_adapter import (
    forecast_health_registration,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

_SCHEMA = "archive-govt-nz.health-forecast-operation/v1"
_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_ERROR = "invalid_forecast_operation"
_OUTPUT_NAMES = (
    "forecast_facts.parquet",
    "field_lineage.parquet",
    "cell_dispositions.parquet",
)
_LINEAGE_FIELDS = (
    "record_id",
    "field",
    "source_coordinate",
    "raw_value",
    "normalized_value",
    "rule",
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _safe_path(path: Path) -> None:
    _require(not any(part.is_symlink() for part in (path, *path.parents)))


def _dispatch(  # noqa: PLR0913 - explicit trusted source context
    source: Path,
    *,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
) -> tuple[DispatchResult, native.ForecastExtraction]:
    registration = forecast_health_registration(
        profile=profile,
        source_locator=source_locator,
        source_vintage=source_vintage,
        observed_at=observed_at,
    )
    _safe_path(source)
    payload = verified_snapshot(
        source, expected_sha256, max_bytes=native.MAX_SOURCE_BYTES
    )
    result = dispatch_bronze(
        payload,
        source_sha256=expected_sha256,
        media_type=_MEDIA,
        registrations=(registration,),
    )
    selection = result.selection
    _require(
        selection.status == "selected"
        and selection.adapter_id == registration.adapter_id
        and selection.adapter_version == "1"
        and selection.reason is None
        and selection.source_sha256 == expected_sha256
        and selection.declared_media_type == selection.detected_media_type == _MEDIA
        and selection.considered_adapter_ids
        == selection.matched_adapter_ids
        == (registration.adapter_id,)
        and result.output.layout == profile
    )
    # The loss protocol omits raw cell types/values and native record links.
    # Recover only that auxiliary metadata from these exact immutable bytes;
    # facts and lineage below are consumed from the real dispatch output.
    parsed = native.parse_forecast_snapshot(
        payload,
        expected_sha256=expected_sha256,
        profile=profile,
        observed_at=observed_at,
        source_vintage=source_vintage,
        source_locator=source_locator,
    )
    _require(
        list(result.output.records)
        == [
            {name: row.get(name) for name in native.SILVER_SCHEMA.names}
            for row in parsed.facts
        ]
    )
    _require(
        [asdict(row) for row in result.output.lineage]
        == [{name: row[name] for name in _LINEAGE_FIELDS} for row in parsed.lineage]
    )
    losses = [
        {name: row[name] for name in ("source_coordinate", "disposition", "reason")}
        for row in parsed.dispositions
        if row["disposition"] != "normalized"
    ] + [
        {
            "source_coordinate": "worksheet:" + row["sheet"],
            "disposition": "preserved_only",
            "reason": row["reason"],
        }
        for row in parsed.excluded_sheets
    ]
    _require([asdict(row) for row in result.output.losses] == losses)
    expected_dimensions, expected_links = context_source_dimensions(
        result.output.records, result.output.lineage, family="forecast"
    )
    _require(result.output.dimensions == expected_dimensions)
    _require(result.output.dimension_links == expected_links)
    return result, parsed


def _project(
    result: DispatchResult, parsed: native.ForecastExtraction
) -> dict[str, pa.Table]:
    context = parsed.context
    lineage = [
        {
            "lineage_id": metadata["lineage_id"],
            "source_object_sha256": context["source_object_sha256"],
            "source_locator": context["source_locator"],
            **asdict(row),
        }
        for row, metadata in zip(result.output.lineage, parsed.lineage, strict=True)
    ]
    return {
        _OUTPUT_NAMES[0]: pa.Table.from_pylist(
            list(result.output.records), native.SILVER_SCHEMA
        ),
        _OUTPUT_NAMES[1]: pa.Table.from_pylist(lineage, native.LINEAGE_SCHEMA),
        # Use the native compatibility schema, without modifying its API/pin.
        _OUTPUT_NAMES[2]: pa.Table.from_pylist(
            parsed.dispositions,
            native._CELL_SCHEMA,  # noqa: SLF001
        ),
    }


def _receipt(
    result: DispatchResult,
    parsed: native.ForecastExtraction,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    context = parsed.context
    counts = {
        name: sum(row["disposition"] == name for row in parsed.dispositions)
        for name in ("normalized", "rejected", "context", "preserved_only")
    }
    counts["inventoried_cells"] = len(parsed.dispositions)
    receipt = {
        "schema_version": _SCHEMA,
        "native_extraction_schema_version": (
            "archive-govt-nz.health-forecast-extraction/v1"
        ),
        "transformation_id": native.TRANSFORMATION,
        "profile": result.output.layout,
        "status": "partial"
        if counts["rejected"]
        else "planned"
        if dry_run
        else "passed",
        **{
            key: context[key]
            for key in ("source_object_sha256", "source_locator", "source_vintage")
        },
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "counts": counts,
        "selection": parsed.selection,
        "disposition_scope": "nonempty_cells_plus_selected_inputs",
        "excluded_sheets": parsed.excluded_sheets,
        "workbook_inventory": parsed.inventory,
        "adapter_selection": result.selection.to_receipt(),
        "common_losses": [asdict(row) for row in result.output.losses],
        "compatibility_projection": {
            "facts_and_field_lineage": "actual_common_dispatch_output",
            "raw_cell_metadata": "same_verified_snapshot_shared_native_parser",
            "all_common_fields_reconciled": True,
            "original_losses_retained": True,
            "rejected_cells": "partial_package_never_operation_success",
        },
    }
    return json.loads(encode_json(receipt))


def _snapshot(path: Path, pin: str, limit: int) -> bytes:
    _safe_path(path)
    return verified_snapshot(path, pin, max_bytes=limit)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


@dataclass(frozen=True, slots=True)
class _ExpectedPackage:
    hashes: dict[str, str]
    sizes: dict[str, int]
    manifest: bytes


def _expected_package(
    expected: dict[str, Any],
    tables: dict[str, pa.Table],
) -> _ExpectedPackage:
    """Derive all read limits from trusted regenerated outputs, never file stats."""
    hashes = {}
    sizes = {}
    for name, table in tables.items():
        with pa.BufferOutputStream() as stream:
            pq.write_table(table, stream)
            payload = stream.getvalue().to_pybytes()
        hashes[name] = hashlib.sha256(payload).hexdigest()
        sizes[name] = len(payload)
    # This is the existing native writer's exact UTF-8 serialization.
    manifest = (encode_json({**expected, "output_sha256": hashes}) + "\n").encode()
    return _ExpectedPackage(hashes, sizes, manifest)


def _readback(
    output_dir: Path,
    pin: str,
    expected: dict[str, Any],
    package: _ExpectedPackage,
) -> dict[str, Any]:
    manifest_path = output_dir / "MANIFEST.json"
    snapshot = _snapshot(manifest_path, pin, len(package.manifest))
    manifest = json.loads(snapshot, object_pairs_hook=_object)
    # Exact regenerated metadata closes every nested shape, value and key;
    # canonical JSON also distinguishes booleans from integers. There is no
    # schema wildcard accepting caller-defined selection/loss data.
    _require(isinstance(manifest, dict))
    _require(
        encode_json(
            {key: value for key, value in manifest.items() if key != "output_sha256"}
        )
        == encode_json(expected)
    )
    _require(
        {path.name for path in output_dir.iterdir()}
        == {*_OUTPUT_NAMES, "MANIFEST.json"}
    )
    _require(manifest.get("output_sha256") == package.hashes)
    for name in _OUTPUT_NAMES:
        _snapshot(output_dir / name, package.hashes[name], package.sizes[name])
    _require(_snapshot(manifest_path, pin, len(package.manifest)) == snapshot)
    return manifest


def normalize_forecast(  # noqa: PLR0913 - explicit trusted source context
    source: Path,
    output_dir: Path,
    *,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Consume common output; explicitly requested partial writes retain evidence."""
    _safe_path(output_dir)
    _require(type(dry_run) is bool and not output_dir.exists())
    result, parsed = _dispatch(
        source,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    )
    receipt = _receipt(result, parsed, dry_run=dry_run)
    if dry_run:
        return {**receipt, "preflight_scope": "source_validation_only"}
    tables = _project(result, parsed)
    package = _expected_package(receipt, tables)
    written = write_workbook_outputs(output_dir, tables, receipt)
    # Producer consistency uses its source-derived pin. Later verification must
    # still supply a separately retained caller pin through verify_forecast.
    pin = hashlib.sha256(package.manifest).hexdigest()
    _require(_readback(output_dir, pin, receipt, package) == written)
    return written


def verify_forecast(  # noqa: PLR0913 - independent pin and trusted source context
    source: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
) -> dict[str, Any]:
    """Verify completed or partial evidence; never infer a pin or repair a run."""
    _require(
        isinstance(manifest_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is not None
    )
    manifest_path = output_dir / "MANIFEST.json"
    _safe_path(manifest_path)
    _require(manifest_path.is_file())
    result, parsed = _dispatch(
        source,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    )
    expected = _receipt(result, parsed, dry_run=False)
    package = _expected_package(expected, _project(result, parsed))
    return _readback(output_dir, manifest_sha256, expected, package)
