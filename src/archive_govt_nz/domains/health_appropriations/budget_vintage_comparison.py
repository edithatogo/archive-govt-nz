"""Source-qualified Budget estimate transitions, without restated comparability.

The reviewed original hashes bind Explanation!B3, B17, B21, B23, B40-B42:
June year ends, amount types and thousands are established; Supplementary
Estimates are excluded and earlier agency data are not restated. Literal
matches permit arithmetic diagnostics, not expenditure-performance claims.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import localcontext
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.budget_reader import (
    read_verified_budget,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.budget-estimate-transitions/v1"
SOURCE_PINS = {
    "Budget-2025": "d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338",
    "Budget-2026": "3fc6bba178c78c4a4b259c920a6f55307ec95a547353f340086c86fc2a26f5a0",
}
TRANSITIONS = {
    2025: ("Estimated Actual", "Actuals"),
    2026: ("Main Estimates", "Estimated Actual"),
}
SCHEMA = pa.schema(
    [
        ("year", pa.int64()),
        ("period_start", pa.date32()),
        ("period_end", pa.date32()),
        ("dimensions_json", pa.string()),
        ("earlier_amount_type", pa.string()),
        ("later_amount_type", pa.string()),
        ("state", pa.string()),
        ("semantic_comparability", pa.string()),
        ("earlier_record_ids", pa.list_(pa.string())),
        ("later_record_ids", pa.list_(pa.string())),
        ("earlier_source_rows", pa.list_(pa.int64())),
        ("later_source_rows", pa.list_(pa.int64())),
        ("earlier_amounts", pa.list_(pa.decimal128(20, 3))),
        ("later_amounts", pa.list_(pa.decimal128(20, 3))),
        ("difference_later_minus_earlier", pa.decimal128(21, 3)),
        ("unit", pa.string()),
    ]
)


@dataclass(frozen=True)
class BudgetComparisonInput:
    """An original and its separately pinned reviewed Budget package."""

    original: Path
    package: Path
    manifest_sha256: str


@dataclass(frozen=True)
class BudgetComparison:
    """Typed diagnostics plus input bindings and deliberately limited claims."""

    table: pa.Table
    receipt: dict[str, Any]


def _read(
    source: BudgetComparisonInput, vintage: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    facts, _, dispositions, manifest = read_verified_budget(
        source.package, source.manifest_sha256
    )
    if (
        manifest["source_vintage"] != vintage
        or manifest["source_object_sha256"] != SOURCE_PINS[vintage]
    ):
        message = "source_profile_mismatch"
        raise ValueError(message)
    verified_snapshot(source.original, SOURCE_PINS[vintage], max_bytes=64 * 1024 * 1024)
    edition = int(vintage[-4:])
    for fact in facts:
        year = fact["year"]
        expected = (
            "Main Estimates"
            if year == edition + 1
            else "Estimated Actual"
            if year == edition
            else "Actuals"
        )
        if (
            year not in range(edition - 4, edition + 2)
            or fact["amount_type"] != expected
        ):
            message = "amount_type_period_mismatch"
            raise ValueError(message)
    coordinates = {
        r["record_id"]: r["source_row"]
        for r in dispositions
        if r["record_id"] is not None
    }
    return [
        {**fact, "source_row": coordinates[fact["record_id"]]} for fact in facts
    ], manifest


def _compare_budget_vintages(
    earlier: BudgetComparisonInput, later: BudgetComparisonInput
) -> BudgetComparison:
    """Read pinned sources; retain all transition inputs, never aggregate them.

    Matching compares every raw dimension except Year, Amount $000 and Amount
    Type. Duplicate coordinates stay ambiguous, even if values agree. Missing
    matches retain one side; no zero substitution or fuzzy mapping occurs.
    This library operation writes nothing and rechecks all input pins at exit.
    """
    grouped: list[dict[tuple[int, str], list[dict[str, Any]]]] = []
    bindings, accounting = {}, {}
    for side, source, vintage in [
        ("earlier", earlier, "Budget-2025"),
        ("later", later, "Budget-2026"),
    ]:
        facts, manifest = _read(source, vintage)
        groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
        for fact in facts:
            if fact["year"] in TRANSITIONS:
                raw = json.loads(fact["raw_values_json"])
                dimensions = {
                    name: value
                    for name, value in raw.items()
                    if name not in ("Year", "Amount $000", "Amount Type")
                }
                key = (
                    fact["year"],
                    json.dumps(
                        dimensions,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
                )
                groups[key].append(fact)
        selected = sum(map(len, groups.values()))
        accounting[side] = {
            "selected": selected,
            "outside_transitions": len(facts) - selected,
        }
        bindings[side] = {
            "source_vintage": vintage,
            "source_object_sha256": manifest["source_object_sha256"],
            "manifest_sha256": source.manifest_sha256,
            "observed_at": manifest["observed_at"],
            "source_locator": manifest["source_locator"],
            "definition_coordinates": [
                "Explanation!" + c
                for c in ("B3", "B17", "B21", "B23", "B40", "B41", "B42")
            ],
        }
        grouped.append(groups)
    rows = []
    for year, dimensions in sorted(set(grouped[0]) | set(grouped[1])):
        a = sorted(
            grouped[0].get((year, dimensions), []), key=lambda r: r["source_row"]
        )
        b = sorted(
            grouped[1].get((year, dimensions), []), key=lambda r: r["source_row"]
        )
        state = (
            "ambiguous_literal_group"
            if len(a) > 1 or len(b) > 1
            else "earlier_only"
            if not b
            else "later_only"
            if not a
            else "unique_literal_pair"
        )
        difference = None
        if state == "unique_literal_pair":
            with localcontext() as context:
                context.prec = 80
                difference = b[0]["amount"] - a[0]["amount"]
        record = {
            "year": year,
            "period_start": date(year - 1, 7, 1),
            "period_end": date(year, 6, 30),
            "dimensions_json": dimensions,
            "earlier_amount_type": TRANSITIONS[year][0],
            "later_amount_type": TRANSITIONS[year][1],
            "state": state,
            "semantic_comparability": "not_established",
            "difference_later_minus_earlier": difference,
            "unit": "NZD_thousands",
        }
        for side, facts in [("earlier", a), ("later", b)]:
            record[side + "_record_ids"] = [r["record_id"] for r in facts]
            record[side + "_source_rows"] = [r["source_row"] for r in facts]
            record[side + "_amounts"] = [r["amount"] for r in facts]
        rows.append(record)
    for source, vintage in [(earlier, "Budget-2025"), (later, "Budget-2026")]:
        verified_snapshot(
            source.original, SOURCE_PINS[vintage], max_bytes=64 * 1024 * 1024
        )
        verified_snapshot(
            source.package / "MANIFEST.json",
            source.manifest_sha256,
            max_bytes=64 * 1024 * 1024,
        )
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    return BudgetComparison(
        table,
        {
            "schema_version": VERSION,
            "status": "verified_literal_diagnostic",
            "source_bindings": bindings,
            "input_accounting": accounting,
            "group_count": len(rows),
            "state_counts": {
                state: sum(r["state"] == state for r in rows)
                for state in (
                    "unique_literal_pair",
                    "ambiguous_literal_group",
                    "earlier_only",
                    "later_only",
                )
            },
            "caveats": [
                "supplementary_estimates_excluded",
                "earlier_data_not_restated_for_restructuring",
                "names_and_scope_are_edition_specific",
                "gst_basis_not_established",
                "not_official_estimates_reconciliation",
                "arithmetic_difference_not_performance_variance",
            ],
            "rights_state": "not_evaluated",
            "publication_approval": "not_granted",
            "full_track_completion": "not_asserted",
        },
    )


def compare_budget_vintages(
    earlier: BudgetComparisonInput, later: BudgetComparisonInput
) -> BudgetComparison:
    """Isolate the reader and arithmetic from caller Decimal precision."""
    with localcontext() as context:
        context.prec = 80
        return _compare_budget_vintages(earlier, later)
