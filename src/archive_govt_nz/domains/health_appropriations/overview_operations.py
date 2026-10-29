"""Operational common overview dispatch with explicit legacy-table projection.

The compact operation receipt does not pin this manifest. Later readback must
supply its SHA from the scoped producer run inventory or recovery receipt.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq
from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_overview_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_estimates_summary as native,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    DispatchResult,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    identity,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

_SCHEMA = "archive-govt-nz.vote-health-overview-operation/v1"
_ERROR = "invalid_overview_operation"
_MAX_METADATA = 1024 * 1024
_MAX_TABLE = 4 * 1024 * 1024
_OUTPUT_NAMES = (
    "vote_health_overview_facts.parquet",
    "field_lineage.parquet",
    "page_dispositions.parquet",
)


def _closed(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


_TEXT = {"type": "string", "minLength": 1}
_PIN = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
# Exact expected selection/loss/context equality is checked after this shape.
MANIFEST_SCHEMA = _closed(
    {
        "schema_version": {"const": _SCHEMA},
        "status": {"const": "passed"},
        "profile": _TEXT,
        "source_object_sha256": _PIN,
        "source_locator": _TEXT,
        "source_vintage": _TEXT,
        "observed_at": _TEXT,
        "counts": _closed(
            {
                "pages": {"type": "integer", "minimum": 1},
                "facts": {"type": "integer", "minimum": 1},
            }
        ),
        "adapter_selection": _closed(
            {
                "schema_version": {
                    "const": "archive-govt-nz.health-adapter-selection/v1"
                },
                "source_sha256": _PIN,
                "declared_media_type": {"const": "application/pdf"},
                "detected_media_type": {"const": "application/pdf"},
                "adapter": _closed({"id": _TEXT, "version": {"const": "1"}}),
                "status": {"const": "selected"},
                "reason": {"type": "null"},
                "considered_adapter_ids": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": _TEXT,
                },
                "matched_adapter_ids": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": _TEXT,
                },
                "receipt_sha256": _PIN,
            }
        ),
        "common_losses": {
            "type": "array",
            "minItems": 1,
            "items": _closed(
                {
                    "source_coordinate": _TEXT,
                    "disposition": {"enum": ["partially_normalized", "preserved_only"]},
                    "reason": _TEXT,
                }
            ),
        },
        "compatibility_projection": _closed(
            {
                "preserved_only": {"const": "preserved_unreviewed"},
                "unreviewed_reason": {"const": "not_reviewed_by_overview_profile"},
                "original_losses_retained": {"const": True},
            }
        ),
        "output_sha256": _closed(dict.fromkeys(_OUTPUT_NAMES, _PIN)),
    }
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _dispatch(  # noqa: PLR0913 - explicit source identity/context
    source: Path,
    *,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
) -> tuple[DispatchResult, adapters.ReviewedOverviewProfile, dict[str, Any]]:
    controls = adapters.reviewed_overview_profile(source_vintage)
    _require(profile == controls.profile and expected_sha256 == controls.source_sha256)
    _require(not source.is_symlink() and source.is_file())
    payload = verified_snapshot(source, expected_sha256, max_bytes=native.MAX_BYTES)
    registration = adapters.vote_health_estimates_overview_registration(
        source_locator=source_locator,
        source_vintage=source_vintage,
        observed_at=observed_at,
    )
    result = dispatch_bronze(
        payload,
        source_sha256=expected_sha256,
        media_type="application/pdf",
        registrations=(registration,),
    )
    selection = result.selection
    _require(
        selection.status == "selected"
        and selection.adapter_id == controls.adapter_id
        and selection.adapter_version == "1"
        and selection.reason is None
        and selection.source_sha256 == expected_sha256
        and selection.declared_media_type
        == selection.detected_media_type
        == "application/pdf"
        and selection.considered_adapter_ids
        == selection.matched_adapter_ids
        == (controls.adapter_id,)
    )
    _require(
        result.output.layout == profile
        and len(result.output.records) == controls.fact_count
    )
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    return result, controls, context


def _project(
    result: DispatchResult,
    controls: adapters.ReviewedOverviewProfile,
    context: dict[str, Any],
) -> dict[str, pa.Table]:
    output = result.output
    facts = list(output.records)
    ids = {row["record_id"] for row in facts}
    _require(len(ids) == len(facts))
    expected_dimensions, expected_links = adapters.overview_period_dimensions(
        output.records, output.lineage
    )
    _require(
        output.dimensions == expected_dimensions
        and output.dimension_links == expected_links
    )
    _require(
        all(
            all(row.get(key) == value for key, value in context.items())
            and set(row) == set(native.FACT_SCHEMA.names)
            and row["transformation_id"] == controls.transformation
            and row["record_id"]
            == identity(
                controls.transformation,
                context["source_object_sha256"],
                row["source_page"],
                row["summary_measure"],
            )
            and row["lineage_id"] == identity(row["record_id"], "lineage")
            for row in facts
        )
    )
    value_lineage = [row for row in output.lineage if row.field == "value"]
    phrase_lineage = [row for row in output.lineage if row.field == "source_phrase"]
    _require(
        len(value_lineage) == len(facts)
        and {row.record_id for row in value_lineage} == ids
    )
    _require(
        len(value_lineage) + len(phrase_lineage) == len(output.lineage)
        and (
            not phrase_lineage
            or (
                len(phrase_lineage) == len(facts)
                and {row.record_id for row in phrase_lineage} == ids
            )
        )
    )
    _require(
        all(
            row.field == "value" and row.rule == controls.transformation
            for row in value_lineage
        )
    )
    facts_by_id = {row["record_id"]: row for row in facts}
    _require(
        all(
            row.rule == "reviewed_overview_source_phrase/v1"
            and row.raw_value == row.normalized_value
            and isinstance(facts_by_id[row.record_id]["raw_values_json"], str)
            and row.raw_value
            == json.loads(str(facts_by_id[row.record_id]["raw_values_json"]))[
                "source_phrase"
            ]
            and row.source_coordinate
            == (
                f"pdf:page={facts_by_id[row.record_id]['source_page']};"
                f"overview:{facts_by_id[row.record_id]['summary_measure']}"
            )
            for row in phrase_lineage
        )
    )
    lineage = [
        {
            "lineage_id": identity(row.record_id, "value"),
            "source_object_sha256": context["source_object_sha256"],
            "source_locator": context["source_locator"],
            **asdict(row),
        }
        for row in value_lineage
    ]
    pages = {row["source_page"] for row in facts}
    _require(pages <= {2, 3} and len(output.losses) == controls.page_count)
    dispositions = []
    for page, loss in enumerate(output.losses, start=1):
        normalized = page in pages
        expected_reason = (
            controls.disposition_reason
            if normalized
            else "not_reviewed_by_2016_17_overview_profile"
            if controls.vintage == native.VINTAGE_2016_17
            else "not_reviewed_by_overview_profile"
        )
        _require(
            loss.source_coordinate == f"pdf:page={page}"
            and loss.disposition
            == ("partially_normalized" if normalized else "preserved_only")
            and loss.reason == expected_reason
        )
        dispositions.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "source_locator": context["source_locator"],
                "source_page": page,
                "disposition": "partially_normalized"
                if normalized
                else "preserved_unreviewed",
                "reason": controls.disposition_reason
                if normalized
                else "not_reviewed_by_overview_profile",
            }
        )
    return {
        _OUTPUT_NAMES[0]: pa.Table.from_pylist(facts, native.FACT_SCHEMA),
        _OUTPUT_NAMES[1]: pa.Table.from_pylist(lineage, native.LINEAGE_SCHEMA),
        _OUTPUT_NAMES[2]: pa.Table.from_pylist(dispositions, native.DISPOSITION_SCHEMA),
    }


def _receipt(
    result: DispatchResult,
    controls: adapters.ReviewedOverviewProfile,
    context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA,
        "status": "passed",
        "profile": controls.profile,
        **{
            key: context[key]
            for key in ("source_object_sha256", "source_locator", "source_vintage")
        },
        "observed_at": context["observed_at"].isoformat(),
        "counts": {
            "pages": len({row["source_page"] for row in result.output.records}),
            "facts": len(result.output.records),
        },
        "adapter_selection": result.selection.to_receipt(),
        "common_losses": [asdict(loss) for loss in result.output.losses],
        "compatibility_projection": {
            "preserved_only": "preserved_unreviewed",
            "unreviewed_reason": "not_reviewed_by_overview_profile",
            "original_losses_retained": True,
        },
    }


def _safe_path(path: Path) -> None:
    _require(not any(part.is_symlink() for part in (path, *path.parents)))


def _snapshot(path: Path, pin: str, limit: int) -> bytes:
    _safe_path(path)
    return verified_snapshot(path, pin, max_bytes=limit)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _json(snapshot: bytes) -> dict[str, Any]:
    result = json.loads(snapshot, object_pairs_hook=_object)
    _require(isinstance(result, dict))
    return result


def _table_hashes(tables: dict[str, pa.Table]) -> dict[str, str]:
    hashes = {}
    for name, table in tables.items():
        with pa.BufferOutputStream() as stream:
            pq.write_table(table, stream)
            payload = stream.getvalue().to_pybytes()
        hashes[name] = hashlib.sha256(payload).hexdigest()
    return hashes


def _readback(
    output_dir: Path,
    pin: str,
    expected: dict[str, Any],
    tables: dict[str, pa.Table],
) -> dict[str, Any]:
    manifest_path = output_dir / "MANIFEST.json"
    snapshot = _snapshot(manifest_path, pin, _MAX_METADATA)
    manifest = _json(snapshot)
    Draft202012Validator(MANIFEST_SCHEMA).validate(manifest)
    _require(
        {key: value for key, value in manifest.items() if key != "output_sha256"}
        == expected
    )
    _require(
        {p.name for p in output_dir.iterdir()} == {*_OUTPUT_NAMES, "MANIFEST.json"}
    )
    _require(manifest["output_sha256"] == _table_hashes(tables))
    for name in _OUTPUT_NAMES:
        _snapshot(output_dir / name, manifest["output_sha256"][name], _MAX_TABLE)
    _require(_snapshot(manifest_path, pin, _MAX_METADATA) == snapshot)
    return manifest


def normalize_overview(  # noqa: PLR0913 - source identity is explicit
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
    """Write actual common output; originals/existing output are never changed."""
    _safe_path(output_dir)
    _require(
        type(dry_run) is bool
        and not output_dir.exists()
        and not output_dir.is_symlink()
    )
    result, controls, context = _dispatch(
        source,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    )
    tables = _project(result, controls, context)
    receipt = _receipt(result, controls, context)
    if dry_run:
        return {**receipt, "status": "planned"}
    written = write_workbook_outputs(output_dir, tables, receipt)
    pin = hashlib.sha256((output_dir / "MANIFEST.json").read_bytes()).hexdigest()
    _require(_readback(output_dir, pin, receipt, tables) == written)
    return written


def verify_overview(  # noqa: PLR0913 - caller retains independent manifest authority
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
    """Verify a pinned completed overview; never infer a pin or repair a run."""
    # Pin/shape validation precedes expensive source parsing or provenance use.
    snapshot = _snapshot(output_dir / "MANIFEST.json", manifest_sha256, _MAX_METADATA)
    Draft202012Validator(MANIFEST_SCHEMA).validate(_json(snapshot))
    result, controls, context = _dispatch(
        source,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    )
    tables = _project(result, controls, context)
    return _readback(
        output_dir, manifest_sha256, _receipt(result, controls, context), tables
    )
