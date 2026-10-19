"""Source-native Budget 2019 Silver with exact BIFF8 stored-integer evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from openpyxl.utils.cell import get_column_letter

from archive_govt_nz.domains.health_appropriations import (
    biff8_projection,
    biff8_records,
    budget_expenditure_2020,
    budget_expenditure_2024,
    budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    exact_number,
    identity,
    source_context,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

SCHEMA_VERSION = "archive-govt-nz.health-budget-biff8-extraction/v1"
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 16384
_DEFINITION_COLUMN = 2
PERIOD_TYPES = {
    2015: "Actuals",
    2016: "Actuals",
    2017: "Actuals",
    2018: "Actuals",
    2019: "Estimated Actual",
    2020: "Main Estimates",
}
BASIS = biff8_projection.VALUE_BASIS


@dataclass(frozen=True, slots=True)
class BiffBudgetProfile:
    """Closed source observation and independently reviewed physical columns."""

    kind: str
    source_sha256: str
    source_locator: str
    max_rows: int
    fields: tuple[tuple[str, str], ...]
    numeric_columns: tuple[tuple[str, int], ...]
    definitions: tuple[tuple[int, str], ...]
    definition_links: tuple[tuple[str, int], ...]

    @property
    def profile_id(self) -> str:
        """Identify the separately versioned stored-integer interpretation."""
        return f"budget-{self.kind}-2019-biff8/v1"

    @property
    def transformation(self) -> str:
        """Keep source-native output identity separate from literal XLSX facts."""
        return f"budget-2019-health-{self.kind}-biff8/v1"

    @property
    def fact_schema(self) -> pa.Schema:
        """Retain source dimensions while excluding the lexical-token class."""
        base = (
            budget_expenditure_2024.FACT_SCHEMA
            if self.kind == "expenditure"
            else budget_revenue.FACT_SCHEMA
        )
        return pa.schema(
            [
                f
                for f in base
                if f.name not in {"source_number_token", "raw_values_json"}
            ]
            + [
                pa.field("value_basis", pa.string()),
                pa.field("canonical_stored_integer", pa.string()),
                pa.field("numeric_evidence_id", pa.string()),
                pa.field("decoded_values_json", pa.string()),
            ]
        )


PROFILES = {
    "expenditure": BiffBudgetProfile(
        "expenditure",
        "30602fd66ec1f4fb7d0b47f2766f6560c4d22e90c11e994fba3e404e29ceab48",
        "https://www.treasury.govt.nz/sites/default/files/2019-05/b19-expenditure-data.xls",
        6288,
        tuple(budget_expenditure_2024.FIELDS.items()),
        (
            ("app_id", 3),
            ("parent_id", 4),
            ("amount", 11),
            ("year", 12),
            ("m_number", 16),
        ),
        tuple(
            (int(coordinate[1:]), text)
            for coordinate, text in {
                **budget_expenditure_2020.DEFINITIONS,
                "B3": (
                    "This Expense workbook contains details of actual government "
                    "expenditure for the years ended 30 June 2015, 2016, 2017 and "
                    "2018; estimated actual government expenditure for the year "
                    "ending 30\xa0June 2019 and budgeted government expenditure for "
                    "the year ending 30 June 2020 as published in Budget 2019."
                ),
            }.items()
        ),
        (
            *(
                (field, int(coordinate[1:]))
                for field, coordinate in budget_expenditure_2020.DEFINITION_COORDINATES
            ),
            ("source_vintage", 3),
            ("amount_type", 3),
        ),
    ),
    "revenue": BiffBudgetProfile(
        "revenue",
        "d927995dd91eda6fdfb4020eb2a3e91871a24d5144e837e7801b6725e5f33df8",
        "https://www.treasury.govt.nz/sites/default/files/2019-05/b19-revenue-data.xls",
        1020,
        tuple(budget_revenue.FIELDS.items()),
        (("app_id", 3), ("amount", 6), ("year", 7)),
        tuple(
            (int(coordinate[1:]), text)
            for coordinate, text in {
                **budget_revenue.DEFINITIONS_2020,
                "B4": (
                    "The Revenue workbook contains details of  actual government "
                    "Crown revenue and capital receipts for the years ended 30 June "
                    "2015, 2016, 2017 and 2018; estimated actual government Crown "
                    "revenue and capital receipts for the year ending 30 June 2019 "
                    "and budgeted government Crown revenue and capital receipts for "
                    "the year ending 30 June 2020 as published in Budget 2019."
                ),
            }.items()
        ),
        (
            ("unit", 36),
            ("valid_time_end", 37),
            ("amount_type", 38),
            ("app_id", 42),
            ("source_vintage", 4),
            ("amount_type", 4),
        ),
    ),
}
NUMERIC_SCHEMA = pa.schema(
    [pa.field("source_object_sha256", pa.string()), *biff8_projection.NUMERIC_SCHEMA]
)
LINEAGE_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("lineage_id", pa.string()),
        ("field", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_coordinate", pa.string()),
        ("source_row", pa.int64()),
        ("source_column", pa.int64()),
        ("raw_value", pa.string()),
        ("normalized_value", pa.string()),
        ("value_basis", pa.string()),
        ("numeric_evidence_id", pa.string()),
        ("rule", pa.string()),
    ]
)
DISPOSITION_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("sheet", pa.string()),
        ("source_row", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
        ("record_id", pa.string()),
        ("decoded_values_json", pa.string()),
    ]
)


@dataclass(frozen=True, slots=True)
class BiffBudgetSnapshot:
    """All companion tables and bounded source observations for one interpretation."""

    tables: Mapping[str, pa.Table]
    metadata: Mapping[str, Any]


def _require(condition: object) -> None:
    if not condition:
        message = "budget_biff8_contract"
        raise ValueError(message)


def _definitions(payload: bytes, profile: BiffBudgetProfile) -> biff8_records.BiffSheet:
    sheet = biff8_records.read_sheet(
        payload, profile.source_sha256, sheet="Explanation"
    )
    for row, expected in profile.definitions:
        _require(
            row not in sheet.formula_rows
            and row not in sheet.error_rows
            and 1 <= row <= len(sheet.values)
            and len(sheet.values[row - 1]) >= _DEFINITION_COLUMN
            and type(sheet.values[row - 1][1]) is str
            and sheet.values[row - 1][1] == expected
        )
    return sheet


def _selected_reason(values: dict[str, Any], profile: BiffBudgetProfile) -> str | None:
    required = (
        (
            "department",
            "appropriation_name",
            "category_name",
            "appropriation_or_category_type",
            "functional_classification",
            "portfolio_name",
        )
        if profile.kind == "expenditure"
        else ("department", "description", "revenue_type")
    )
    checks = [
        (
            any(
                type(values[field]) is not str or not values[field].strip()
                for field in required
            ),
            "missing_label",
        ),
        (
            any(
                values[field] <= 0
                for field, _ in profile.numeric_columns
                if field not in {"amount", "year"}
            ),
            "invalid_source_id",
        ),
        (
            values["year"] not in PERIOD_TYPES
            or values["amount_type"] != PERIOD_TYPES.get(values["year"]),
            "invalid_period_type",
        ),
        (exact_number(values["amount"]) is None, "invalid_amount_range"),
    ]
    if profile.kind == "revenue":
        checks.append(
            (
                values["revenue_type"] not in {"Non-Tax Revenue", "Capital Receipts"},
                "invalid_revenue_type",
            )
        )
    else:
        checks.extend(
            [
                (
                    any(
                        values[field] is not None and type(values[field]) is not str
                        for field in ("restriction_type", "current_scope")
                    ),
                    "invalid_optional_label",
                ),
                (values["group_type"] not in {"Single", "MCA"}, "invalid_group_type"),
                (values["periodicity"] not in {"A", "M"}, "invalid_periodicity"),
            ]
        )
    return next((reason for invalid, reason in checks if invalid), None)


def _scope(
    raw: biff8_records.BiffSheet, row: int, values: dict[str, Any]
) -> tuple[str, str] | None:
    if all(value is None for value in values.values()):
        return "blank", "empty_row"
    if type(values["vote"]) is not str or not values["vote"].strip():
        return "rejected", "invalid_vote"
    if values["vote"] != "Health":
        return "out_of_scope", "non_health_vote"
    if row in raw.formula_rows:
        return "rejected", "formula_not_evaluated"
    if row in raw.error_rows:
        return "rejected", "spreadsheet_error"
    return None


def _classify(
    raw: biff8_records.BiffSheet,
    row: int,
    profile: BiffBudgetProfile,
) -> tuple[str, str, dict[str, Any], list[biff8_records.NumericWitness]]:
    values = dict(
        zip((field for _, field in profile.fields), raw.values[row - 1], strict=True)
    )
    scope = _scope(raw, row, values)
    if scope is not None:
        return *scope, values, []
    witnesses = []
    try:
        for field, column in profile.numeric_columns:
            witness = raw.integer_cell(row, column)
            values[field] = raw.verify_integer(witness, row=row, column=column)
            witnesses.append(witness)
    except ValueError as error:
        return "rejected", str(error), values, []
    reason = _selected_reason(values, profile)
    if reason:
        return "rejected", reason, values, []
    return "normalized", "named_biff8_columns", values, witnesses


def _fact(
    context: dict[str, Any],
    profile: BiffBudgetProfile,
    row: int,
    values: dict[str, Any],
    witnesses: list[biff8_records.NumericWitness],
) -> dict[str, Any]:
    record_id = identity(profile.transformation, profile.source_sha256, "Raw Data", row)
    by_field = dict(
        zip((field for field, _ in profile.numeric_columns), witnesses, strict=True)
    )
    return {
        **context,
        **values,
        "record_id": record_id,
        "schema_version": f"archive-govt-nz.health-budget-biff8-{profile.kind}-fact/v1",
        "recordset": f"budget_{profile.kind}_fact",
        "source_row": row,
        "amount": exact_number(values["amount"]),
        "value_basis": BASIS,
        "canonical_stored_integer": by_field["amount"].canonical_stored_integer,
        "numeric_evidence_id": by_field["amount"].numeric_evidence_id,
        "unit": "$000",
        "currency": None,
        "valid_time_start": None,
        "valid_time_end": date(values["year"], 6, 30),
        "rights_state": "not_evaluated",
        "quality_flags": [
            "iso_currency_not_verified",
            "period_start_not_asserted",
            "no_parent_category_aggregation",
            "source_classification_unmapped",
        ],
        "transformation_id": profile.transformation,
        "lineage_id": identity(record_id, "lineage"),
    }


def _lineage(
    profile: BiffBudgetProfile,
    fact: dict[str, Any],
    values: dict[str, Any],
    witnesses: list[biff8_records.NumericWitness],
) -> list[dict[str, Any]]:
    by_field = dict(
        zip((field for field, _ in profile.numeric_columns), witnesses, strict=True)
    )
    result = []
    for column, (_, field) in enumerate(profile.fields, 1):
        witness = by_field.get(field)
        result.append(
            {
                "record_id": fact["record_id"],
                "lineage_id": fact["lineage_id"],
                "field": field,
                "source_object_sha256": profile.source_sha256,
                "source_locator": profile.source_locator,
                "source_coordinate": (
                    f"'Raw Data'!{get_column_letter(column)}{fact['source_row']}"
                ),
                "source_row": fact["source_row"],
                "source_column": column,
                "raw_value": None if witness else values[field],
                "normalized_value": None if fact[field] is None else str(fact[field]),
                "value_basis": BASIS if witness else "source_text/v1",
                "numeric_evidence_id": witness.numeric_evidence_id if witness else None,
                "rule": profile.transformation,
            }
        )
    definitions = dict(profile.definitions)
    for field, row in profile.definition_links:
        result.append(
            {
                "record_id": fact["record_id"],
                "lineage_id": fact["lineage_id"],
                "field": field,
                "source_object_sha256": profile.source_sha256,
                "source_locator": profile.source_locator,
                "source_coordinate": f"'Explanation'!B{row}",
                "source_row": row,
                "source_column": 2,
                "raw_value": definitions[row],
                "normalized_value": str(fact[field]),
                "value_basis": "source_text/v1",
                "numeric_evidence_id": None,
                "rule": profile.transformation,
            }
        )
    return result


def parse_snapshot(
    payload: bytes, *, profile: BiffBudgetProfile, observed_at: str
) -> BiffBudgetSnapshot:
    """Interpret one hash-pinned source without writing or granting source rights."""
    _require(profile.kind in {"expenditure", "revenue"})
    context = source_context(
        profile.source_sha256, profile.source_locator, "Budget-2019", observed_at
    )
    raw = biff8_records.read_sheet(payload, profile.source_sha256, sheet="Raw Data")
    _definitions(payload, profile)
    _require(
        1 < len(raw.values) <= profile.max_rows + 1
        and raw.values[0] == tuple(header for header, _ in profile.fields)
        and 1 not in raw.formula_rows
        and 1 not in raw.error_rows
    )
    facts, lineage, dispositions, numeric = [], [], [], []
    for row in range(2, len(raw.values) + 1):
        _require(len(raw.values[row - 1]) == len(profile.fields))
        _require(all(len(str(value)) <= MAX_TEXT for value in raw.values[row - 1]))
        decoded_json = encode_json(
            dict(
                zip(
                    (header for header, _ in profile.fields),
                    raw.values[row - 1],
                    strict=True,
                )
            )
        )
        state, reason, values, witnesses = _classify(raw, row, profile)
        fact = (
            _fact(context, profile, row, values, witnesses)
            if state == "normalized"
            else None
        )
        dispositions.append(
            {
                "source_object_sha256": profile.source_sha256,
                "source_locator": profile.source_locator,
                "sheet": "Raw Data",
                "source_row": row,
                "disposition": state,
                "reason": reason,
                "record_id": fact["record_id"] if fact else None,
                "decoded_values_json": decoded_json,
            }
        )
        if fact is None:
            continue
        fact["decoded_values_json"] = decoded_json
        _require(set(fact) == set(profile.fact_schema.names))
        links = _lineage(profile, fact, values, witnesses)
        biff8_projection.replay_projection(
            raw,
            fact,
            [w.to_record() for w in witnesses],
            [link for link in links if link["numeric_evidence_id"] is not None],
            columns=dict(profile.numeric_columns),
        )
        facts.append(fact)
        lineage.extend(links)
        numeric.extend(
            {"source_object_sha256": profile.source_sha256, **w.to_record()}
            for w in witnesses
        )
    tables = {
        "budget_facts.parquet": pa.Table.from_pylist(facts, schema=profile.fact_schema),
        "field_lineage.parquet": pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        "row_dispositions.parquet": pa.Table.from_pylist(
            dispositions, schema=DISPOSITION_SCHEMA
        ),
        "numeric_evidence.parquet": pa.Table.from_pylist(
            numeric, schema=NUMERIC_SCHEMA
        ),
    }
    counts = {
        state: sum(row["disposition"] == state for row in dispositions)
        for state in ("normalized", "out_of_scope", "blank", "rejected")
    }
    counts["input"] = len(dispositions)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile.profile_id,
        "transformation_id": profile.transformation,
        "source_object_sha256": profile.source_sha256,
        "source_locator": profile.source_locator,
        "source_vintage": "Budget-2019",
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "value_basis": BASIS,
        "status": "partial" if counts["rejected"] else "passed" if facts else "empty",
        "counts": counts,
        "workbook_inventory": raw.inventory,
        "decoded_values_semantics": "reader_values_only_not_source_decimal_tokens",
        "excluded_sheets": [
            {
                "sheet": b.name,
                "reason": "preserved_context_sheet_inventoried_only",
            }
            for b in raw.bindings
            if b.name != "Raw Data"
        ],
        "definitions": [
            {
                "source_coordinate": f"'Explanation'!B{row}",
                "text_sha256": identity(text),
            }
            for row, text in profile.definitions
        ],
    }
    return BiffBudgetSnapshot(tables, metadata)
