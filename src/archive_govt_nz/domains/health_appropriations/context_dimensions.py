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
            "series_id",
            "reference_period",
            (
                ("unit", "unit"),
                ("measure", "geography"),
                ("measure", "denominator_selected"),
            ),
        ),
        "qes": (
            "stats_nz_qes_series",
            "series_reference",
            "period_token",
            (("unit", "unit"), ("measure", "adjustment")),
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
        vintage = str(row["source_vintage"])
        source_fields = [("series", identifier_field), ("period", period_field)]
        source_fields.extend((kind, field) for kind, field in extra_fields)
        for kind, field in source_fields:
            value = row.get(field)
            if value is None:
                continue
            value_text = str(value)
            if not value_text.strip():
                continue
            source = lineage_by_record.get(record_id, {}).get(field)
            coordinate = (
                source.source_coordinate
                if source is not None
                else "record:" + record_id + ":" + field
            )
            raw_value = source.raw_value if source is not None else value_text
            label = value_text
            period = str(value_text) if kind == "period" else None
            if kind == "period":
                dimension_kind = "period"
            elif kind == "series":
                dimension_kind = "measure"
            else:
                dimension_kind = kind
            dimension = Dimension(
                kind=dimension_kind,
                scheme=scheme + "/" + kind,
                label=label,
                period_token=period,
            )
            key = dimension_key(dimension)
            assertions.setdefault(
                key,
                Mapping(dimension=dimension, vintage=vintage, version=_VERSION),
            )
            occurrences.append(
                DimensionLink(
                    source_record_id=record_id,
                    kind=dimension.kind,
                    dimension_key=key,
                    source_coordinate=coordinate,
                    raw_value=raw_value,
                    normalized_value=value_text,
                    rule="context-source-literal/retain-exact/v1",
                )
            )
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
