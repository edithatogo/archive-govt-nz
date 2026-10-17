"""Five reviewed context operations, with complete common output and native tables.

The compact public receipt is not a manifest authentication mechanism. Readback
requires an independently retained pin and the exact trusted source context.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    cpi,
    gdp,
    population_annual_export,
    qes,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    DispatchResult,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.context_population_projection import (  # noqa: E501
    project_population,
)
from archive_govt_nz.domains.health_appropriations.cpi_adapter import cpi_registration
from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook
from archive_govt_nz.domains.health_appropriations.gdp_adapter import gdp_registration
from archive_govt_nz.domains.health_appropriations.population_annual_adapter import (
    population_annual_registration,
)
from archive_govt_nz.domains.health_appropriations.qes_adapter import qes_registration
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
        AdapterOutput,
    )

_SCHEMA = "archive-govt-nz.health-context-operation/v1"
_ERROR = "invalid_context_operation"
PROFILES = frozenset(
    {
        "cpiq-se9a/v1",
        "population-annual-mean-context/v1",
        "qes-june2026-table8/v1",
        "gdp-expenditure-actual-2026q1/v1",
        "gdp-expenditure-actual-2026q2/v1",
    }
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


def _registration(
    profile: str, context: dict[str, Any], observed_at: str
) -> tuple[AdapterRegistration, int]:
    _require(profile in PROFILES)
    options = {
        name: context[name]
        for name in ("source_locator", "source_vintage", "observed_at")
    }
    options["observed_at"] = observed_at
    if profile == "cpiq-se9a/v1":
        return cpi_registration(**options), cpi.MAX_BYTES
    if profile == "population-annual-mean-context/v1":
        return population_annual_registration(
            **options
        ), population_annual_export.MAX_BYTES
    if profile == "qes-june2026-table8/v1":
        return qes_registration(**options), qes.MAX_BYTES
    vintage = gdp.JUNE_VINTAGE if profile.endswith("2026q2/v1") else gdp.VINTAGE
    _require(context["source_vintage"] == vintage)
    return gdp_registration(**options), gdp.MAX_BYTES


def _dispatch(
    source: Path, profile: str, context: dict[str, Any], observed_at: str
) -> tuple[DispatchResult, bytes]:
    registration, limit = _registration(profile, context, observed_at)
    _safe_path(source)
    payload = verified_snapshot(
        source, context["source_object_sha256"], max_bytes=limit
    )
    result = dispatch_bronze(
        payload,
        source_sha256=context["source_object_sha256"],
        media_type=registration.media_type,
        registrations=(registration,),
    )
    selection = result.selection
    _require(
        selection.status == "selected"
        and selection.schema_version == "archive-govt-nz.health-adapter-selection/v1"
        and selection.reason is None
        and selection.adapter_id == registration.adapter_id
        and selection.adapter_version == registration.version
        and selection.source_sha256 == context["source_object_sha256"]
        and selection.declared_media_type
        == selection.detected_media_type
        == registration.media_type
        and selection.considered_adapter_ids
        == selection.matched_adapter_ids
        == (registration.adapter_id,)
    )
    # Reconcile every original common field, including unresolved dimensions and
    # links, against the same independently hash-verified immutable source. Both
    # structural and serialized equality matter (e.g. False versus integer zero).
    expected = registration.adapter.extract(
        payload, source_sha256=context["source_object_sha256"]
    )
    _require(
        result.output == expected
        and encode_json(asdict(result.output)) == encode_json(asdict(expected))
    )
    return result, payload


def _project(
    result: DispatchResult, payload: bytes, profile: str, context: dict[str, Any]
) -> tuple[dict[str, pa.Table], dict[str, Any]]:
    if profile == "population-annual-mean-context/v1":
        tables, counts = project_population(result.output, context)
        return tables, {
            "native_extraction_schema_version": (
                "archive-govt-nz.health-population-annual-extraction/v1"
            ),
            "transformation_id": "stats-nz-population-annual-mean-context/v1",
            "analytical_selection": "not_selected",
            "counts": counts,
        }
    native = (
        cpi
        if profile == "cpiq-se9a/v1"
        else qes
        if profile == "qes-june2026-table8/v1"
        else gdp
    )
    facts, lineage, dispositions = native.inspect_bronze_payload(payload, context)
    # Auxiliary disposition metadata comes from the exact snapshot parser; the
    # fact and six-field lineage values below come from actual common dispatch.
    _require(list(result.output.records) == facts)
    common_lineage = [asdict(row) for row in result.output.lineage]
    _require(
        common_lineage
        == [{key: row[key] for key in _LINEAGE_FIELDS} for row in lineage]
    )
    projected_lineage = [
        {**metadata, **row}
        for metadata, row in zip(lineage, common_lineage, strict=True)
    ]
    family = "cpi" if native is cpi else "qes" if native is qes else "gdp"
    tables = {
        family + "_facts.parquet": pa.Table.from_pylist(
            list(result.output.records), native.FACT_SCHEMA
        ),
        "field_lineage.parquet": pa.Table.from_pylist(
            projected_lineage, LINEAGE_SCHEMA
        ),
        (
            "row_dispositions.parquet" if native is cpi else "cell_dispositions.parquet"
        ): pa.Table.from_pylist(dispositions, native.DISPOSITION_SCHEMA),
    }
    metadata: dict[str, Any] = {
        "native_extraction_schema_version": "archive-govt-nz.health-"
        + family
        + "-extraction/v1",
        "transformation_id": native.TRANSFORMATION,
    }
    if native is cpi:
        missing = sum(row["amount"] is None for row in facts)
        metadata.update(
            series_reference=cpi.SERIES,
            index_base=None,
            counts={
                "input": len(dispositions),
                "selected": len(facts),
                "numeric": len(facts) - missing,
                "missing": missing,
                "unselected": len(dispositions) - len(facts),
            },
        )
    elif native is qes:
        metadata.update(
            native_extraction_schema_version="archive-govt-nz.qes-extraction/v1",
            workbook_inventory=inventory_workbook(BytesIO(payload)),
            disposition_scope="nonempty_cells",
            quality_flags=list(qes.FLAGS),
            counts={
                "normalized": len(facts),
                "field_lineage": len(lineage),
                "inventoried_cells": len(dispositions),
            },
        )
    else:
        metadata.update(
            transformation_id=gdp.JUNE_TRANSFORMATION
            if profile.endswith("2026q2/v1")
            else gdp.TRANSFORMATION,
            currency=None,
            counts={
                "facts": len(facts),
                "lineage": len(lineage),
                "dispositions": len(dispositions),
            },
        )
    return tables, metadata


def _receipt(
    result: DispatchResult,
    metadata: dict[str, Any],
    profile: str,
    context: dict[str, Any],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    receipt = {
        "schema_version": _SCHEMA,
        **metadata,
        **context,
        "observed_at": context["observed_at"].isoformat(),
        "profile": profile,
        "status": "passed"
        if not dry_run or profile == "qes-june2026-table8/v1"
        else "planned",
        "rights_state": "not_evaluated",
        "adapter_selection": result.selection.to_receipt(),
        "common_output": asdict(result.output),
        "compatibility_projection": {
            "facts": (
                "actual_common_records_with_explicit_population_native_enrichment"
            ),
            "lineage": (
                "actual_common_fields_with_explicit_population_native_period_and_rule_projection"
            ),
            "population_status": (
                "native_disposition_plus_full_common_status_lineage_in_manifest"
            ),
            "dispositions": "same_verified_snapshot_native_metadata",
            "all_common_fields_retained": True,
            "dimensions": "source_literals_only_no_approved_joins",
            "historical_canonical_readers": "unchanged_native_packages_only",
        },
    }
    return json.loads(encode_json(receipt))


@dataclass(frozen=True, slots=True)
class _ExpectedPackage:
    hashes: dict[str, str]
    sizes: dict[str, int]
    manifest: bytes


def _expected_package(
    receipt: dict[str, Any], tables: dict[str, pa.Table]
) -> _ExpectedPackage:
    hashes = {}
    sizes = {}
    for name, table in tables.items():
        with pa.BufferOutputStream() as stream:
            pq.write_table(table, stream)
            payload = stream.getvalue().to_pybytes()
        hashes[name] = hashlib.sha256(payload).hexdigest()
        sizes[name] = len(payload)
    return _ExpectedPackage(
        hashes,
        sizes,
        (encode_json({**receipt, "output_sha256": hashes}) + "\n").encode(),
    )


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _snapshot(path: Path, pin: str, limit: int) -> bytes:
    _safe_path(path)
    return verified_snapshot(path, pin, max_bytes=limit)


def _readback(
    output_dir: Path, pin: str, expected: dict[str, Any], package: _ExpectedPackage
) -> dict[str, Any]:
    path = output_dir / "MANIFEST.json"
    snapshot = _snapshot(path, pin, len(package.manifest))
    manifest = json.loads(snapshot, object_pairs_hook=_object)
    _require(isinstance(manifest, dict))
    _require(
        encode_json(
            {key: value for key, value in manifest.items() if key != "output_sha256"}
        )
        == encode_json(expected)
    )
    _require(
        {item.name for item in islice(output_dir.iterdir(), len(package.hashes) + 2)}
        == {"MANIFEST.json", *package.hashes}
    )
    _require(manifest.get("output_sha256") == package.hashes)
    for name, digest in package.hashes.items():
        _snapshot(output_dir / name, digest, package.sizes[name])
    _require(_snapshot(path, pin, len(package.manifest)) == snapshot)
    return manifest


def normalize_context(  # noqa: PLR0913 - explicit trusted source context
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
    """Preflight without writes, or create an exclusive common-evidence package."""
    _safe_path(output_dir)
    _require(type(dry_run) is bool and not output_dir.exists())
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    result, payload = _dispatch(source, profile, context, observed_at)
    tables, metadata = _project(result, payload, profile, context)
    receipt = _receipt(result, metadata, profile, context, dry_run=dry_run)
    if dry_run:
        return {**receipt, "preflight_scope": "source_validation_only"}
    package = _expected_package(receipt, tables)
    written = write_workbook_outputs(output_dir, tables, receipt)
    _require(
        _readback(
            output_dir, hashlib.sha256(package.manifest).hexdigest(), receipt, package
        )
        == written
    )
    return written


@dataclass(frozen=True, slots=True)
class VerifiedContextOperation:
    """Source-regenerated typed tables and complete authenticated common evidence."""

    manifest: dict[str, Any]
    tables: dict[str, pa.Table]
    common_output: AdapterOutput


def read_context(  # noqa: PLR0913 - independent pin and trusted context
    source: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
) -> VerifiedContextOperation:
    """Verify pin/source and return regenerated tables without reopening candidates."""
    _require(
        isinstance(manifest_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is not None
    )
    _safe_path(output_dir / "MANIFEST.json")
    _require((output_dir / "MANIFEST.json").is_file())
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    result, payload = _dispatch(source, profile, context, observed_at)
    tables, metadata = _project(result, payload, profile, context)
    expected = _receipt(result, metadata, profile, context, dry_run=False)
    manifest = _readback(
        output_dir, manifest_sha256, expected, _expected_package(expected, tables)
    )
    return VerifiedContextOperation(manifest, tables, result.output)


def verify_context(  # noqa: PLR0913 - unchanged public independent verification API
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
    """Read back against independent pin and source; never repair or infer a pin."""
    return read_context(
        source,
        output_dir,
        manifest_sha256=manifest_sha256,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    ).manifest
