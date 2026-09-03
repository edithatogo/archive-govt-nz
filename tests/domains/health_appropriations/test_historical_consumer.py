"""Canonical historical inputs are verified before pure downstream analysis."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from decimal import Decimal, Inexact, Rounded, getcontext, localcontext

import pyarrow as pa
import pytest
from tests.domains.health_appropriations.test_historical_projection import _inputs

from archive_govt_nz.domains.health_appropriations.historical import (
    _DISPOSITIONS,
    _SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.historical_analysis import (
    analyze_historical,
)
from archive_govt_nz.domains.health_appropriations.historical_consumer import (
    bridge_historical_inputs,
)
from archive_govt_nz.domains.health_appropriations.historical_projection import (
    project_historical,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA


def _json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def _case() -> tuple[dict[str, object], dict[str, pa.Table], bytes]:
    inputs = _inputs()
    projected = project_historical(**inputs)
    return inputs, projected.tables, _json(projected.receipt)


def _series_case(  # noqa: C901 - test builder mirrors mutually exclusive source dependencies
    *,
    second_year: int,
    second_month: int,
    second_basis: str,
    gdp_month: int | None = None,
) -> tuple[dict[str, object], dict[str, pa.Table], bytes]:
    base = _inputs()
    fact0 = base["facts"].to_pylist()[0]
    links0 = base["lineage"].to_pylist()

    def variant(  # noqa: PLR0913 - explicit source dimensions keep cases legible
        fact: dict[str, object],
        links: list[dict[str, object]],
        index: int,
        *,
        year: int,
        month: int,
        basis: str | None,
        measure: str,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        row = deepcopy(fact)
        label = str(year)
        token = (
            "100.00000000000000000"
            if measure == "nominal_gdp"
            else ("12.00000000000000000" if index == 0 else "15.00000000000000000")
        )
        row.update(
            record_id="sha256:" + str(index + 1) * 64,
            source_observation_id="sha256:" + str(index + 3) * 64,
            lineage_id="sha256:" + str(index + 5) * 64,
            year=year,
            year_label=label,
            amount=Decimal(token),
            source_number_token=token,
            period_end_month=month,
            accounting_basis=basis,
            recordset=(
                "fiscal_context_fact"
                if measure == "nominal_gdp"
                else "health_spending_fact"
            ),
            measure=measure,
            valid_time_end=date(year, month, 31 if month == 3 else 30),
            footnotes=[],
        )
        month_label = "March" if month == 3 else "June"
        context = f"{basis}, {month_label} Years" if basis else f"{month_label} Years"
        result = []
        for original in links:
            link = deepcopy(original)
            link.update(
                lineage_id=row["lineage_id"],
                record_id=row["record_id"],
                source_coordinate=link["source_coordinate"].replace(
                    "'Spending'!", f"'Spending{index}'!"
                ),
            )
            field = link["field"]
            if field == "accounting_basis" and basis is None:
                continue
            link["normalized_value"] = str(row[field])
            if field in {"amount", "source_number_token"}:
                link["raw_value"] = token
            elif field in {"year", "year_label"}:
                link["raw_value"] = label
            elif field == "period_end_month":
                link["raw_value"] = context
            elif field == "valid_time_end":
                link["raw_value"] = (
                    label if link["source_coordinate"].endswith("B5") else context
                )
            elif field == "accounting_basis":
                link["raw_value"] = context
            elif field == "measure":
                link["raw_value"] = (
                    "Nominal GDP" if measure == "nominal_gdp" else "Health"
                )
            elif field == "footnotes":
                continue
            result.append(link)
        return row, result

    variants = [
        variant(
            fact0,
            links0,
            0,
            year=2025,
            month=6,
            basis="PBE Standards",
            measure="health_spending",
        ),
        variant(
            fact0,
            links0,
            1,
            year=second_year,
            month=second_month,
            basis=second_basis,
            measure="health_spending",
        ),
    ]
    if gdp_month is not None:
        variants.append(
            variant(
                fact0,
                links0,
                2,
                year=second_year,
                month=gdp_month,
                basis=None,
                measure="nominal_gdp",
            )
        )
    facts = [item[0] for item in variants]
    links = [link for item in variants for link in item[1]]
    cells = []
    for row, row_links in variants:
        literals = {
            link["source_coordinate"]: link["raw_value"]
            for link in row_links
            if link["field"] != "source_number_format"
        }
        for coordinate, raw_value in sorted(literals.items()):
            normalized = coordinate.endswith("H5")
            cells.append(
                {
                    "source_object_sha256": row["source_object_sha256"],
                    "source_coordinate": coordinate,
                    "raw_value_json": json.dumps(raw_value),
                    "disposition": "normalized" if normalized else "context",
                    "reason": (
                        "literal_historical_observation"
                        if normalized
                        else "historical_context"
                    ),
                    "record_id": row["record_id"] if normalized else None,
                }
            )
    base["facts"] = pa.Table.from_pylist(facts, schema=_SCHEMA)
    base["lineage"] = pa.Table.from_pylist(links, schema=LINEAGE_SCHEMA)
    base["dispositions"] = pa.Table.from_pylist(cells, schema=_DISPOSITIONS)
    base["manifest"]["counts"].update(
        facts=len(facts), lineage=len(links), dispositions=len(cells)
    )
    projected = project_historical(**base)
    return base, projected.tables, _json(projected.receipt)


def test_bridge_is_pure_reversible_and_analysis_equivalent() -> None:
    raw, tables, receipt = _case()
    before_raw = deepcopy(raw)
    before_tables = dict(tables)

    result = bridge_historical_inputs(
        **raw,
        canonical_tables=tables,
        parent_receipt=receipt,
    )

    expected = project_historical(**raw)
    projected_facts = (
        expected.tables["health_spending_fact"].to_pylist()
        + expected.tables["fiscal_context_fact"].to_pylist()
    )
    canonical_analysis = analyze_historical(list(result.inputs))
    raw_analysis = analyze_historical(raw["facts"].to_pylist())
    semantic = (
        "year",
        "yoy_status",
        "yoy_percent",
        "previous_exact_amount",
        "gdp_share_status",
        "gdp_share_percent",
        "gdp_exact_amount",
        "formula_policy",
        "rounding_policy",
    )
    assert [{key: row[key] for key in semantic} for row in canonical_analysis] == [
        {key: row[key] for key in semantic} for row in raw_analysis
    ]
    assert [Decimal(row["exact_amount"]) for row in canonical_analysis] == [
        Decimal(row["exact_amount"]) for row in raw_analysis
    ]
    assert result.parent_receipt == json.loads(receipt)
    assert result.canonical_lineage == tuple(
        expected.tables["field_lineage"].to_pylist()
    )
    assert {row["canonical_record_id"] for row in result.backward_ids} == {
        row["record_id"]
        for table in expected.tables.values()
        for row in table.to_pylist()
    }
    assert {
        (row["canonical_record_id"], row["field"]) for row in result.field_accounting
    } == {
        (row["record_id"], field)
        for row in result.inputs
        for field in (
            "record_id",
            "source_object_sha256",
            "source_vintage",
            "year",
            "measure",
            "unit",
            "amount",
            "accounting_basis",
            "valid_time_end",
            "period_end_month",
        )
    }
    assert result.receipt == {
        "schema_version": "archive-govt-nz.health-historical-consumer/v1",
        "status": "passed",
        "input_fixity": "not_performed",
        "rights_state": "not_evaluated",
        "publication_approval": "not_granted",
        "analysis_execution": "not_performed",
        "new_semantic_assertions": [],
        "canonical_projection_rule": "historical-health-gdp-canonical/v1",
        "input_manifest_sha256": raw["manifest_sha256"],
        "canonical_record_count": sum(table.num_rows for table in tables.values()),
        "consumer_fact_count": len(projected_facts),
        "backward_identity_count": sum(table.num_rows for table in tables.values()),
        "field_accounting_count": len(result.field_accounting),
    }
    assert raw == before_raw
    assert all(tables[name].equals(table) for name, table in before_tables.items())


@pytest.mark.parametrize(
    ("second_year", "second_month", "second_basis", "status"),
    [
        (2026, 6, "PBE Standards", "comparable"),
        (2027, 6, "PBE Standards", "year_gap"),
        (2026, 3, "Cash", "period_change"),
        (2026, 6, "Cash", "accounting_basis_change"),
    ],
)
def test_bridge_preserves_public_analysis_policy(
    second_year: int, second_month: int, second_basis: str, status: str
) -> None:
    raw, tables, receipt = _series_case(
        second_year=second_year,
        second_month=second_month,
        second_basis=second_basis,
    )
    result = bridge_historical_inputs(
        **raw, canonical_tables=tables, parent_receipt=receipt
    )
    canonical = analyze_historical(list(result.inputs))
    source = analyze_historical(raw["facts"].to_pylist())
    assert [row["yoy_status"] for row in canonical] == [
        "no_previous_observation",
        status,
    ]
    assert [row["yoy_status"] for row in canonical] == [
        row["yoy_status"] for row in source
    ]
    assert [row["yoy_percent"] for row in canonical] == [
        row["yoy_percent"] for row in source
    ]


@pytest.mark.parametrize(
    ("gdp_month", "status"), [(6, "aligned"), (3, "period_mismatch")]
)
def test_bridge_preserves_gdp_alignment_policy(gdp_month: int, status: str) -> None:
    raw, tables, receipt = _series_case(
        second_year=2026,
        second_month=6,
        second_basis="PBE Standards",
        gdp_month=gdp_month,
    )
    result = bridge_historical_inputs(
        **raw, canonical_tables=tables, parent_receipt=receipt
    )
    canonical = analyze_historical(list(result.inputs))
    source = analyze_historical(raw["facts"].to_pylist())
    assert canonical[1]["gdp_share_status"] == status
    assert canonical[1]["gdp_share_status"] == source[1]["gdp_share_status"]
    assert canonical[1]["gdp_share_percent"] == source[1]["gdp_share_percent"]


def test_bridge_is_independent_of_valid_raw_physical_order() -> None:
    raw, tables, receipt = _series_case(
        second_year=2026, second_month=6, second_basis="PBE Standards"
    )
    for name in ("facts", "lineage", "dispositions"):
        table = raw[name]
        raw[name] = table.take(list(reversed(range(table.num_rows))))
    result = bridge_historical_inputs(
        **raw, canonical_tables=tables, parent_receipt=receipt
    )
    assert len(result.inputs) == 2


def test_bridge_accounts_every_lineage_reference_and_identity_substitution() -> None:
    raw, tables, receipt = _series_case(
        second_year=2026, second_month=6, second_basis="PBE Standards", gdp_month=6
    )
    result = bridge_historical_inputs(
        **raw, canonical_tables=tables, parent_receipt=receipt
    )
    lineage_ids = {row["record_id"] for row in result.canonical_lineage}
    assert all(
        set(row["canonical_lineage_record_ids"]) <= lineage_ids
        for row in result.field_accounting
    )
    assert all(
        row["state"]
        == (
            "canonical_lineage"
            if row["canonical_lineage_record_ids"]
            else "canonical_metadata_transport"
        )
        for row in result.field_accounting
    )
    substitutions = {
        row["canonical_record_id"]: row["source_record_id"]
        for row in result.backward_ids
    }
    assert all(
        substitutions[row["record_id"]] == row["source_record_id"]
        and row["record_id"] != row["source_record_id"]
        for row in result.inputs
    )


@pytest.mark.parametrize("change", ["value", "schema", "order", "extra"])
def test_bridge_rejects_non_exact_canonical_projection(change: str) -> None:
    raw, tables, receipt = _case()
    changed = dict(tables)
    fact = tables["health_spending_fact"]
    if change == "value":
        rows = fact.to_pylist()
        rows[0]["source_label"] = "changed"
        changed["health_spending_fact"] = pa.Table.from_pylist(rows, schema=fact.schema)
    elif change == "schema":
        changed["health_spending_fact"] = fact.replace_schema_metadata(None)
    elif change == "order":
        changed["field_lineage"] = tables["field_lineage"].take(
            list(reversed(range(tables["field_lineage"].num_rows)))
        )
    else:
        changed["unexpected"] = fact
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(
            **raw, canonical_tables=changed, parent_receipt=receipt
        )


@pytest.mark.parametrize(
    "receipt",
    [b"{}", b'{"x":1}', b'{"x":true}', b'{"x":1.0}', b"not-json"],
)
def test_bridge_rejects_non_exact_parent_receipt(receipt: bytes) -> None:
    raw, tables, _ = _case()
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(**raw, canonical_tables=tables, parent_receipt=receipt)


def test_bridge_rejects_receipt_and_table_resource_bounds() -> None:
    raw, tables, receipt = _case()
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(
            **raw, canonical_tables=tables, parent_receipt=receipt + b" " * (4 << 20)
        )
    oversized = dict(tables)
    oversized["health_spending_fact"] = pa.concat_tables(
        [tables["health_spending_fact"]] * 100_001
    )
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(
            **raw, canonical_tables=oversized, parent_receipt=receipt
        )


def test_bridge_rejects_unrepresentable_canonical_decimal_and_period_contradiction() -> (
    None
):
    raw, tables, receipt = _case()
    rows = tables["health_spending_fact"].to_pylist()
    rows[0]["amount"] = Decimal("12.345678901234560001")
    changed = dict(tables)
    changed["health_spending_fact"] = pa.Table.from_pylist(
        rows, schema=tables["health_spending_fact"].schema
    )
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(
            **raw, canonical_tables=changed, parent_receipt=receipt
        )

    raw, tables, receipt = _case()
    rows = raw["facts"].to_pylist()
    rows[0]["valid_time_end"] = date(2024, 6, 30)
    raw["facts"] = pa.Table.from_pylist(rows, schema=_SCHEMA)
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(**raw, canonical_tables=tables, parent_receipt=receipt)


def test_bridge_ignores_hostile_decimal_context_without_mutating_it() -> None:
    raw, tables, receipt = _case()
    original = str(getcontext())
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        context.clear_flags()
        result = bridge_historical_inputs(
            **raw, canonical_tables=tables, parent_receipt=receipt
        )
        assert len(result.inputs) == 1
        assert context.prec == 2
        assert context.traps[Inexact]
        assert context.traps[Rounded]
        assert not context.flags[Inexact]
        assert not context.flags[Rounded]
    assert str(getcontext()) == original


def test_bridge_rejects_boolean_manifest_pin_and_interrupts_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw, tables, receipt = _case()
    raw["manifest_sha256"] = True
    with pytest.raises(ValueError, match="historical_consumer_contract"):
        bridge_historical_inputs(**raw, canonical_tables=tables, parent_receipt=receipt)
    raw, tables, receipt = _case()

    def interrupt(**_: object) -> object:
        raise KeyboardInterrupt

    monkeypatch.setattr(
        "archive_govt_nz.domains.health_appropriations.historical_consumer.project_historical",
        interrupt,
    )
    with pytest.raises(KeyboardInterrupt):
        bridge_historical_inputs(**raw, canonical_tables=tables, parent_receipt=receipt)
