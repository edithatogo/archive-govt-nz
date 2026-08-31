"""Pure historical shape/semantic projection, not input fixity or publication."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.historical import (
    _DISPOSITIONS,
    _SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.schemas.health_recordsets import recordset_schema

_RULE = "historical-health-gdp-canonical/v1"
_SOURCE_RULE = "treasury-historical-health-gdp/v1"
_FACT_VERSION = "archive-govt-nz.health-historical-silver/v1"
_MANIFEST_VERSION = "archive-govt-nz.health-historical-extraction/v1"
_VERSION = "archive-govt-nz.health-recordsets/v1"
_NUMBER_BOUND = 128
_MAX_YEAR = 9999
_MAX_ROWS = 100_000
_MARCH = 3
_END_DEPENDENCIES = 2
# Parquet changes only these list child names on the known source schema.
_TRANSPORT_SCHEMA = pa.schema(
    [
        field.with_type(pa.list_(pa.field("element", pa.string())))
        if field.name in {"quality_flags", "footnotes"}
        else field
        for field in _SCHEMA
    ],
    metadata=_SCHEMA.metadata,
)
_PERIOD_CONTEXT = MappingProxyType(
    {
        "Cash, March Years": 3,
        "Cash, June Years": 6,
        "IFRS, June Years": 6,
        "PBE Standards, June Years": 6,
        "March Years": 3,
        " March Years": 3,
        "June Years": 6,
    }
)
_BASIS_CONTEXT = MappingProxyType(
    {
        "Cash, March Years": "Cash",
        "Cash, June Years": "Cash",
        "old-GAAP": "old-GAAP",
        "IFRS, June Years": "IFRS",
        "PBE Standards, June Years": "PBE Standards",
    }
)
_MAP = MappingProxyType(
    {
        "amount": ("amount",),
        "source_number_token": ("value_token",),
        "year_label": ("period_token",),
        "unit": ("unit", "currency"),
        "measure": ("measure", "source_label"),
        "accounting_basis": ("accounting_basis",),
        "valid_time_end": ("valid_time_end",),
    }
)
_RETAINED = frozenset({"year", "period_end_month", "source_number_format", "footnotes"})
_CONTEXT = (
    "source_object_sha256",
    "source_locator",
    "source_vintage",
    "rights_state",
    "observed_at",
)


@dataclass(frozen=True)
class HistoricalProjection:
    """Fresh canonical tables and loss accounting over caller-supplied inputs."""

    tables: dict[str, pa.Table]
    receipt: dict[str, Any]


def _require(condition: object) -> None:
    if not condition:
        message = "historical_projection_contract"
        raise ValueError(message)


def _id(*parts: object) -> str:
    payload = json.dumps(
        parts,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _digest(value: object, *, prefixed: bool = False) -> None:
    _require(isinstance(value, str))
    _require(
        re.fullmatch(("sha256:" if prefixed else "") + r"[0-9a-f]{64}", str(value))
        is not None
    )


def _amount(value: object, token: object) -> Decimal:
    _require(isinstance(value, Decimal) and value.is_finite())
    _require(isinstance(token, str) and 0 < len(token) <= _NUMBER_BOUND)
    _require(
        re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", str(token))
        is not None
    )
    number = Decimal(str(token))
    _require(number.is_finite() and number == value)
    parts = number.as_tuple()
    exponent = parts.exponent
    _require(isinstance(exponent, int))
    coefficient = int("".join(map(str, parts.digits)))
    shift = int(exponent) + 18
    # Bound before exponentiation; no ambient Decimal arithmetic/rounding.
    _require(-_NUMBER_BOUND <= shift <= _NUMBER_BOUND)
    if shift < 0:
        coefficient, remainder = divmod(coefficient, 10**-shift)
        _require(remainder == 0)
    else:
        coefficient *= 10**shift
    _require(coefficient < 10**38)
    return number


def _fact(row: dict[str, Any], context: dict[str, Any]) -> None:
    _require(all(row[key] == context[key] for key in _CONTEXT))
    _require(
        row["schema_version"] == _FACT_VERSION
        and row["domain"] == "health_appropriations"
    )
    _require(row["transformation_id"] == _SOURCE_RULE)
    for field in ("record_id", "lineage_id", "source_observation_id"):
        _digest(row[field], prefixed=True)
    _require(row["recordset"] in ("health_spending_fact", "fiscal_context_fact"))
    health = row["recordset"] == "health_spending_fact"
    _require(row["measure"] == ("health_spending" if health else "nominal_gdp"))
    _require(
        row["accounting_basis"] in ("Cash", "old-GAAP", "IFRS", "PBE Standards")
        if health
        else row["accounting_basis"] is None
    )
    _require(row["unit"] == "NZD_millions" and row["amount_type"] is None)
    _require(row["valid_time_start"] is None)
    _require(
        all(
            row[field] is None
            for field in (
                "donor_table",
                "donor_row_number",
                "department",
                "appropriation_name",
                "functional_classification",
                "portfolio_name",
            )
        )
    )
    year, month = row["year"], row["period_end_month"]
    _require(type(year) is int and 1 <= year <= _MAX_YEAR and month in (3, 6))
    _require(row["valid_time_end"] == date(year, month, 31 if month == _MARCH else 30))
    _require(
        isinstance(row["year_label"], str)
        and re.fullmatch(str(year) + r"[†*^#]*", row["year_label"]) is not None
    )
    flags = row["quality_flags"]
    _require(
        isinstance(flags, list)
        and all(isinstance(flag, str) and flag for flag in flags)
    )
    _require(
        {"period_start_not_provided", "cross_basis_comparability_not_asserted"}
        <= set(flags)
    )
    _require(
        isinstance(row["footnotes"], list)
        and all(isinstance(note, str) for note in row["footnotes"])
    )
    _amount(row["amount"], row["source_number_token"])


def _validated(
    manifest: dict[str, Any],
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require(
        manifest["schema_version"] == _MANIFEST_VERSION
        and manifest["status"] == "passed"
    )
    _require(
        manifest["rights_state"] == "not_evaluated"
        and manifest["transformation_id"] == _SOURCE_RULE
    )
    _digest(manifest["source_object_sha256"])
    _require(
        all(
            isinstance(manifest[key], str) and manifest[key].strip()
            for key in ("source_locator", "source_vintage")
        )
    )
    observed = datetime.fromisoformat(manifest["observed_at"])
    _require(observed.tzinfo is not None)
    context = {**manifest, "observed_at": observed}
    for table, schema, name in (
        (facts, _SCHEMA, "facts"),
        (lineage, LINEAGE_SCHEMA, "lineage"),
        (dispositions, _DISPOSITIONS, "dispositions"),
    ):
        _require(
            table.schema.equals(schema, check_metadata=True)
            or (
                name == "facts"
                and table.schema.equals(_TRANSPORT_SCHEMA, check_metadata=True)
            )
        )
        _require(0 < table.num_rows <= _MAX_ROWS)
        _require(
            type(manifest["counts"][name]) is int
            and manifest["counts"][name] == table.num_rows
        )
    _require(
        type(manifest["counts"]["rejected"]) is int
        and manifest["counts"]["rejected"] == 0
    )
    rows, links, cells = (
        facts.to_pylist(),
        lineage.to_pylist(),
        dispositions.to_pylist(),
    )
    for row in rows:
        _fact(row, context)
    indexed = {row["record_id"]: row for row in rows}
    _require(len(indexed) == len(rows))
    _require(
        len({(row["measure"], row["year"], row["period_end_month"]) for row in rows})
        == len(rows)
    )
    coordinates = {cell["source_coordinate"]: cell for cell in cells}
    _require(len(coordinates) == len(cells))
    _require(
        Counter(
            cell["record_id"] for cell in cells if cell["disposition"] == "normalized"
        )
        == Counter(indexed.keys())
    )
    for cell in cells:
        _require(cell["source_object_sha256"] == manifest["source_object_sha256"])
        _require(
            isinstance(cell["source_coordinate"], str) and cell["source_coordinate"]
        )
        _require(cell["disposition"] in ("normalized", "context", "preserved_only"))
        _require(
            cell["record_id"] in indexed
            if cell["disposition"] == "normalized"
            else cell["record_id"] is None
        )
    seen: set[str] = set()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in links:
        _require(
            link["record_id"] in indexed and link["field"] in set(_MAP) | _RETAINED
        )
        row = indexed[link["record_id"]]
        _require(
            all(
                link[key] == row[key]
                for key in ("lineage_id", "source_object_sha256", "source_locator")
            )
        )
        _require(
            link["rule"] == _SOURCE_RULE and link["source_coordinate"] in coordinates
        )
        _require(link["normalized_value"] == str(row[link["field"]]))
        if link["field"] != "source_number_format":
            _require(
                json.loads(coordinates[link["source_coordinate"]]["raw_value_json"])
                == link["raw_value"]
            )
        identity = _id(link)
        _require(identity not in seen)
        seen.add(identity)
        grouped[link["record_id"]].append(link)
    for row in rows:
        _dependencies(row, grouped[row["record_id"]], coordinates)
    return rows, links


def _dependencies(
    row: dict[str, Any], links: list[dict[str, Any]], cells: dict[str, dict[str, Any]]
) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in links:
        groups[link["field"]].append(link)
    for field in (
        "amount",
        "source_number_token",
        "source_number_format",
        "year",
        "year_label",
        "period_end_month",
        "unit",
        "measure",
    ):
        _require(len(groups[field]) == 1)
    _require(
        len(groups["accounting_basis"])
        == (1 if row["accounting_basis"] is not None else 0)
    )
    _require(len(groups["valid_time_end"]) == _END_DEPENDENCIES)
    end_coordinates = {link["source_coordinate"] for link in groups["valid_time_end"]}
    _require(
        end_coordinates
        == {
            groups[field][0]["source_coordinate"]
            for field in ("year", "period_end_month")
        }
    )
    context_values = {
        groups[field][0]["source_coordinate"]: groups[field][0]["raw_value"]
        for field in ("year", "period_end_month")
    }
    _require(
        all(
            link["raw_value"] == context_values[link["source_coordinate"]]
            for link in groups["valid_time_end"]
        )
    )
    _require(groups["year"][0]["raw_value"] == row["year_label"])
    _require(groups["year_label"][0]["raw_value"] == row["year_label"])
    _require(
        groups["year_label"][0]["source_coordinate"]
        == groups["year"][0]["source_coordinate"]
    )
    _require(
        _PERIOD_CONTEXT.get(groups["period_end_month"][0]["raw_value"])
        == row["period_end_month"]
    )
    _require(groups["unit"][0]["raw_value"] == "$ millions")
    _require(
        groups["source_number_format"][0]["raw_value"] == row["source_number_format"]
    )
    if row["accounting_basis"] is not None:
        _require(
            _BASIS_CONTEXT.get(groups["accounting_basis"][0]["raw_value"])
            == row["accounting_basis"]
        )
    amount = groups["amount"][0]
    _require(amount["raw_value"] == row["source_number_token"])
    _require(
        groups["source_number_token"][0]["source_coordinate"]
        == amount["source_coordinate"]
    )
    _require(
        groups["source_number_token"][0]["raw_value"] == row["source_number_token"]
    )
    _require(
        groups["measure"][0]["raw_value"]
        == ("Health" if row["measure"] == "health_spending" else "Nominal GDP")
    )
    cell = cells[amount["source_coordinate"]]
    _require(
        cell["record_id"] == row["record_id"] and cell["disposition"] == "normalized"
    )
    _require(
        Counter(link["raw_value"] for link in groups["footnotes"])
        == Counter(row["footnotes"])
    )


def _canonical(row: dict[str, Any], pin: str) -> dict[str, Any]:
    result = dict.fromkeys(recordset_schema(row["recordset"]).names)
    for name in (
        *_CONTEXT,
        "source_observation_id",
        "quality_flags",
        "valid_time_end",
        "measure",
        "amount",
        "unit",
        "accounting_basis",
    ):
        result[name] = row[name]
    result["amount"] = pa.scalar(row["amount"], type=pa.decimal128(38, 18)).as_py()
    record_id = _id(
        _RULE,
        pin,
        row["source_object_sha256"],
        row["source_vintage"],
        row["recordset"],
        row["record_id"],
    )
    result.update(
        record_id=record_id,
        schema_version=_VERSION,
        recordset=row["recordset"],
        domain="health_appropriations",
        source_record_id=row["record_id"],
        source_schema_version=_FACT_VERSION,
        transformation_id=_RULE,
        lineage_id=_id(record_id, "lineage"),
        observation_context="caller_supplied_extraction_observation",
        valid_time_status="end_known_start_unknown",
        period_token=row["year_label"],
        value_token=row["source_number_token"],
        source_decimal_precision=38,
        source_decimal_scale=17,
        currency="NZD",
        source_label="Health" if row["measure"] == "health_spending" else "Nominal GDP",
    )
    return result


def project_historical(
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> HistoricalProjection:
    """Project caller-verified inputs without I/O, capture or fixity assertions.

    The supplied manifest digest is syntax-checked identity, not reverified bytes.
    Callers retain and verify the complete source package. No input row is edited.
    Unsupported values fail the whole call; retained-only lineage is accounted.
    """
    _digest(manifest_sha256)
    rows, links = _validated(manifest, facts, lineage, dispositions)
    canonical = {row["record_id"]: _canonical(row, manifest_sha256) for row in rows}
    output: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in ("health_spending_fact", "fiscal_context_fact", "field_lineage")
    }
    for row in canonical.values():
        output[row["recordset"]].append(row)
    accounting = []
    for link in links:
        fact = canonical[link["record_id"]]
        source_identity = _id(manifest_sha256, link)
        targets = []
        for field in _MAP.get(link["field"], ()):
            record = {
                name: fact[name]
                for name in recordset_schema("field_lineage").names
                if name in fact
            }
            record.update(
                record_id=_id(
                    _RULE,
                    fact["record_id"],
                    field,
                    link["source_coordinate"],
                    source_identity,
                ),
                recordset="field_lineage",
                source_schema_version=_MANIFEST_VERSION,
                target_record_id=fact["record_id"],
                field=field,
                source_coordinate=link["source_coordinate"],
                raw_value=link["raw_value"],
                normalized_value=str(fact[field]),
                rule=_RULE,
            )
            output["field_lineage"].append(record)
            targets.append(record["record_id"])
        accounting.append(
            {
                "source_lineage_id": source_identity,
                "state": "mapped" if targets else "retained_only",
                "target_lineage_record_ids": sorted(targets),
            }
        )
    tables = {
        name: pa.Table.from_pylist(
            sorted(values, key=lambda row: row["record_id"]),
            schema=recordset_schema(name),
        )
        for name, values in output.items()
    }
    return HistoricalProjection(
        tables,
        {
            "schema_version": "archive-govt-nz.health-historical-projection/v1",
            "status": "passed",
            "input_fixity": "not_performed",
            "input_manifest_sha256": manifest_sha256,
            "rights_state": "not_evaluated",
            "publication_approval": "not_granted",
            "lineage_accounting": sorted(
                accounting, key=lambda row: row["source_lineage_id"]
            ),
            "retained_source_fields": sorted(
                _RETAINED | {"raw_values_json", "footnotes"}
            ),
        },
    )
