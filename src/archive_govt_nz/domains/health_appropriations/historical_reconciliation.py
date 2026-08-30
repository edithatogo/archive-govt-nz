"""Loss-accounted historical comparison; never rewrite either observation."""

from __future__ import annotations

from decimal import Decimal, localcontext
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.historical import _exact_amount

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_MEASURES = frozenset(("health_spending", "nominal_gdp"))
_MAX_YEAR = 9999


def _year(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= _MAX_YEAR
    ):
        raise ValueError("reconciliation_year")
    return value


def _source_index(
    facts: Sequence[Mapping[str, Any]], lineage: Sequence[Mapping[str, Any]]
) -> dict[tuple[str, int], dict[str, Any]]:
    locations: dict[str, Mapping[str, Any]] = {}
    for row in lineage:
        if row["field"] != "amount":
            continue
        record_id = row["record_id"]
        if record_id in locations:
            raise ValueError("reconciliation_duplicate_lineage")
        locations[record_id] = row
    result = {}
    for fact in facts:
        key = (fact["measure"], _year(fact["year"]))
        amount = fact["amount"]
        if key[0] not in _MEASURES or key in result:
            raise ValueError("reconciliation_source_key")
        if not isinstance(amount, Decimal) or _exact_amount(str(amount)) is None:
            raise ValueError("reconciliation_source_amount")
        location = locations.get(fact["record_id"])
        if (
            location is None
            or location["source_object_sha256"] != fact["source_object_sha256"]
            or not location["source_coordinate"]
        ):
            raise ValueError("reconciliation_source_lineage")
        result[key] = {**fact, "source_coordinate": location["source_coordinate"]}
    return result


def _donor_index(
    oracle: Mapping[str, Sequence[tuple[int, str]]],
) -> dict[tuple[str, int], Decimal]:
    if set(oracle) != _MEASURES:
        raise ValueError("reconciliation_oracle_measures")
    result = {}
    for measure, rows in oracle.items():
        for year, value in rows:
            key = (measure, _year(year))
            if key in result or _exact_amount(value) is None:
                raise ValueError("reconciliation_donor_key_or_amount")
            result[key] = Decimal(value)
    return result


def _comparison(
    source: Mapping[str, Any] | None, donor: Decimal | None
) -> tuple[str, str, str | None]:
    if source is None:
        return "donor_only", "donor_year_absent_from_source", None
    if donor is None:
        annotated = source["year_label"] != str(source["year"])
        return (
            "source_only",
            "annotated_year_absent_from_donor"
            if annotated
            else "source_year_absent_from_donor",
            None,
        )
    if source["amount"] == donor:
        return "exact_match", "exact_numeric_match", "0"
    # Canonical source amounts have 38 digits; widen precision for subtraction.
    with localcontext() as context:
        context.prec = 76
        delta = str(source["amount"] - donor)
    return "value_difference", "source_numeric_value_differs_from_donor", delta


def compare_historical(
    facts: Sequence[Mapping[str, Any]],
    lineage: Sequence[Mapping[str, Any]],
    oracle: Mapping[str, Sequence[tuple[int, str]]],
) -> list[dict[str, Any]]:
    """Compare the complete year union, retaining values, coordinates and reasons.

    Inputs are validated historical records and observed donor table values.
    A difference is not silently repaired or approved for publication: both
    observations remain distinct, including donor-only and source-only years.
    """
    sources = _source_index(facts, lineage)
    donors = _donor_index(oracle)
    result = []
    for measure, year in sorted(sources.keys() | donors.keys()):
        source = sources.get((measure, year))
        donor = donors.get((measure, year))
        status, reason, delta = _comparison(source, donor)
        result.append(
            {
                "schema_version": "archive-govt-nz.health-historical-reconciliation/v1",
                "measure": measure,
                "year": year,
                "status": status,
                "reason": reason,
                "source_record_id": source["record_id"] if source else None,
                "source_object_sha256": source["source_object_sha256"]
                if source
                else None,
                "source_coordinate": source["source_coordinate"] if source else None,
                "source_year_label": source["year_label"] if source else None,
                "source_value": str(source["amount"]) if source else None,
                "donor_value": str(donor) if donor is not None else None,
                "delta": delta,
                "resolution": "retain_both_observations",
            }
        )
    return result
