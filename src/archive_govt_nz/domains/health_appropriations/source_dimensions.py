"""Unresolved, source-literal dimensions for the Budget expenditure profile."""

from __future__ import annotations

import re
from dataclasses import dataclass

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    DimensionLink,
    FieldLineage,
)
from archive_govt_nz.domains.health_appropriations.dimension_mapping import (
    Dimension,
    Mapping,
    dimension_key,
    source_reference,
    validate_mappings,
)

_VERSION = "budget-expenditure-source-literal/v1"
_MAX_FACTS = 1000
_SOURCE_FIELDS = (
    ("vote", "budget_workbook_vote_source_label", "raw:Vote", "vote"),
    (
        "appropriation",
        "budget_workbook_appropriation_source_label",
        "appropriation_name",
        "appropriation_name",
    ),
    (
        "department",
        "budget_workbook_department_source_label",
        "department",
        "department",
    ),
    (
        "portfolio",
        "budget_workbook_portfolio_source_label",
        "portfolio_name",
        "portfolio_name",
    ),
    (
        "amount_type",
        "budget_workbook_amount_type_source_label",
        "amount_type",
        "amount_type",
    ),
    (
        "functional_classification",
        "budget_workbook_functional_classification_source_label",
        "functional_classification",
        "functional_classification",
    ),
)
_LABEL_TARGET_REASON = (
    "The captured field is a source literal; no crosswalk with an effective "
    "period is evidenced."
)


@dataclass(frozen=True, slots=True)
class _DimensionSpec:
    kind: str
    scheme: str
    label: str
    source: FieldLineage
    period_token: str | None = None
    coordinate: str | None = None
    raw_value: str | None = None
    use_source_raw_value: bool = True
    normalized_value: str | None = None
    rule: str | None = None
    unresolved_reason: str = "No source-backed canonical target or effective period."


@dataclass(slots=True)
class _DimensionBuilder:
    assertions: dict[str, Mapping]
    occurrences: list[DimensionLink]

    def add(
        self,
        source_record_id: str,
        vintage: str,
        source_sha256: str,
        spec: _DimensionSpec,
    ) -> None:
        dimension = Dimension(
            kind=spec.kind,
            scheme=spec.scheme,
            label=spec.label,
            period_token=spec.period_token,
        )
        key = dimension_key(dimension)
        coordinate = spec.coordinate or spec.source.source_coordinate
        reference = source_reference(source_sha256, coordinate)
        assertion = Mapping(
            dimension=dimension,
            vintage=vintage,
            version=_VERSION,
            unresolved_reason=spec.unresolved_reason,
            source_references=(reference,),
        )
        existing = self.assertions.get(key)
        if existing is not None:
            assertion = Mapping(
                dimension=dimension,
                vintage=vintage,
                version=_VERSION,
                unresolved_reason=spec.unresolved_reason,
                source_references=tuple(
                    sorted(set(existing.source_references) | {reference})[:32]
                ),
            )
        self.assertions[key] = assertion
        raw_value = (
            spec.source.raw_value if spec.use_source_raw_value else spec.raw_value
        )
        self.occurrences.append(
            DimensionLink(
                source_record_id=source_record_id,
                kind=spec.kind,
                dimension_key=key,
                source_coordinate=spec.coordinate or spec.source.source_coordinate,
                raw_value=raw_value,
                normalized_value=spec.normalized_value or spec.label,
                rule=spec.rule or spec.source.rule,
            )
        )


def _fact_specs(
    fact: dict[str, object], source_links: dict[str, FieldLineage]
) -> tuple[_DimensionSpec, ...]:
    specs: list[_DimensionSpec] = []
    for kind, scheme, field, fact_field in _SOURCE_FIELDS:
        source = source_links.get(field)
        value = fact.get(fact_field)
        if source is None or source.raw_value is None or not source.raw_value.strip():
            message = "budget_dimension_source_field_missing"
            raise ValueError(message)
        if value is not None and str(value) != source.normalized_value:
            message = "budget_dimension_fact_lineage_mismatch"
            raise ValueError(message)
        specs.append(
            _DimensionSpec(
                kind=kind,
                scheme=scheme,
                label=source.raw_value,
                source=source,
                unresolved_reason=_LABEL_TARGET_REASON,
            )
        )

    period = source_links.get("year")
    if period is None or period.raw_value is None:
        message = "budget_period_source_field_missing"
        raise ValueError(message)
    specs.append(
        _DimensionSpec(
            kind="period",
            scheme="budget_workbook_financial_year_source_token",
            label=period.raw_value,
            source=period,
            period_token=period.raw_value,
            unresolved_reason=(
                "The source retains a year token but the admitted evidence does "
                "not establish calendar bounds or a period join."
            ),
        )
    )

    amount = source_links.get("amount")
    if amount is None:
        message = "budget_amount_source_field_missing"
        raise ValueError(message)
    amount_cell = amount.source_coordinate.rsplit("!", 1)[-1]
    if re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]*", amount_cell) is None:
        message = "budget_amount_coordinate_invalid"
        raise ValueError(message)
    column = re.sub(r"\d+$", "", amount_cell)
    specs.extend(
        (
            _DimensionSpec(
                kind="unit",
                scheme="budget_workbook_amount_unit_source_header",
                label="Amount $000",
                source=amount,
                coordinate=f"'Raw Data'!{column}1",
                raw_value="Amount $000",
                use_source_raw_value=False,
                rule="budget-expenditure/amount-header/v1",
                unresolved_reason=(
                    "The source header establishes the displayed scale only; "
                    "currency semantics are not evidenced."
                ),
            ),
            _DimensionSpec(
                kind="measure",
                scheme="budget_expenditure_measure_rule",
                label="appropriation_amount",
                source=amount,
                raw_value=None,
                use_source_raw_value=False,
                rule="budget-expenditure/measure-rule/v1",
                unresolved_reason=(
                    "This adapter measure is source-profile specific; "
                    "cross-source equivalence is not evidenced."
                ),
            ),
        )
    )
    return tuple(specs)


def budget_source_dimensions(
    facts: tuple[dict[str, object], ...],
    lineage: tuple[FieldLineage, ...],
) -> tuple[tuple[Mapping, ...], tuple[DimensionLink, ...]]:
    """Create stable unresolved assertions and cell links from Budget facts.

    Identity is scoped to the literal source scheme and exact source label.
    Financial-year dates, classification crosswalks, currency and economic
    categories are deliberately not inferred. Unit and measure labels are
    adapter assertions linked to the source Amount $000 column, not mappings.
    """
    if len(facts) > _MAX_FACTS:
        message = "budget_dimension_fact_limit"
        raise ValueError(message)
    vintages = {row.get("source_vintage") for row in facts}
    if len(vintages) > 1:
        message = "budget_dimension_single_vintage_required"
        raise ValueError(message)
    links_by_record: dict[str, dict[str, FieldLineage]] = {}
    for item in lineage:
        links_by_record.setdefault(item.record_id, {})[item.field] = item
    builder = _DimensionBuilder({}, [])
    for fact in facts:
        record_id = str(fact["record_id"])
        source_links = links_by_record.get(record_id, {})
        vintage = str(fact["source_vintage"])
        for spec in _fact_specs(fact, source_links):
            builder.add(
                record_id,
                vintage,
                str(fact["source_object_sha256"]),
                spec,
            )

    dimensions = validate_mappings(tuple(builder.assertions.values()))
    occurrences = tuple(
        sorted(
            builder.occurrences,
            key=lambda row: (
                row.source_record_id,
                row.kind,
                row.dimension_key,
                row.source_coordinate,
            ),
        )
    )
    return dimensions, occurrences
