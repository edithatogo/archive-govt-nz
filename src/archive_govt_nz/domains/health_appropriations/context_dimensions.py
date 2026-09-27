"""Unresolved source-literal mappings for price, population and GDP contexts."""

from __future__ import annotations

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    DimensionLink,
    FieldLineage,
)
from archive_govt_nz.domains.health_appropriations.dimension_mapping import (
    Dimension,
    Mapping,
    dimension_key,
    validate_mappings,
)

_VERSION = "context-source-literal/v1"
_UNKNOWN_FAMILY = "unknown_context_dimension_family"


def _source_dimension(
    row: dict[str, object],
    *,
    scheme: str,
    kind: str,
    field: str,
    source: FieldLineage | None,
) -> tuple[Mapping, DimensionLink] | None:
    """Build one assertion only when a source cell backs the literal."""
    value = row.get(field)
    if value is None or not str(value).strip() or source is None:
        return None
    record_id = str(row["record_id"])
    value_text = str(value)
    dimension_kind = kind
    if kind == "period":
        dimension_kind = "period"
    elif kind == "series":
        dimension_kind = "measure"
    dimension = Dimension(
        kind=dimension_kind,
        scheme=scheme + "/" + kind,
        label=value_text,
        period_token=value_text if kind == "period" else None,
    )
    key = dimension_key(dimension)
    mapping = Mapping(
        dimension=dimension,
        vintage=str(row["source_vintage"]),
        version=_VERSION,
    )
    link = DimensionLink(
        source_record_id=record_id,
        kind=dimension.kind,
        dimension_key=key,
        source_coordinate=source.source_coordinate,
        raw_value=source.raw_value,
        normalized_value=value_text,
        rule="context-source-literal/retain-exact/v1",
    )
    return mapping, link


def context_source_dimensions(
    records: tuple[dict[str, object], ...],
    lineage: tuple[FieldLineage, ...],
    *,
    family: str,
) -> tuple[tuple[Mapping, ...], tuple[DimensionLink, ...]]:
    """Retain source labels and periods as unresolved assertions with row links."""
    profiles = {
        "cpi": (
            "stats_nz_cpi_series",
            "series_reference",
            "period_token",
            (("unit", "unit"), ("measure", "index_base")),
        ),
        "population": (
            "stats_nz_population_table",
            None,
            "period_token",
            (),
        ),
        "qes": (
            "stats_nz_qes_series",
            "series_id",
            "period_token",
            (("unit", "unit_label"), ("measure", "adjustment")),
        ),
        "gdp": (
            "stats_nz_gdp_series",
            "series_reference",
            "period_token",
            (("unit", "unit"), ("measure", "price_basis")),
        ),
    }
    if family not in profiles:
        raise ValueError(_UNKNOWN_FAMILY)
    scheme, identifier_field, period_field, extra_fields = profiles[family]
    lineage_by_record: dict[str, dict[str, FieldLineage]] = {}
    for item in lineage:
        lineage_by_record.setdefault(item.record_id, {})[item.field] = item
    assertions: dict[str, Mapping] = {}
    occurrences: list[DimensionLink] = []
    for row in records:
        record_id = str(row["record_id"])
        source_fields = []
        if identifier_field is not None:
            source_fields.append(("series", identifier_field))
        source_fields.append(("period", period_field))
        source_fields.extend((kind, field) for kind, field in extra_fields)
        for kind, field in source_fields:
            source = lineage_by_record.get(record_id, {}).get(field)
            result = _source_dimension(
                row, scheme=scheme, kind=kind, field=field, source=source
            )
            if result is None:
                continue
            mapping, link = result
            assertions.setdefault(link.dimension_key, mapping)
            occurrences.append(link)
    mappings = validate_mappings(tuple(assertions.values()))
    links = tuple(
        sorted(
            occurrences,
            key=lambda link: (
                link.source_record_id,
                link.kind,
                link.dimension_key,
                link.source_coordinate,
            ),
        )
    )
    return mappings, links
