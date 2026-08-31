"""Additive structural contracts; not row validation or source promotion.

Existing source-specific v1 Parquet packages retain their schemas and bytes.
Decimal128(38,18) is a bounded DuckDB-compatible carrier, not a change to
source units or precision. Projections must reject values outside that range,
never round or drop them, and must retain the source precision/scale,
validate semantic invariants and preserve field lineage before using these
shapes. Unknown valid times remain null; observation time is not capture proof.
"""

from __future__ import annotations

from types import MappingProxyType

import pyarrow as pa

_COMMON = (
    pa.field("record_id", pa.string(), nullable=False),
    pa.field("schema_version", pa.string(), nullable=False),
    pa.field("recordset", pa.string(), nullable=False),
    pa.field("domain", pa.string(), nullable=False),
    pa.field("source_object_sha256", pa.string(), nullable=False),
    pa.field("source_observation_id", pa.string()),
    pa.field("source_locator", pa.string(), nullable=False),
    pa.field("source_vintage", pa.string(), nullable=False),
    pa.field("valid_time_start", pa.date32()),
    pa.field("valid_time_end", pa.date32()),
    pa.field("valid_time_status", pa.string(), nullable=False),
    pa.field("period_token", pa.string()),
    pa.field("observed_at", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("observation_context", pa.string(), nullable=False),
    pa.field("rights_state", pa.string(), nullable=False),
    pa.field(
        "quality_flags", pa.list_(pa.field("element", pa.string())), nullable=False
    ),
    pa.field("transformation_id", pa.string(), nullable=False),
    pa.field("lineage_id", pa.string(), nullable=False),
    pa.field("source_record_id", pa.string()),
    pa.field("source_schema_version", pa.string(), nullable=False),
)
_FACT = (
    pa.field("measure", pa.string(), nullable=False),
    pa.field("amount", pa.decimal128(38, 18)),
    pa.field("value_token", pa.string()),
    pa.field("null_reason", pa.string()),
    pa.field("source_decimal_precision", pa.int16()),
    pa.field("source_decimal_scale", pa.int16()),
    pa.field("unit", pa.string()),
    pa.field("currency", pa.string()),
    pa.field("price_basis", pa.string()),
    pa.field("base_period", pa.string()),
    pa.field("denominator_definition", pa.string()),
    pa.field("amount_type", pa.string()),
    pa.field("source_label", pa.string(), nullable=False),
)
_FIELDS = MappingProxyType(
    {
        "source_inventory": (
            pa.field("source_coordinate", pa.string(), nullable=False),
            pa.field("item_kind", pa.string(), nullable=False),
            pa.field("disposition", pa.string(), nullable=False),
            pa.field("reason", pa.string(), nullable=False),
            pa.field("source_fingerprint", pa.string()),
        ),
        "appropriation_fact": (
            *_FACT,
            pa.field("vote", pa.string()),
            pa.field("appropriation", pa.string()),
            pa.field("department", pa.string()),
            pa.field("portfolio", pa.string()),
            pa.field("classification_ids", pa.list_(pa.field("element", pa.string()))),
        ),
        "health_spending_fact": (
            *_FACT,
            pa.field("institutional_coverage", pa.string()),
            pa.field("accounting_basis", pa.string()),
        ),
        "fiscal_context_fact": (
            *_FACT,
            pa.field("institutional_coverage", pa.string()),
            pa.field("accounting_basis", pa.string()),
            pa.field("seasonal_adjustment", pa.string()),
        ),
        "pharmaceutical_budget_fact": (
            *_FACT,
            pa.field("budget_scope", pa.string()),
            pa.field("funding_regime", pa.string()),
        ),
        "price_population_fact": (
            *_FACT,
            pa.field("series_id", pa.string(), nullable=False),
            pa.field("geography", pa.string()),
            pa.field("population_definition", pa.string()),
            pa.field("seasonal_adjustment", pa.string()),
        ),
        "classification_dimension": (
            pa.field("scheme", pa.string(), nullable=False),
            pa.field("scheme_version", pa.string()),
            pa.field("source_label", pa.string(), nullable=False),
            pa.field("normalized_identifier", pa.string()),
            pa.field("mapping_state", pa.string(), nullable=False),
            pa.field("mapping_method", pa.string()),
            pa.field("mapping_evidence", pa.string()),
        ),
        "field_lineage": (
            pa.field("target_record_id", pa.string(), nullable=False),
            pa.field("field", pa.string(), nullable=False),
            pa.field("source_coordinate", pa.string(), nullable=False),
            pa.field("raw_value", pa.string()),
            pa.field("normalized_value", pa.string()),
            pa.field("rule", pa.string(), nullable=False),
        ),
    }
)
RECORDSETS = MappingProxyType(
    {
        name: pa.schema(
            (*_COMMON, *fields),
            metadata={
                b"domain": b"health_appropriations",
                b"recordset": name.encode(),
                b"schema_version": b"archive-govt-nz.health-recordsets/v1",
                b"contract_scope": b"structural_only",
            },
        )
        for name, fields in _FIELDS.items()
    }
)
_VERSIONS = MappingProxyType({"v1": RECORDSETS})


def recordset_schema(name: str, *, version: str = "v1") -> pa.Schema:
    """Return an immutable shape; reject unknown names/versions with KeyError.

    Arrow shapes do not enforce constant field values, unique IDs, time
    alignment, null-reason consistency, rights or cross-record lineage closure.
    Those require separately tested row and package validators. Published
    Ministry indicators with unresolved units are not mapped by this registry.
    """
    return _VERSIONS[version][name]
