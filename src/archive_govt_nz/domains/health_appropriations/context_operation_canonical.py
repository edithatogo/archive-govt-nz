"""Canonical projection of five verified common-operation source cohorts.

Historical fixed native readers remain unchanged. This path authenticates the
actual operation manifest and retains its complete common-evidence closure.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    context_operations,
)
from archive_govt_nz.domains.health_appropriations import (
    cpi_canonical_projection as cpi,
)
from archive_govt_nz.domains.health_appropriations import (
    gdp_canonical_projection as gdp,
)
from archive_govt_nz.domains.health_appropriations import (
    population_annual_canonical_projection as population,
)
from archive_govt_nz.domains.health_appropriations import (
    qes_canonical_projection as qes,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json
from archive_govt_nz.schemas.health_recordset_normalization import validate_table
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

_SCHEMA = "archive-govt-nz.health-context-operation-canonical-projection/v1"
_ERROR = "context_operation_canonical_invalid"


@dataclass(frozen=True, slots=True)
class ContextSourceProfile:
    """Fixed official source identity and its existing canonical record contract."""

    source_sha256: str
    source_locator: str
    source_vintage: str
    observed_at: str
    transformation: str
    recordset: str
    version: str = "v1"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _profile(profile: str) -> ContextSourceProfile:
    # Resolve the existing exact official cohorts, not candidate metadata. Each
    # observation literal stays distinct even for equivalent timestamp instants.
    if profile == "cpiq-se9a/v1":
        return ContextSourceProfile(
            cpi.SOURCE_SHA256,
            cpi.SOURCE_LOCATOR,
            cpi.SOURCE_VINTAGE,
            cpi.OBSERVED_AT,
            cpi.TRANSFORMATION,
            "price_population_fact",
        )
    if profile == "population-annual-mean-context/v1":
        return ContextSourceProfile(
            population.SOURCE_SHA256,
            population.SOURCE_LOCATOR,
            population.SOURCE_VINTAGE,
            population.OBSERVED_AT,
            population.TRANSFORMATION,
            "price_population_fact",
        )
    if profile == "qes-june2026-table8/v1":
        return ContextSourceProfile(
            qes.SOURCE_SHA256,
            qes.SOURCE_LOCATOR,
            qes.SOURCE_VINTAGE,
            qes.OBSERVED_AT,
            qes.TRANSFORMATION,
            "earnings_fact",
            "v2",
        )
    if profile == "gdp-expenditure-actual-2026q1/v1":
        return ContextSourceProfile(
            gdp.SOURCE_SHA256,
            gdp.SOURCE_LOCATOR,
            gdp.SOURCE_VINTAGE,
            gdp.OBSERVED_AT,
            gdp.TRANSFORMATION,
            "fiscal_context_fact",
        )
    _require(profile == "gdp-expenditure-actual-2026q2/v1")
    return ContextSourceProfile(
        gdp.JUNE_SOURCE_SHA256,
        gdp.JUNE_SOURCE_LOCATOR,
        gdp.JUNE_SOURCE_VINTAGE,
        gdp.JUNE_OBSERVED_AT,
        gdp.JUNE_TRANSFORMATION,
        "fiscal_context_fact",
    )


def _canonicalize(
    verified: context_operations.VerifiedContextOperation,
    profile: str,
    definition: ContextSourceProfile,
) -> tuple[pa.Table, pa.Table]:
    tables = verified.tables
    lineage = tables["field_lineage.parquet"]
    if profile == "cpiq-se9a/v1":
        return cpi.canonicalize_cpi_tables(tables["cpi_facts.parquet"], lineage)
    if profile == "population-annual-mean-context/v1":
        return population.canonicalize_population_tables(
            tables["population_facts.parquet"],
            lineage,
            tables["row_dispositions.parquet"],
        )
    if profile == "qes-june2026-table8/v1":
        return qes.canonicalize_qes_tables(tables["qes_facts.parquet"], lineage)
    return gdp.canonicalize_gdp_tables(
        tables["gdp_facts.parquet"], lineage, transformation=definition.transformation
    )


_QES_LINEAGE_COMPLETION = "qes-operation-canonical-lineage-completion/v1"
_LINEAGE_VALUES = (
    "target_record_id",
    "field",
    "source_coordinate",
    "raw_value",
    "normalized_value",
    "rule",
)


def _legacy_lineage_digest(table: pa.Table) -> str:
    # The historical QES table cannot be serialized as Parquet because required
    # fields contain nulls. Preserve its exact schema and rows without repair.
    payload = encode_json(
        {
            "arrow_schema": table.schema.serialize().to_pybytes().hex(),
            "rows": table.to_pylist(),
        }
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _complete_qes_lineage(facts: pa.Table, legacy: pa.Table) -> pa.Table:
    """Preserve six original fields and complete mandatory evidenced metadata.

    The frozen legacy reader writes only these six fields to a full schema,
    leaving required identities/context null. Completion belongs to this new
    operation path; no historical output, source value or native pin is rewritten.
    """
    targets = {row["record_id"]: row for row in facts.to_pylist()}
    _require(len(targets) == facts.num_rows)
    rows = []
    for item in legacy.to_pylist():
        _require(item["target_record_id"] in targets)
        target = targets[item["target_record_id"]]
        values = {key: item[key] for key in _LINEAGE_VALUES}
        record_id = (
            "sha256:"
            + hashlib.sha256(
                f"{item['target_record_id']}\0{item['field']}\0{item['source_coordinate']}".encode()
            ).hexdigest()
        )
        rows.append(
            {
                **{
                    key: target[key]
                    for key in recordset_schema("field_lineage", version="v2").names
                    if key in target
                },
                **values,
                "record_id": record_id,
                "recordset": "field_lineage",
                "transformation_id": _QES_LINEAGE_COMPLETION,
                "quality_flags": [
                    *target["quality_flags"],
                    "canonical_lineage_source_context_completed",
                ],
            }
        )
    return pa.Table.from_pylist(rows, recordset_schema("field_lineage", version="v2"))


def context_source_profile(profile: str) -> ContextSourceProfile:
    """Return the fixed reviewed cohort; candidate metadata cannot define it."""
    return _profile(profile)


@dataclass(frozen=True, slots=True)
class CanonicalContextProjection:
    """Verified canonical tables with their original common evidence closure."""

    facts: pa.Table
    lineage: pa.Table
    receipt: dict[str, Any]
    operation: context_operations.VerifiedContextOperation


def read_canonical_context(  # noqa: PLR0913 - independent pin and exact reviewed context
    source: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
) -> CanonicalContextProjection:
    """Verify the operation first, then reuse its source's pure canonical mapping.

    This is read-only and grants no source, rights, currency or analytical
    admission. Complete common evidence remains reachable by the operation pin.
    """
    definition = _profile(profile)
    _require(
        (expected_sha256, source_locator, source_vintage, observed_at)
        == (
            definition.source_sha256,
            definition.source_locator,
            definition.source_vintage,
            definition.observed_at,
        )
    )
    verified = context_operations.read_context(
        source,
        output_dir,
        manifest_sha256=manifest_sha256,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    )
    facts, lineage = _canonicalize(verified, profile, definition)
    lineage_completion = None
    if profile == "qes-june2026-table8/v1":
        legacy_lineage = lineage
        lineage = _complete_qes_lineage(facts, legacy_lineage)
        lineage_completion = {
            "transformation_id": _QES_LINEAGE_COMPLETION,
            "reason": "legacy_qes_lineage_required_identity_and_context_fields_null",
            "legacy_lineage_sha256": _legacy_lineage_digest(legacy_lineage),
            "legacy_digest_encoding": "canonical_json_with_serialized_arrow_schema/v1",
            "legacy_fields_preserved": list(_LINEAGE_VALUES),
            "metadata_source": (
                "verified_canonical_target_facts_and_original_common_evidence"
            ),
            "historical_outputs_unchanged": True,
        }
    validate_table(definition.recordset, facts, version=definition.version)
    validate_table("field_lineage", lineage, version=definition.version)
    _require(facts.num_rows == len(verified.common_output.records))
    receipt = {
        "schema_version": _SCHEMA,
        "status": "verified_source_faithful_projection",
        "profile": profile,
        "source_object_sha256": expected_sha256,
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": observed_at,
        "source_manifest_sha256": manifest_sha256,
        "source_manifest_schema_version": verified.manifest["schema_version"],
        "native_compatibility_schema_version": verified.manifest[
            "native_extraction_schema_version"
        ],
        "common_evidence_sha256": hashlib.sha256(
            encode_json(asdict(verified.common_output)).encode()
        ).hexdigest(),
        "common_evidence_counts": {
            "records": len(verified.common_output.records),
            "lineage": len(verified.common_output.lineage),
            "losses": len(verified.common_output.losses),
            "dimensions": len(verified.common_output.dimensions),
            "dimension_links": len(verified.common_output.dimension_links),
        },
        "transformation_id": definition.transformation,
        "recordset": definition.recordset,
        "recordset_version": definition.version,
        "input_records": len(verified.common_output.records),
        "output_records": facts.num_rows,
        "lineage_records": lineage.num_rows,
        "canonical_fields": "existing_source_faithful_fact_transform_unchanged",
        "lineage_completion": lineage_completion,
        "complete_common_provenance": (
            "retained_in_independently_pinned_source_operation_manifest"
        ),
        "rights_state": "not_evaluated",
        "denominator_selection": "not_performed",
        "currency_admission": "not_performed",
        "approved_joins": "none",
        "publication": "not_performed",
    }
    return CanonicalContextProjection(facts, lineage, receipt, verified)


def project_context_operation(  # noqa: PLR0913 - preserve the existing tuple API
    source: Path,
    output_dir: Path,
    *,
    manifest_sha256: str,
    profile: str,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Project independently verified operations without discarding common evidence."""
    result = read_canonical_context(
        source,
        output_dir,
        manifest_sha256=manifest_sha256,
        profile=profile,
        expected_sha256=expected_sha256,
        source_vintage=source_vintage,
        source_locator=source_locator,
        observed_at=observed_at,
    )
    return result.facts, result.lineage, result.receipt
